"""Compare separation models on one local song without network access."""
import argparse
import sys
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / 'analysis'))

import inputs
import installation
import report
from offline import deny_network
from candidates import CANDIDATES, COMBINATIONS, MSST_COMMIT, by_id
from evaluation import Session, combined, evaluate


def selected(identifiers, home):
    if identifiers:
        return [by_id(identifier) for identifier in identifiers]
    return [candidate for candidate in CANDIDATES if installation.has_downloads(home, candidate)]


def output_folder(args):
    if args.out:
        return args.out
    stamp = datetime.now().strftime('%Y%m%dT%H%M%S')
    return installation.REPOSITORY / 'test-results' / 'separation' / f'{args.song.stem}-{stamp}'


def parse(argv):
    parser = argparse.ArgumentParser(description='手元の曲で分離モデルを比べます（オフライン）。')
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
    rows += [row for row in (combined(combination, rows, session) for combination in COMBINATIONS) if row]
    report.write(folder, dict(input=str(args.song), excerpt=dict(start=args.start, seconds=len(mix) / inputs.RATE),
                              device=device, torch=torch.__version__, msstCommit=MSST_COMMIT, models=rows))
    print(f'結果: {folder / "report.md"}', flush=True)


if __name__ == '__main__':
    main()
