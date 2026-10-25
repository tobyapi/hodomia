"""Online setup of the pinned separation code and weights. Analysis only reads what this records."""
import os
import shutil
import subprocess
import urllib.request
from pathlib import Path
from separation import COMMIT, DOWNLOADS, REPOSITORY, SETUP_ID, code_files, digest, home
from storage import write_json


def git(*args):
    return subprocess.run(['git', *args], check=True, capture_output=True, text=True).stdout.strip()


def checkout(folder):
    """Clone once; refuse an existing checkout that is not the unmodified pinned commit."""
    msst = folder / 'msst'
    if not msst.exists():
        git('clone', '--quiet', REPOSITORY, str(msst))
        git('-C', str(msst), 'checkout', '--quiet', '--detach', COMMIT)
    if git('-C', str(msst), 'rev-parse', 'HEAD') != COMMIT or git('-C', str(msst), 'status', '--porcelain', '--untracked-files=no'):
        raise RuntimeError(f'分離モデルのコードが固定コミット {COMMIT} と一致しません。既存のファイルは変更しません。')


def fetch(url, target, expected):
    """Download to a temporary name and keep the file only when its SHA-256 matches."""
    target.parent.mkdir(parents=True, exist_ok=True)
    if target.is_file() and digest(target) == expected:
        return
    partial = target.with_name(target.name + '.partial')
    try:
        with urllib.request.urlopen(url) as response, partial.open('wb') as output:
            shutil.copyfileobj(response, output, 1 << 20)
        if digest(partial) != expected:
            raise RuntimeError(f'{target.name} のSHA-256が一致しません。もう一度セットアップしてください。')
        os.replace(partial, target)
    finally:
        partial.unlink(missing_ok=True)


def smoke_test(folder, runtime):
    """Separate two seconds of noise offline, so strict weight loading and the runner fail here, not in analysis."""
    import numpy as np
    import soundfile as sf
    import torch
    from separation import separate
    work = folder / 'setup-check'
    shutil.rmtree(work, ignore_errors=True)
    work.mkdir()
    try:
        noise = np.random.default_rng(0).normal(0, .05, (88200, 2)).astype(np.float32)
        sf.write(str(work / 'noise.wav'), noise, 44100, subtype='FLOAT')
        separate(work / 'noise.wav', work / 'stems', runtime, 'cuda' if torch.cuda.is_available() else 'cpu')
    finally:
        shutil.rmtree(work, ignore_errors=True)


def install(runtime):
    folder = home(runtime)
    folder.mkdir(parents=True, exist_ok=True)
    (folder / 'installation.json').unlink(missing_ok=True)
    print('Download: separation code (MSST)', flush=True)
    checkout(folder)
    for download in DOWNLOADS:
        print(f'Download: {Path(download.path).name}', flush=True)
        fetch(download.url, folder / download.path, download.sha256)
    files = code_files(folder) + [download.path for download in DOWNLOADS]
    write_json(folder / 'installation.json', dict(setup=SETUP_ID, repository=REPOSITORY, commit=COMMIT,
                                                  files={name: digest(folder / name) for name in files}))
    print('Check: separation', flush=True)
    try:
        smoke_test(folder, runtime)
    except BaseException:
        (folder / 'installation.json').unlink(missing_ok=True)
        raise
