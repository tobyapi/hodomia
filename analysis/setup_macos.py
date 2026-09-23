"""Install the pinned Apple Silicon analysis environment before offline inference."""
import argparse
import platform
import subprocess
from pathlib import Path

from chordmini import COMMIT
from locking import file_lock


def run(*args):
    subprocess.run(args, check=True)


def install_chordmini(runtime, source):
    home = runtime / 'chordmini'
    repo = home / 'repo'
    python = home / 'venv/bin/python'
    home.mkdir(parents=True, exist_ok=True)
    if not repo.exists():
        run('git', 'clone', 'https://github.com/ptnghia-j/ChordMini.git', str(repo))
        run('git', '-C', str(repo), 'checkout', '--detach', COMMIT)
    actual = subprocess.check_output(['git', '-C', str(repo), 'rev-parse', 'HEAD'], text=True).strip()
    if actual != COMMIT:
        raise RuntimeError('ChordMini の固定コミットが一致しません。既存ファイルは変更しません。')
    if not python.exists():
        run('uv', 'venv', str(home / 'venv'), '--python', '3.11')
    run('uv', 'pip', 'install', '--python', str(python), '-r', str(repo / 'requirements.txt'))
    run(str(python), str(source / 'analysis/chordmini_install.py'), str(home))
    with (home / 'requirements.lock.txt').open('w', encoding='utf-8') as output:
        subprocess.run(['uv', 'pip', 'freeze', '--python', str(python)], check=True, stdout=output)
    print('コードモデルの準備が完了しました。', flush=True)


def install_analysis(runtime, source):
    python = runtime / 'venv/bin/python'
    if not python.exists():
        run('uv', 'venv', str(runtime / 'venv'), '--python', '3.11')
    lock = source / 'analysis/requirements.macos-arm64.lock.txt'
    run('uv', 'pip', 'install', '--python', str(python), '-r', str(lock))
    run(str(python), str(source / 'analysis/prepare.py'), '--runtime', str(runtime))
    with (runtime / 'requirements.lock.txt').open('w', encoding='utf-8') as output:
        subprocess.run(['uv', 'pip', 'freeze', '--python', str(python)], check=True, stdout=output)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('runtime', type=Path)
    parser.add_argument('mode', choices=('full', 'chordmini'))
    args = parser.parse_args()
    if platform.system() != 'Darwin' or platform.machine() != 'arm64':
        raise RuntimeError('このセットアップは Apple Silicon 搭載 Mac 向けです。')
    runtime = args.runtime.resolve()
    source = Path(__file__).resolve().parent.parent
    runtime.mkdir(parents=True, exist_ok=True)
    with file_lock(runtime / 'control/analysis.lock'):
        if args.mode == 'full':
            install_analysis(runtime, source)
        install_chordmini(runtime, source)
    print('解析環境の準備が完了しました。', flush=True)


if __name__ == '__main__':
    main()
