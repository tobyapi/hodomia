"""Locations and integrity checks of the comparison environment inside the runtime folder."""
import hashlib
import os
import subprocess
from pathlib import Path

from candidates import MSST_COMMIT

REPOSITORY = Path(__file__).resolve().parents[2]


def default_runtime():
    return Path(os.environ.get('HODOMIA_RUNTIME') or REPOSITORY / '.runtime')


def home(runtime):
    return Path(runtime) / 'separation-compare'


def python_path(folder):
    return folder / 'venv' / ('Scripts/python.exe' if os.name == 'nt' else 'bin/python')


def weights_path(folder, candidate):
    return folder / 'weights' / candidate.weights.filename


def sha256(path):
    digest = hashlib.sha256()
    with open(path, 'rb') as stream:
        for block in iter(lambda: stream.read(1 << 20), b''):
            digest.update(block)
    return digest.hexdigest()


def has_weights(folder, candidate):
    return candidate.weights is None or weights_path(folder, candidate).is_file()


def verify_weights(folder, candidate):
    path = weights_path(folder, candidate)
    if not path.is_file():
        raise FileNotFoundError(f'{candidate.id}: 重みがありません。scripts/separation/prepare.py を実行してください。')
    if sha256(path) != candidate.weights.sha256:
        raise ValueError(f'{candidate.id}: 重みのSHA-256が一致しません。prepare.py で取得し直してください。')


def verify_checkout(repo):
    """Refuse to run model code other than the pinned, unmodified MSST commit."""
    def git(*args):
        return subprocess.run(['git', '-C', str(repo), *args], check=True, capture_output=True, text=True).stdout.strip()
    if not (repo / '.git').exists():
        raise FileNotFoundError('MSSTのチェックアウトがありません。scripts/separation/prepare.py を実行してください。')
    if git('rev-parse', 'HEAD') != MSST_COMMIT or git('status', '--porcelain', '--untracked-files=no'):
        raise ValueError(f'MSSTは変更のない {MSST_COMMIT} である必要があります。既存のファイルは上書きしません。')
