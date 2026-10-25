"""Stem separation subprocess boundary: pinned MSST code and MIT-licensed weights, four validated stems."""
import hashlib
import sys
import time
from dataclasses import dataclass
from pathlib import Path
from model_process import run_logged
from storage import read_json, write_json

REPOSITORY = 'https://github.com/ZFTurbo/Music-Source-Separation-Training.git'
COMMIT = '6fdad13686bb7e84d029ec66f9dbe76e65c93ebf'
# ready.json and separation_setup.rs compare this; a new value asks existing installations to run setup again.
SETUP_ID = 'kim-melband-roformer+bs-roformer-ep17'
# Runs store this; a different value makes pipeline separate again instead of reusing older stems.
ENGINE = 'Mel-Band RoFormer Kimberley Jensen (vocals) + BS-RoFormer ZFTurbo ep_17 (drums, bass) / other=residual'
STEMS = ('vocals', 'drums', 'bass', 'other')
RATE = 44100
# An 8 GB GPU separates in about a fifth of the song's length; a busy desktop CPU took twelve times it.
LIMIT_PER_SECOND = 20
LIMIT_MARGIN_SECONDS = 600


@dataclass(frozen=True)
class Download:
    url: str
    path: str
    sha256: str


@dataclass(frozen=True)
class Model:
    model_type: str
    config: str
    weights: str
    outputs: tuple[str, ...]


# Kimberley Jensen's model card states MIT (Hugging Face KimberleyJSN/melbandroformer).
VOCALS = Model('mel_band_roformer', 'msst/configs/KimberleyJensen/config_vocals_mel_band_roformer_kj.yaml',
               'weights/MelBandRoformer.ckpt', ('vocals',))
# ZFTurbo released this checkpoint under MIT (MSST issue #254). Its vocals and other stems are not used.
RHYTHM = Model('bs_roformer', 'weights/config_bs_roformer_384_8_2_485100.yaml',
               'weights/model_bs_roformer_ep_17_sdr_9.6568.ckpt', ('drums', 'bass'))
RELEASE = 'https://github.com/ZFTurbo/Music-Source-Separation-Training/releases/download/v1.0.12/'
DOWNLOADS = (
    Download('https://huggingface.co/KimberleyJSN/melbandroformer/resolve/'
             'ac9b0614ab3cd7f77219e18ba494dfd93956c348/MelBandRoformer.ckpt', VOCALS.weights,
             '87201f4d31afb5bc79993230fc49446918425574db48c01c405e44f365c7559e'),
    Download(RELEASE + 'config_bs_roformer_384_8_2_485100.yaml', RHYTHM.config,
             'd8afb980318d0c08b9c2e24a7adc00d4f3150320c127a7e4de861800d1321939'),
    Download(RELEASE + 'model_bs_roformer_ep_17_sdr_9.6568.ckpt', RHYTHM.weights,
             '3e9daecd70aaed5b5a0d1f861cc4d77eaa45afb3fc6301b1cf32c1be0f5868fb'),
)


def home(runtime):
    return Path(runtime) / 'separation'


def digest(path):
    with Path(path).open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


def code_files(folder):
    """The MSST files the runner imports, relative to the separation home."""
    msst = folder / 'msst'
    paths = sorted(msst.glob('utils/*.py')) + sorted(msst.glob('models/bs_roformer/*.py'))
    return [path.relative_to(folder).as_posix() for path in paths] + [VOCALS.config]


def verify_installation(folder):
    installation = folder / 'installation.json'
    if not installation.is_file():
        raise RuntimeError('分離モデルが未準備です。セットアップを実行してください。')
    data = read_json(installation)
    if data.get('commit') != COMMIT or data.get('setup') != SETUP_ID or not data.get('files'):
        raise RuntimeError('分離モデルが更新されています。セットアップを実行してください。')
    for name, expected in data['files'].items():
        if not (folder / name).is_file() or digest(folder / name) != expected:
            raise ValueError('分離モデルのファイルがセットアップ後に変更されています: ' + name)


def check_stems(paths, frames):
    import soundfile as sf
    for name, path in paths.items():
        if not path.is_file():
            raise ValueError(f'分離結果に{name}がありません。')
        info = sf.info(str(path))
        if info.frames != frames or info.samplerate != RATE or info.channels != 2:
            raise ValueError(f'分離結果の{name}が原曲と同じ長さの44.1 kHzステレオではありません。')


def separate(audio, stems, runtime, device, check_cancel=lambda: None, python=sys.executable):
    """Write vocals, drums, bass and other next to each other, as All-In-One reads them from one folder."""
    import soundfile as sf
    folder, log = home(runtime), Path(stems).parent / 'separation'
    verify_installation(folder)
    stems = Path(stems)
    stems.mkdir(parents=True, exist_ok=True)
    log.mkdir(exist_ok=True)
    command = [str(python), str(Path(__file__).with_name('separation_runner.py')), '--home', str(folder.resolve()),
               '--audio', str(Path(audio).resolve()), '--output', str(stems.resolve()),
               '--device', device, '--metadata', str((log / 'separation.json').resolve())]
    frames = sf.info(str(audio)).frames
    limit = LIMIT_MARGIN_SECONDS + LIMIT_PER_SECOND * frames / RATE
    started = time.monotonic()
    if run_logged(command, log / 'separation.log', check_cancel, limit, f'分離が{limit / 60:.0f}分を超えました。'):
        raise RuntimeError('分離に失敗しました。解析フォルダーのseparation/separation.logを確認してください。')
    paths = {name: stems / f'{name}.wav' for name in STEMS}
    check_stems(paths, frames)
    metadata = read_json(log / 'separation.json')
    metadata.update(engine=ENGINE, repository=REPOSITORY, commit=COMMIT, elapsedSeconds=time.monotonic() - started)
    write_json(log / 'separation.json', metadata)
    return paths
