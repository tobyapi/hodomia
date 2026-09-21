"""YAMNet process boundary; only a verified local model is used during inference."""
import hashlib
import math
import os
import subprocess
import time
from pathlib import Path
from storage import read_json, write_json, within
from vocal_labels import CLASSES

MODEL_URL = 'https://tfhub.dev/google/yamnet/1?tf-hub-format=compressed'
ARCHIVE_SHA256 = 'b80da2a1a56926fb0767205051a200dd7b3beaf3ea1ea126c42a53943996e5e0'


def digest(path):
    with Path(path).open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


def verify(home):
    installation = read_json(Path(home) / 'installation.json')
    if installation.get('archiveSha256') != ARCHIVE_SHA256 or not installation.get('files'):
        raise ValueError('YAMNetのセットアップをやり直してください。')
    for name, expected in installation['files'].items():
        if digest(within(home, name)) != expected:
            raise ValueError('YAMNetのモデルがセットアップ後に変更されています。')
    return installation


def validate_frames(sources, duration, expected_sources):
    if set(sources) != set(expected_sources):
        raise ValueError('YAMNetの入力音声と出力が一致しません。')
    for frames in sources.values():
        if not frames:
            raise ValueError('YAMNetのスコアがありません。')
        previous = -1.
        for index, frame in enumerate(frames):
            a, b = frame['start'], frame['end']
            if not all(math.isfinite(v) for v in (a, b)) or not 0 <= a < b <= duration + 1e-6 or a <= previous:
                raise ValueError('YAMNetの時刻が不正です。')
            if abs(a - index * .48) > 1e-6 or abs(b - min(a + .975, duration)) > 1e-6:
                raise ValueError('YAMNetの解析窓に欠落があります。')
            if set(frame['scores']) != set(CLASSES) or set(frame['classScores']) != {name for names in CLASSES.values() for name in names} or any(not math.isfinite(v) or not 0 <= v <= 1 for v in [*frame['scores'].values(), *frame['classScores'].values()]):
                raise ValueError('YAMNetのスコアが不正です。')
            previous = a
        if frames[0]['start'] != 0 or duration - frames[-1]['end'] > 1e-6:
            raise ValueError('YAMNetの末尾に欠落があります。')


def infer(sources, runtime, folder, duration, check_cancel):
    home = Path(runtime) / 'yamnet'
    python = home / 'venv' / ('Scripts/python.exe' if os.name == 'nt' else 'bin/python')
    installation = verify(home)
    output = Path(folder) / 'yamnet'
    output.mkdir()
    write_json(output / 'request.json', {'sources': {k: str(Path(v).resolve()) for k, v in sources.items()}, 'duration': duration})
    command = [str(python), str(Path(__file__).with_name('yamnet_runner.py')), '--home', str(home.resolve()), '--output', str(output.resolve())]
    started = time.monotonic()
    with (output / 'inference.log').open('w', encoding='utf-8') as log:
        with subprocess.Popen(command, stdout=log, stderr=subprocess.STDOUT,
                              env={**os.environ, 'PYTHONUTF8': '1', 'CUDA_VISIBLE_DEVICES': '-1', 'TF_CPP_MIN_LOG_LEVEL': '2'},
                              creationflags=subprocess.CREATE_NO_WINDOW if os.name == 'nt' else 0) as process:
            try:
                while process.poll() is None:
                    check_cancel()
                    if time.monotonic() - started > 900:
                        raise TimeoutError('YAMNetの比較処理が15分を超えました。')
                    time.sleep(.2)
            except BaseException:
                process.kill()
                process.wait()
                raise
            if process.returncode:
                raise RuntimeError('YAMNetの推論に失敗しました。解析フォルダーのyamnet/inference.logを確認してください。')
    result = read_json(output / 'scores.json')
    validate_frames(result['sources'], duration, sources)
    result['engine'].update(model='google/yamnet/1', archiveSha256=ARCHIVE_SHA256, modelFiles=installation['files'],
                            elapsedSeconds=time.monotonic() - started, inputHashes={k: digest(v) for k, v in sources.items()})
    write_json(output / 'scores.json', result)
    return result
