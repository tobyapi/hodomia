"""Locations and integrity checks of the comparison environment inside the runtime folder."""
import hashlib
import os
import subprocess
from pathlib import Path

from candidates import MSST_COMMIT, Download

REPOSITORY = Path(__file__).resolve().parents[2]


def default_runtime():
    return Path(os.environ.get('HODOMIA_RUNTIME') or REPOSITORY / '.runtime')


def home(runtime):
    return Path(runtime) / 'separation-compare'


def python_path(folder):
    return folder / 'venv' / ('Scripts/python.exe' if os.name == 'nt' else 'bin/python')


def downloads(candidate):
    files = [candidate.config, candidate.weights]
    return [file for file in files if isinstance(file, Download)]


def download_path(folder, download):
    return folder / 'weights' / download.filename


def config_path(folder, candidate):
    if isinstance(candidate.config, Download):
        return download_path(folder, candidate.config)
    return folder / 'msst' / candidate.config


def sha256(path):
    digest = hashlib.sha256()
    with open(path, 'rb') as stream:
        for block in iter(lambda: stream.read(1 << 20), b''):
            digest.update(block)
    return digest.hexdigest()


def has_downloads(folder, candidate):
    return all(download_path(folder, download).is_file() for download in downloads(candidate))


def verify_downloads(folder, candidate):
    for download in downloads(candidate):
        path = download_path(folder, download)
        if not path.is_file():
            raise FileNotFoundError(f'{candidate.id}: {download.filename} がありません。scripts/separation/prepare.py を実行してください。')
        if sha256(path) != download.sha256:
            raise ValueError(f'{candidate.id}: {download.filename} のSHA-256が一致しません。prepare.py で取得し直してください。')


def verify_checkout(repo):
    """Refuse to run model code other than the pinned, unmodified MSST commit."""
    def git(*args):
        return subprocess.run(['git', '-C', str(repo), *args], check=True, capture_output=True, text=True).stdout.strip()
    if not (repo / '.git').exists():
        raise FileNotFoundError('MSSTのチェックアウトがありません。scripts/separation/prepare.py を実行してください。')
    if git('rev-parse', 'HEAD') != MSST_COMMIT or git('status', '--porcelain', '--untracked-files=no'):
        raise ValueError(f'MSSTは変更のない {MSST_COMMIT} である必要があります。既存のファイルは上書きしません。')
