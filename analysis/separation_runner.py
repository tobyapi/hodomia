"""Offline subprocess that splits one 44.1 kHz stereo file into the four analysis stems with pinned MSST code."""
import argparse
import json
import socket
import sys
import time
from pathlib import Path


def deny_network():
    def refuse(*_args, **_kwargs):
        raise RuntimeError('分離はオフラインで実行します。ネット接続は禁止です。')
    socket.create_connection = refuse
    socket.socket.connect = refuse
    socket.socket.connect_ex = refuse


def analysis_stems(mix, vocals, rhythm):
    """Vocals from one model, drums and bass from another; other is what they leave, so the four sum to the mix."""
    stems = dict(vocals=vocals['vocals'], drums=rhythm['drums'], bass=rhythm['bass'])
    stems['other'] = mix - stems['vocals'] - stems['drums'] - stems['bass']
    return stems


def import_msst(checkout):
    """MSST's utils and models are namespace packages, so a same-named installed package would win."""
    sys.path.insert(0, str(checkout))
    import utils.settings
    if not Path(utils.settings.__file__).resolve().is_relative_to(checkout.resolve()):
        raise RuntimeError('分離モデルのコードが固定したチェックアウトから読み込まれていません。')


def run_model(model, folder, mix, device):
    """Return the model's used outputs as (frames, channels) arrays and the inference seconds."""
    import torch
    from utils.model_utils import demix
    from utils.settings import get_model_from_config
    network, config = get_model_from_config(model.model_type, str(folder / model.config))
    # weights_only refuses pickled code; strict loading refuses a checkpoint that does not fit the config.
    network.load_state_dict(torch.load(folder / model.weights, map_location='cpu', weights_only=True), strict=True)
    # On an 8 GB GPU a larger batch was not faster and left little memory for the rest of the system.
    config.inference.batch_size = 1
    network = network.to(device).eval()
    started = time.perf_counter()
    try:
        outputs = demix(config, network, mix.T, torch.device(device), model.model_type)
    finally:
        del network
        if device == 'cuda':
            torch.cuda.empty_cache()
    return {name: outputs[name].T for name in model.outputs}, time.perf_counter() - started


def main():
    parser = argparse.ArgumentParser()
    for name in ('--home', '--audio', '--output', '--metadata'):
        parser.add_argument(name, type=Path, required=True)
    parser.add_argument('--device', choices=('cuda', 'cpu'), required=True)
    args = parser.parse_args()
    deny_network()
    import numpy as np
    import soundfile as sf
    import torch
    from separation import RATE, RHYTHM, VOCALS
    import_msst(args.home / 'msst')
    torch.set_num_threads(min(8, torch.get_num_threads()))
    mix, rate = sf.read(str(args.audio), dtype='float32', always_2d=True)
    if rate != RATE or mix.shape[1] != 2:
        raise ValueError('分離の入力は44.1 kHzステレオである必要があります。')
    vocals, vocal_seconds = run_model(VOCALS, args.home, mix, args.device)
    rhythm, rhythm_seconds = run_model(RHYTHM, args.home, mix, args.device)
    for name, samples in analysis_stems(mix, vocals, rhythm).items():
        if not np.isfinite(samples).all():
            raise ValueError(f'分離結果の{name}に不正なサンプルがあります。')
        sf.write(str(args.output / f'{name}.wav'), np.ascontiguousarray(samples), rate, subtype='FLOAT')
    models = [dict(modelType=model.model_type, config=model.config, weights=model.weights,
                   outputs=list(model.outputs), seconds=seconds)
              for model, seconds in ((VOCALS, vocal_seconds), (RHYTHM, rhythm_seconds))]
    args.metadata.write_text(json.dumps(dict(device=args.device, torch=torch.__version__, batchSize=1,
                                             models=models), indent=2), encoding='utf-8')


if __name__ == '__main__':
    main()
