"""Verified Mel-Band inference in an isolated process, with reusable provenance."""
import hashlib
import os
import subprocess
import time
from pathlib import Path
from storage import read_json, write_json, within

VERSION = '0.47.0'
MODEL = 'vocals_mel_band_roformer.ckpt'
CONFIG = 'vocals_mel_band_roformer.yaml'
FILES = {
    MODEL: ('https://huggingface.co/KimberleyJSN/melbandroformer/resolve/ac9b0614ab3cd7f77219e18ba494dfd93956c348/MelBandRoformer.ckpt',
            '87201f4d31afb5bc79993230fc49446918425574db48c01c405e44f365c7559e'),
    CONFIG: ('https://github.com/nomadkaraoke/python-audio-separator/releases/download/model-configs/vocals_mel_band_roformer.yaml',
             'b958b29c8f7195f0d86bee6759a33980db675c4ecaf2fcaa80fa125828e6cd38'),
}
SETTINGS = dict(segmentSize=801, overlap=4, autocast=True, sampleRate=44100, channels=2,
                normalizationThreshold=1., amplificationThreshold=0., pitchShift=0)


def digest(path):
    with Path(path).open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


def verify(home):
    home = Path(home)
    installation = read_json(home / 'installation.json')
    if installation.get('version') != VERSION or installation.get('files') != {k: v[1] for k, v in FILES.items()}:
        raise ValueError('Mel-Bandをセットアップしてください。')
    for name, (_, expected) in FILES.items():
        if digest(home / 'models' / name) != expected:
            raise ValueError('Mel-Bandの重みまたは設定が変更されています。再セットアップしてください。')
    return installation


def validate_outputs(folder, duration):
    import soundfile as sf
    import numpy as np
    outputs = {}
    for name in ('melband_vocals', 'melband_instrumental'):
        path = Path(folder) / (name + '.wav')
        with sf.SoundFile(path) as stream:
            if stream.samplerate != 44100 or stream.channels != 2 or abs(len(stream) / 44100 - duration) > .02:
                raise ValueError('Mel-Bandの出力音声の長さ・形式が不正です。')
            for block in stream.blocks(blocksize=44100):
                if not np.isfinite(block).all():
                    raise ValueError('Mel-Bandの出力に非有限値があります。')
        outputs[name] = path
    return outputs


def cached_result(root, previous, key):
    if not previous or previous.get('engine', {}).get('cacheKey') != key:
        return None
    stems = previous.get('stems', {})
    if set(stems) != {'melband_vocals', 'melband_instrumental'}:
        return None
    for name, relative in stems.items():
        path = within(root, relative)
        if not path.is_file() or digest(path) != previous['engine'].get('outputHashes', {}).get(name):
            return None
    return previous


def separate(audio, root, runtime, folder, duration, check_cancel, previous=None):
    home = Path(runtime) / 'melband'
    installation = verify(home)
    key = dict(inputHash=digest(audio), files=installation['files'], version=VERSION,
               packages=installation['packages'], settings=SETTINGS, runnerHash=digest(Path(__file__).with_name('melband_runner.py')))
    cached = cached_result(root, previous, key)
    if cached:
        check_cancel()
        return cached
    output = Path(folder) / 'melband'
    output.mkdir()
    python = home / 'venv' / ('Scripts/python.exe' if os.name == 'nt' else 'bin/python')
    started = time.monotonic()
    for segment in (801, 401):
        command = [str(python), str(Path(__file__).with_name('melband_runner.py')), str(home.resolve()),
                   str(Path(audio).resolve()), str(output.resolve()), str(segment)]
        with (output / f'inference-{segment}.log').open('w', encoding='utf-8') as log:
            with subprocess.Popen(command, stdout=log, stderr=subprocess.STDOUT,
                                  env={**os.environ, 'PYTHONUTF8': '1'},
                                  creationflags=subprocess.CREATE_NO_WINDOW if os.name == 'nt' else 0) as process:
                try:
                    while process.poll() is None:
                        check_cancel()
                        if time.monotonic() - started > 7200:
                            raise TimeoutError('Mel-Bandの処理が2時間を超えました。')
                        time.sleep(.2)
                except BaseException:
                    process.kill()
                    process.wait()
                    raise
        if process.returncode == 0:
            break
        if process.returncode != 42 or segment == 401:
            raise RuntimeError(f'Mel-Bandの分離に失敗しました。melband/inference-{segment}.logを確認してください。')
    check_cancel()
    paths = validate_outputs(output, duration)
    engine = read_json(output / 'engine.json')
    if engine['packages'] != installation['packages']:
        raise ValueError('Mel-Bandの依存がセットアップ後に変更されています。')
    engine.update(cacheKey=key, elapsedSeconds=time.monotonic() - started,
                  outputHashes={name: digest(path) for name, path in paths.items()})
    result = dict(stems={name: str(path.relative_to(root)).replace('\\', '/') for name, path in paths.items()}, engine=engine)
    write_json(output / 'provenance.json', result)
    return result
