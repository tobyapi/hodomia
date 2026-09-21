"""Checkpointed single-song analysis; errors remain explicit and retryable."""
import hashlib
import socket
import traceback
from locking import analysis_operation
from analysis_options import validate_options
from pathlib import Path
from storage import manifest, within, row
from checkpoints import Cancelled, Checkpoint, create_run
from lyrics_stage import analyze_lyrics
from vocal_stage import vocal_events as detect_vocals


@analysis_operation
def run(root, runtime, options, cancel_path=None, on_run=None):
    root, runtime = Path(root), Path(runtime)
    project = manifest(root)
    validate_options(options, project['duration'])
    region = options.get('region')
    events_only = options.get('scope') == 'vocal-events'
    harmony_only = options.get('scope') == 'harmony'
    (root / 'cancel.flag').unlink(missing_ok=True)
    run_id, folder, previous, result = create_run(root, project, options, on_run)
    checkpoint = Checkpoint(root, folder, result, cancel_path)
    publish, attempt, cancelled = checkpoint.publish, checkpoint.attempt, checkpoint.cancelled
    errors = checkpoint.errors

    try:
        publish('音源の同一性を確認', 0)
        with within(root, project['source']['path']).open('rb') as stream:
            if hashlib.file_digest(stream, 'sha256').hexdigest() != project['source']['sha256']:
                raise ValueError('保存済みの元音源が変更されています。新しいプロジェクトとして読み込んでください。')
        from engines import configure, separate, beats, sections
        from dsp import basics, estimate_key, pitch, stem_activity
        import numpy as np
        models, device = configure(runtime)
        # After setup every network attempt is a bug, including model-cache fallback.
        def deny_network(*args, **kwargs):
            raise RuntimeError('解析中はネット接続を禁止しています。モデルをセットアップしてください。')
        socket.create_connection = deny_network
        socket.socket.connect = deny_network
        audio = within(root, project['audio'])
        duration = project['duration']
        paths = {}
        def analyze_harmony_signal(signal, sr, source):
            from chordmini import infer
            def check_cancel():
                if cancelled():
                    raise Cancelled()
            chords, engine = infer(audio, runtime, folder, duration, check_cancel)
            key = estimate_key(signal, sr, duration)
            result['tracks'].update(chords=chords, key=key)
            result.pop('chordComparisons', None)
            result['engines']['chords'] = engine
            result['engines']['harmonySource'] = engine['source']
            result['engines']['keySource'] = source
        if harmony_only:
            def refresh_harmony():
                from dsp import accompaniment
                paths = {name: within(root, path) for name, path in result.get('stems', {}).items()}
                y, sr, _, _ = basics(audio)
                signal, source = accompaniment(paths, y, sr)
                analyze_harmony_signal(signal, sr, source)
            attempt('コード・キーを再推定', .1, refresh_harmony)
            publish('コード・キーの再推定に失敗しました' if errors else 'コード・キーの再推定完了', 1, 'partial' if errors else 'complete')
            return
        def vocal_events(start_progress, end_progress):
            detect_vocals(start_progress, end_progress, audio, paths, models, device,
                          duration, folder, options, checkpoint, result)
        if events_only:
            paths = {name: within(root, path) for name, path in result.get('stems', {}).items()}
            attempt('声の表現を検出', .05, lambda: vocal_events(.05, .95))
            publish('声の表現の検出に失敗しました' if errors else '声の表現のみ解析完了', 1, 'partial' if errors else 'complete')
            return
        if not region:
            publish('波形・音量', .05)
            y, sr, basic, onset = basics(audio)
            result['series'].update(basic)
            result['engines']['signal'] = 'librosa 0.11 / chroma key / pYIN'
            if basic['silence']:
                result['tracks'] = {name: [] for name in ('beats', 'sections', 'lyrics', 'words', 'vocalEvents', 'chords', 'key')}
                publish('無音のため音楽情報を推定できませんでした', 1, 'complete')
                return
            def separation():
                nonlocal paths
                cached = previous or {}
                candidates = {name: within(root, path) for name, path in cached.get('stems', {}).items()}
                if (cached.get('sourceHash') == project['source']['sha256'] and
                    cached.get('engines', {}).get('separation') == 'htdemucs_ft / shifts=2 / overlap=.5' and
                    set(candidates) == {'vocals', 'drums', 'bass', 'other'} and all(p.is_file() for p in candidates.values())):
                    paths = candidates
                    result['engines']['separationCache'] = cached.get('runId')
                else:
                    paths = separate(audio, folder / 'stems', models, device)
                result['stems'] = {name: str(path.relative_to(root)).replace('\\', '/') for name, path in paths.items()}
                result['engines']['separation'] = 'htdemucs_ft / shifts=2 / overlap=.5'
                for name, path in paths.items():
                    result['series'][name] = stem_activity(path, name, duration)
            attempt('ボーカル・楽器の分離', .12, separation)
            times = []
            def rhythm():
                nonlocal times
                times, downs = beats(audio, models, device)
                times = [t for t in times if 0 <= t < duration]
                result['tracks']['beats'] = [row('beat', i, t, t, '1' if any(abs(t - d) < .08 for d in downs) else '拍')
                                             for i, t in enumerate(times)]
                intervals = np.diff(times)
                result['bpm'] = float(60 / np.median(intervals)) if len(intervals) else None
                result['series']['tempo'] = [{'time': t, 'value': float(60 / dt)} for t, dt in zip(times, intervals) if dt > 0]
                result['engines']['beats'] = 'Beat This final0'
            attempt('拍・BPM', .42, rhythm)
            def analyze_harmony():
                from dsp import accompaniment
                signal, source = accompaniment(paths, y, sr)
                analyze_harmony_signal(signal, sr, source)
            attempt('コード・キー', .5, analyze_harmony)
            def analyze_structure():
                if not paths:
                    raise ValueError('構造解析の前に分離を完了してください。')
                result['tracks']['sections'] = sections(paths, folder, models, device, duration)
                result['engines']['structure'] = 'All-In-One harmonix-all / all-in-one-infer 3.1.0'
            attempt('曲構成・サビの推定', .6, analyze_structure)
        else:
            paths = {name: within(root, path) for name, path in result.get('stems', {}).items()}
        if options['mode'] != 'instrumental':
            def lyrics():
                analyze_lyrics(paths, models, device, options, duration, folder, region, run_id, result)
            attempt('日本語歌唱の精密解析' if options['mode'] == 'japanese' else '歌詞・単語の時刻', .72, lyrics)
        elif not region:
            result['tracks'].update(lyrics=[], words=[])
        if not region:
            attempt('声の表現を検出', .82, lambda: vocal_events(.82, .89))
            target = paths.get('vocals') if options['mode'] != 'instrumental' else paths.get('other', audio)
            if target:
                attempt('主旋律の音高', .9, lambda: result['series'].update(pitch=pitch(target, options['mode'] == 'instrumental')))
        state = 'partial' if errors else 'complete'
        publish('一部の解析に失敗しました' if errors else '解析完了', 1, state)
    except Cancelled:
        checkpoint.finish_error()
    except Exception as error:
        checkpoint.finish_error(error)
        traceback.print_exc()
        raise
