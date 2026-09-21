"""Online-only acquisition of the exact Mel-Band checkpoint and configuration."""
import shutil
import sys
import tempfile
import urllib.request
from pathlib import Path
from melband import FILES, VERSION, digest, verify
from melband_runner import packages
from storage import write_json


def install(home):
    home = Path(home).resolve()
    (home / 'models').mkdir(parents=True, exist_ok=True)
    for name, (url, expected) in FILES.items():
        target = home / 'models' / name
        if target.is_file() and digest(target) == expected:
            continue
        partial = target.with_suffix(target.suffix + '.partial')
        with urllib.request.urlopen(url, timeout=120) as response, partial.open('wb') as stream:
            shutil.copyfileobj(response, stream)
        if digest(partial) != expected:
            raise ValueError('Mel-Bandの配布ファイルのハッシュが一致しません: ' + name)
        partial.replace(target)
    import torch
    write_json(home / 'installation.json', dict(version=VERSION, files={k: v[1] for k, v in FILES.items()},
               packages=packages(), urls={k: v[0] for k, v in FILES.items()}, cudaAvailable=torch.cuda.is_available(),
               license='MIT', licenseUrl='https://huggingface.co/KimberleyJSN/melbandroformer'))
    verify(home)
    # Readiness includes offline model loading, strict weights and actual inference.
    import numpy as np
    import soundfile as sf
    from melband_runner import run
    from melband import validate_outputs
    try:
        with tempfile.TemporaryDirectory(dir=home) as temporary:
            output = Path(temporary)
            audio = output / 'silence.wav'
            sf.write(audio, np.zeros((44100, 2), dtype='float32'), 44100, subtype='FLOAT')
            run(home, audio, output, 401)
            validate_outputs(output, 1.)
    except BaseException:
        (home / 'installation.json').unlink(missing_ok=True)
        raise
    print('Mel-Bandの重み・設定・実行環境を準備しました。CUDA:', torch.cuda.is_available(), flush=True)


if __name__ == '__main__':
    install(sys.argv[1])
