"""ChordMini subprocess boundary: validated intervals and reproducible provenance."""
import hashlib
import math
import os
import subprocess
import time
from pathlib import Path
from storage import read_json, row, write_json

COMMIT = 'aa6e3a8d7b017f082fd2aaff9329d5c26af49c03'


def read_lab(path, duration):
    rows, previous = [], 0.
    for number, line in enumerate(Path(path).read_text(encoding='utf-8').splitlines(), 1):
        if not line.strip() or line.lstrip().startswith('#'):
            continue
        parts = line.split()
        if len(parts) != 3:
            raise ValueError(f'ChordMini: invalid label at line {number}')
        start, end = float(parts[0]), float(parts[1])
        if not (math.isfinite(start) and math.isfinite(end) and 0 <= start < end <= duration + 1e-6):
            raise ValueError(f'ChordMini: invalid time at line {number}')
        if abs(start - previous) > 1e-6:
            raise ValueError(f'ChordMini: gap or overlap at line {number}')
        rows.append(row('chord', len(rows), start, min(end, duration), parts[2],
                        warning='学習済みモデルの推定。正解率・信頼度は未評価です。'))
        previous = end
    if not rows or duration - previous > 2048 / 22050 + 1e-6:
        raise ValueError('ChordMini: missing or incomplete chord output')
    return rows


def digest(path):
    with Path(path).open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


def verify_installation(home):
    installation = read_json(home / 'installation.json')
    if installation.get('commit') != COMMIT or not installation.get('files'):
        raise ValueError('ChordMiniのセットアップをやり直してください。')
    for name, expected in installation['files'].items():
        if name == 'checkpoints/2e1d_model_best.pth':
            continue  # Older installations also recorded the unused comparison checkpoint.
        if digest(home / 'repo' / name) != expected:
            raise ValueError('ChordMiniのファイルがセットアップ後に変更されています: ' + name)


def infer(audio, runtime, output, duration, check_cancel=lambda: None):
    home, output = Path(runtime) / 'chordmini', Path(output) / 'chordmini'
    python = home / 'venv' / ('Scripts/python.exe' if os.name == 'nt' else 'bin/python')
    repo = home / 'repo'
    if not python.is_file() or not (repo / 'config/ChordMini.yaml').is_file():
        raise ValueError('ChordMiniが未準備です。npm run setup:chordmini を実行してください。')
    verify_installation(home)
    checkpoint = repo / 'checkpoints/btc_model_best.pth'
    output.mkdir(parents=True, exist_ok=False)
    command = [str(python), str(Path(__file__).with_name('chordmini_runner.py')), '--repo', str(repo.resolve()),
               '--audio', str(Path(audio).resolve()), '--output', str(output.resolve())]
    started = time.monotonic()
    with (output / 'inference.log').open('w', encoding='utf-8') as log:
        with subprocess.Popen(command, stdout=log, stderr=subprocess.STDOUT,
                              env={**os.environ, 'PYTHONUTF8': '1'},
                              creationflags=subprocess.CREATE_NO_WINDOW if os.name == 'nt' else 0) as process:
            try:
                while process.poll() is None:
                    check_cancel()
                    if time.monotonic() - started > 1800:
                        raise TimeoutError('ChordMiniの解析が30分を超えました。')
                    time.sleep(.2)
            except BaseException:
                process.kill()
                process.wait()
                raise
            if process.returncode:
                raise RuntimeError('ChordMiniの推論に失敗しました。解析フォルダーのchordmini/inference.logを確認してください。')
    rows = read_lab(output / 'chords.lab', duration)
    metadata = read_json(output / 'inference.json')
    metadata.update(backend='chordmini-btc', source='original', repository='https://github.com/ptnghia-j/ChordMini',
                    commit=COMMIT, checkpoint=checkpoint.name, checkpointSha256=digest(checkpoint),
                    configSha256=digest(repo / 'config/ChordMini.yaml'), audioSha256=digest(audio),
                    elapsedSeconds=time.monotonic() - started, coverageEnd=rows[-1]['end'])
    write_json(output / 'inference.json', metadata)
    return rows, metadata
