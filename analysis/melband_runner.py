"""Offline adapter to a pinned audio-separator model; no model discovery/downloads."""
import importlib.metadata
import os
import socket
import subprocess
import sys
from pathlib import Path
from melband import MODEL, CONFIG, SETTINGS, VERSION, verify
from storage import write_json


def packages():
    return {name: importlib.metadata.version(name) for name in ('audio-separator', 'torch', 'torchaudio', 'numpy', 'librosa', 'onnxruntime', 'imageio-ffmpeg')}


def deny_network(*args, **kwargs):
    raise RuntimeError('Mel-Band推論中の通信は禁止されています。')


def run(home, audio, output, segment):
    socket.create_connection = deny_network
    socket.socket.connect = deny_network
    import torch
    from audio_separator.separator import Separator
    installation = verify(home)
    if packages() != installation['packages'] or packages()['audio-separator'] != VERSION:
        raise ValueError('Mel-Bandの環境を再セットアップしてください。')
    torch.set_num_threads(min(8, os.cpu_count() or 1))

    class LocalSeparator(Separator):
        def check_ffmpeg_installed(self):
            import imageio_ffmpeg
            subprocess.run([imageio_ffmpeg.get_ffmpeg_exe(), '-version'], check=True, stdout=subprocess.DEVNULL,
                           creationflags=subprocess.CREATE_NO_WINDOW if os.name == 'nt' else 0)

        def download_model_files(self, model_filename):
            if model_filename != MODEL:
                raise ValueError('未対応の分離モデルです。')
            return MODEL, 'MDXC', 'Kimberley Jensen Mel-Band', str(home / 'models' / MODEL), str(home / 'models' / CONFIG)

    separator = LocalSeparator(model_file_dir=str(home / 'models'), output_dir=str(output),
                               output_format='WAV', use_soundfile=True, use_autocast=True,
                               normalization_threshold=1., amplification_threshold=0.,
                               mdxc_params={'segment_size': segment, 'override_model_segment_size': True,
                                            'overlap': 4, 'batch_size': 1, 'pitch_shift': 0})
    separator.load_model(MODEL)
    separator.separate(str(audio), custom_output_names={'Vocals': 'melband_vocals', 'Other': 'melband_instrumental', 'Instrumental': 'melband_instrumental'})
    write_json(output / 'engine.json', dict(model='KimberleyJSN/melbandroformer', packages=packages(),
               device=str(separator.torch_device), settings={**SETTINGS, 'segmentSize': segment},
               fallback=segment != SETTINGS['segmentSize'], network='disabled', license='MIT',
               notice='分離結果の比較用。発声の保存性能は試聴で確認してください。'))


if __name__ == '__main__':
    try:
        run(Path(sys.argv[1]).resolve(), Path(sys.argv[2]).resolve(), Path(sys.argv[3]).resolve(), int(sys.argv[4]))
    except Exception as error:
        if 'out of memory' in str(error).lower() and 'cuda' in str(error).lower():
            print(str(error), file=sys.stderr)
            sys.exit(42)
        raise
