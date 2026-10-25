"""Run the analysis stages that read stems on each model's output from compare.py, without network access.

Run with the analysis Python, not the comparison venv: All-In-One and Whisper live there."""
import argparse
import hashlib
import json
import sys
import time
from dataclasses import dataclass
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / 'analysis'))

import downstream_report
import installation
from candidates import STEMS
from offline import deny_network


@dataclass(frozen=True)
class Session:
    models: Path
    device: str
    mode: str
    duration: float


def timed(action):
    started = time.perf_counter()
    result = action()
    return result, time.perf_counter() - started


def samples_digest(path):
    """Digest of the audio only: libsndfile stamps the write time into float WAV headers."""
    import soundfile as sf
    samples, _ = sf.read(str(path), dtype='float32')
    return hashlib.sha256(samples.tobytes()).hexdigest()


def transcript(vocals, folder, session, cache):
    """Whisper text and line statistics; models that give the same vocal samples share the transcript."""
    from lyrics import NO_SPEECH_WARNING, comparable, transcribe
    digest = samples_digest(vocals)
    if digest not in cache:
        (tracks, _), seconds = timed(lambda: transcribe(vocals, session.models, session.device, session.mode,
                                                        '', session.duration, folder))
        segments = json.loads((folder / 'transcript.json').read_text(encoding='utf-8'))['segments']
        cache[digest] = dict(
            text=comparable(''.join(s['text'] for s in segments)), lines=len(tracks['lyrics']),
            untimedLines=sum(line['start'] is None for line in tracks['lyrics']),
            noSpeechLines=sum(s['noSpeechProb'] > NO_SPEECH_WARNING for s in segments),
            meanAvgLogprob=sum(s['avgLogprob'] for s in segments) / len(segments) if segments else None,
            seconds=seconds)
    return cache[digest]


def structure(folder, session):
    from dsp import stem_activity
    from engines import sections
    paths = {name: folder / 'stems' / f'{name}.wav' for name in STEMS}
    # All-In-One reuses a cached spectrogram by folder name, which would hide stems written again by compare.py.
    (folder / 'spectrograms' / 'stems.npy').unlink(missing_ok=True)
    rows, seconds = timed(lambda: sections(paths, folder, session.models, session.device, session.duration))
    activity = {name: stem_activity(path, name, session.duration)['regions'] for name, path in paths.items()}
    return dict(sections=[dict(start=r['start'], end=r['end'], label=r['label']) for r in rows],
                activity=activity, structureSeconds=seconds)


def analyze(folder, session, cache):
    print(f'解析: {folder.name}', flush=True)
    result = dict(id=folder.name, lyrics=transcript(folder / 'vocals.wav', folder, session, cache))
    if all((folder / 'stems' / f'{name}.wav').is_file() for name in STEMS):
        result.update(structure(folder, session))
    (folder / 'downstream.json').write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding='utf-8')
    return result


def parse(argv):
    parser = argparse.ArgumentParser(description='compare.pyの出力で曲構成と歌詞の推定を比べます（オフライン）。')
    parser.add_argument('folder', type=Path, help='compare.py の出力フォルダー')
    parser.add_argument('--mode', choices=('japanese', 'multilingual'), default='japanese', help='歌詞解析のモード')
    parser.add_argument('--runtime', type=Path, default=installation.default_runtime())
    return parser.parse_args(argv)


def main(argv=None):
    args = parse(argv)
    deny_network()
    import soundfile as sf
    from engines import configure
    report = json.loads((args.folder / 'report.json').read_text(encoding='utf-8'))
    models, device = configure(args.runtime)
    session = Session(models, device, args.mode, sf.info(str(args.folder / 'mix.wav')).duration)
    cache = {}
    results = [analyze(args.folder / row['id'], session, cache) for row in report['models']]
    downstream_report.write(args.folder, report, results, session.duration)
    print(f'結果: {args.folder / "downstream.md"}', flush=True)


if __name__ == '__main__':
    main()
