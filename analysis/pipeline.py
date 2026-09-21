"""Checkpointed single-song analysis; errors remain explicit and retryable."""
import hashlib
import copy
import os
import socket
import time
import traceback
import uuid
import sys
from locking import analysis_operation, file_lock
from analysis_options import validate_options
from datetime import datetime, timezone
from pathlib import Path
from storage import manifest, within, write_json, read_json, row


class Cancelled(Exception):
    pass


@analysis_operation
def run(root, runtime, options, cancel_path=None, on_run=None):
    root, runtime = Path(root), Path(runtime)
    project = manifest(root)
    validate_options(options, project['duration'])
    region = options.get('region')
    events_only = options.get('scope') == 'vocal-events'
    compare_events = options.get('scope') == 'vocal-comparison'
    harmony_only = options.get('scope') == 'harmony'
    sensitivity = options.get('eventSensitivity', 'standard')
    (root / 'cancel.flag').unlink(missing_ok=True)
    def cancelled():
        return (root / 'cancel.flag').exists() or (cancel_path is not None and Path(cancel_path).exists())
    with file_lock(root / '.write.lock'):
        run_id = datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S') + '-' + uuid.uuid4().hex[:8]
        folder = root / 'runs' / run_id
        folder.mkdir(parents=True)
        write_json(folder / 'request.json', options)
        previous = None
        if project.get('currentRun'):
            previous_file = within(root, 'runs/' + project['currentRun'] + '/result.json')
            if previous_file.exists():
                previous = read_json(previous_file)
        project['currentRun'] = run_id
        write_json(root / 'project.json', project)
        result = copy.deepcopy(previous) if (region or events_only or compare_events or harmony_only) and previous else {'tracks': {}, 'series': {}, 'stems': {}, 'engines': {}}
        result['runId'] = run_id
        if not (events_only or compare_events or harmony_only) or 'mode' not in result:
            result['mode'] = options['mode']
        result['sourceHash'] = project['source']['sha256']
        if on_run is not None:
            on_run(run_id)
    started, errors = time.monotonic(), []
    status = {'state': 'running', 'stage': '準備', 'progress': 0, 'errors': errors}

    def publish(stage, progress, state='running'):
        if cancelled():
            raise Cancelled()
        status.update(state=state, stage=stage, progress=progress, elapsed=time.monotonic() - started)
        write_json(folder / 'result.json', result)
        write_json(folder / 'status.json', status)
        print(stage, flush=True, file=sys.stderr)

    def attempt(stage, progress, action):
        publish(stage, progress)
        try:
            action()
        except Cancelled:
            raise
        except Exception as error:
            errors.append({'stage': stage, 'message': str(error)})
            traceback.print_exc()
        finally:
            from engines import release
            release()
        publish(stage, progress)

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
        if compare_events:
            result.pop('vocalComparisons', None)
            from vocal_comparison import compare
            paths = {name: within(root, path) for name, path in result.get('stems', {}).items()}
            def compare_voices():
                last_update = 0.
                def progress(fraction):
                    nonlocal last_update
                    if cancelled():
                        raise Cancelled()
                    now = time.monotonic()
                    if now - last_update >= 1 or fraction >= 1:
                        publish(f'AST / YAMNet を比較 {round(fraction * 100)}%', .05 + .9 * fraction)
                        last_update = now
                result['vocalComparisons'] = compare(audio, paths.get('vocals'), models, device, runtime,
                                                    duration, folder, sensitivity, progress)
            attempt('AST / YAMNet の比較', .05, compare_voices)
            publish('声の比較に失敗しました' if errors else '声の比較完了', 1, 'partial' if errors else 'complete')
            return
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
            from vocal_events import detect
            last_update = 0.
            def update_progress(fraction):
                nonlocal last_update
                if cancelled():
                    raise Cancelled()
                now = time.monotonic()
                if now - last_update >= 1 or fraction >= 1:
                    publish(f'声の表現を検出 {round(fraction * 100)}%',
                            start_progress + fraction * (end_progress - start_progress))
                    last_update = now
            rows, engine = detect(audio, paths.get('vocals'), models, device, duration, folder, sensitivity,
                                  progress=update_progress, beatbox_recall=options.get('beatboxRecall', True))
            result['tracks']['vocalEvents'] = rows
            result['engines']['vocalEvents'] = engine
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
                from lyrics import transcribe
                vocal = paths.get('vocals')
                if vocal is None:
                    raise ValueError('歌詞解析の前にボーカル分離を完了してください。')
                tracks, engine = transcribe(vocal, models, device, options['mode'], options.get('lyrics', ''),
                                            duration, folder, region)
                if region:
                    for track, rows in tracks.items():
                        kept = [r for r in result['tracks'].get(track, []) if r.get('start') is None or r['end'] <= region['start'] or r['start'] >= region['end']]
                        # IDs include run so old and new rows cannot collide.
                        for r in rows:
                            r['id'] = run_id + '-' + r['id']
                            if r.get('parentId'):
                                r['parentId'] = run_id + '-' + r['parentId']
                        result['tracks'][track] = kept + rows
                else:
                    result['tracks'].update(tracks)
                result['engines']['lyrics'] = engine
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
        status.update(state='cancelled', stage='中止しました', elapsed=time.monotonic() - started)
        write_json(folder / 'result.json', result)
        write_json(folder / 'status.json', status)
    except Exception as error:
        errors.append({'stage': status['stage'], 'message': str(error)})
        status.update(state='failed', stage='解析に失敗しました', elapsed=time.monotonic() - started)
        write_json(folder / 'result.json', result)
        write_json(folder / 'status.json', status)
        traceback.print_exc()
        raise
