"""Compare vocal separation models on one local song without network access."""
import argparse
import socket
import sys
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / 'analysis'))

import inputs
import installation
import measures
import report
import separators
from candidates import BASELINE, CANDIDATES, MSST_COMMIT, by_id


def deny_network():
    def refuse(*_args, **_kwargs):
        raise RuntimeError('分離の比較はオフラインで実行します。ネット接続は禁止です。')
    socket.create_connection = refuse
    socket.socket.connect = refuse
    socket.socket.connect_ex = refuse


@dataclass(frozen=True)
class Session:
    folder: Path
    home: Path
    models: Path
    device: str
    mix_path: Path
    mix: object
    reference: object
    batch_size: int | None


def separation(candidate, session, target):
    if candidate is BASELINE:
        return lambda: separators.demucs_vocals(session.mix_path, target / 'stems', session.models, session.device)
    installation.verify_weights(session.home, candidate)
    weights = installation.weights_path(session.home, candidate)
    return lambda: separators.roformer_vocals(candidate, session.home / 'msst', weights, session.mix,
                                              session.device, session.batch_size)


def evaluate(candidate, session):
    import soundfile as sf
    target = session.folder / candidate.id
    target.mkdir(exist_ok=True)
    print(f'分離: {candidate.label}', flush=True)
    vocals, elapsed, peak = separators.measure(session.device, separation(candidate, session, target))
    instrumental = session.mix - vocals
    for name, samples in (('vocals', vocals), ('instrumental', instrumental)):
        sf.write(str(target / f'{name}.wav'), samples, inputs.RATE, subtype='FLOAT')
    row = dict(id=candidate.id, label=candidate.label, license=candidate.license or '記載なし',
               licenseSource=candidate.license_source, elapsedSeconds=elapsed,
               realtimeFactor=elapsed / (len(session.mix) / inputs.RATE), peakGpuMemoryMiB=peak,
               vocalsLevelDb=measures.level_db(vocals), instrumentalLevelDb=measures.level_db(instrumental))
    if candidate.weights:
        row['weightsSha256'] = candidate.weights.sha256
    if session.reference is not None:
        row.update(sdrVocals=measures.sdr(session.reference, vocals),
                   sdrInstrumental=measures.sdr(session.mix - session.reference, instrumental))
    return row


def selected(identifiers, home):
    if identifiers:
        return [by_id(identifier) for identifier in identifiers]
    return [candidate for candidate in CANDIDATES if installation.has_weights(home, candidate)]


def output_folder(args):
    if args.out:
        return args.out
    stamp = datetime.now().strftime('%Y%m%dT%H%M%S')
    return installation.REPOSITORY / 'test-results' / 'separation' / f'{args.song.stem}-{stamp}'


def parse(argv):
    parser = argparse.ArgumentParser(description='手元の曲でボーカル分離モデルを比べます（オフライン）。')
    parser.add_argument('song', type=Path, help='音源ファイル、またはhodomiaのプロジェクトフォルダー')
    parser.add_argument('--models', nargs='+', choices=[candidate.id for candidate in CANDIDATES],
                        help='既定は重みを準備済みの全モデル')
    parser.add_argument('--start', type=float, default=0, help='比べる区間の開始秒')
    parser.add_argument('--duration', type=float, help='比べる区間の秒数。既定は曲の最後まで')
    parser.add_argument('--reference-vocals', type=Path, help='SDRを計算する正解ボーカルのWAV（44.1 kHzステレオ）')
    parser.add_argument('--batch-size', type=int, help='RoFormerの推論バッチ数。GPUメモリが足りないときに下げる')
    parser.add_argument('--runtime', type=Path, default=installation.default_runtime())
    parser.add_argument('--out', type=Path, help='既定は test-results/separation/<曲名>-<日時>')
    return parser.parse_args(argv)


def main(argv=None):
    args = parse(argv)
    deny_network()
    import torch
    from engines import configure
    home = installation.home(args.runtime)
    installation.verify_checkout(home / 'msst')
    sys.path.insert(0, str(home / 'msst'))
    models, device = configure(args.runtime)
    if device == 'cuda':
        # Initialize the CUDA context here so the first model's time does not include it.
        torch.zeros(1, device=device)
    folder = output_folder(args)
    folder.mkdir(parents=True, exist_ok=True)
    mix_path, mix, reference = inputs.prepare(args.song, folder, args.start, args.duration, args.reference_vocals)
    session = Session(folder, home, models, device, mix_path, mix, reference, args.batch_size)
    rows = [evaluate(candidate, session) for candidate in selected(args.models, home)]
    report.write(folder, dict(input=str(args.song), excerpt=dict(start=args.start, seconds=len(mix) / inputs.RATE),
                              device=device, torch=torch.__version__, msstCommit=MSST_COMMIT, models=rows))
    print(f'結果: {folder / "report.md"}', flush=True)


if __name__ == '__main__':
    main()
