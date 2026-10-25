"""Online setup for the vocal separation comparison. Accepts no audio; run before compare.py."""
import argparse
import os
import shutil
import subprocess
import sys
import urllib.request
from pathlib import Path

import installation
from candidates import CANDIDATES, MSST_COMMIT, MSST_REPOSITORY

TOOL = Path(__file__).resolve().parent
CUDA_INDEX = 'https://download.pytorch.org/whl/cu128'


def run(command):
    subprocess.run(command, check=True)


def fetch(url, target, expected):
    """Download to a temporary name and keep the file only when its SHA-256 matches."""
    if target.is_file() and installation.sha256(target) == expected:
        return False
    partial = target.with_name(target.name + '.partial')
    try:
        with urllib.request.urlopen(url) as response, open(partial, 'wb') as output:
            shutil.copyfileobj(response, output, 1 << 20)
        actual = installation.sha256(partial)
        if actual != expected:
            raise ValueError(f'{target.name}: SHA-256が一致しません（{actual}）。')
        os.replace(partial, target)
    finally:
        partial.unlink(missing_ok=True)
    return True


def install_packages(home):
    python = installation.python_path(home)
    if not python.exists():
        run(['uv', 'venv', str(home / 'venv'), '--python', '3.11'])
    command = ['uv', 'pip', 'install', '--python', str(python), '-r', str(TOOL / 'requirements.txt')]
    if sys.platform != 'darwin':
        command += ['--extra-index-url', CUDA_INDEX, '--index-strategy', 'unsafe-best-match']
    run(command)
    frozen = subprocess.run(['uv', 'pip', 'freeze', '--python', str(python)],
                            check=True, capture_output=True, text=True).stdout
    (home / 'requirements.lock.txt').write_text(frozen, encoding='utf-8')


def checkout_msst(home):
    repo = home / 'msst'
    if not repo.exists():
        run(['git', 'clone', MSST_REPOSITORY, str(repo)])
        run(['git', '-C', str(repo), 'checkout', '--detach', MSST_COMMIT])
    installation.verify_checkout(repo)


def download_weights(home, include_unlicensed):
    (home / 'weights').mkdir(parents=True, exist_ok=True)
    for candidate in CANDIDATES:
        if candidate.weights is None:
            continue
        if candidate.license is None and not include_unlicensed:
            print(f'取得しない: {candidate.id}（ライセンスの記載なし。--include-unlicensed で取得）', flush=True)
            continue
        print(f'取得: {candidate.id}（ライセンス: {candidate.license or "記載なし"}）', flush=True)
        fetch(candidate.weights.url, installation.weights_path(home, candidate), candidate.weights.sha256)


def warn_without_baseline(runtime):
    torch_models = Path(runtime) / 'models' / 'torch'
    if not any(torch_models.glob('**/checkpoints/*.th')):
        print('注意: htdemucs_ftがありません。先に npm run setup:analysis を実行してください。', flush=True)


def main():
    parser = argparse.ArgumentParser(description='分離比較用の環境と重みを準備します（ネット接続あり）。')
    parser.add_argument('--runtime', type=Path, default=installation.default_runtime())
    parser.add_argument('--include-unlicensed', action='store_true',
                        help='ライセンスの記載がない重みも、手元の評価用に取得する')
    args = parser.parse_args()
    home = installation.home(args.runtime)
    home.mkdir(parents=True, exist_ok=True)
    install_packages(home)
    checkout_msst(home)
    download_weights(home, args.include_unlicensed)
    warn_without_baseline(args.runtime)
    print(f'準備完了: {home}', flush=True)


if __name__ == '__main__':
    main()
