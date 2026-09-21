"""Isolated offline entry point for the pinned official ChordMini inference code."""
import argparse
import json
import math
import socket
import sys
from pathlib import Path


def strict_loader(original):
    def load(module, state, strict=True, **kwargs):
        if not strict:
            raise RuntimeError('ChordMini: checkpoint mismatch; non-strict loading is prohibited')
        return original(module, state, strict=True, **kwargs)
    return load


def normalization(checkpoint):
    stats = {**checkpoint, **checkpoint.get('normalization', {})}
    if 'mean' not in stats or 'std' not in stats:
        raise ValueError('ChordMini: checkpoint normalization statistics are missing')
    mean, std = float(stats['mean']), float(stats['std'])
    if not math.isfinite(mean) or not math.isfinite(std) or std <= 0:
        raise ValueError('ChordMini: invalid normalization statistics')
    return mean, std


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--repo', type=Path, required=True)
    parser.add_argument('--audio', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()

    def deny_network(*_args, **_kwargs):
        raise RuntimeError('ChordMini inference is offline; network access is prohibited')
    socket.create_connection = deny_network
    socket.socket.connect = deny_network
    socket.socket.connect_ex = deny_network
    sys.path.insert(0, str(args.repo))
    import numpy as np
    import torch
    import librosa
    from src.evaluation import test as official

    torch.nn.Module.load_state_dict = strict_loader(torch.nn.Module.load_state_dict)
    torch.set_num_threads(min(8, torch.get_num_threads()))
    official.set_random_seed(42, include_python_random=True)
    checkpoint = args.repo / 'checkpoints/btc_model_best.pth'
    mean, std = normalization(torch.load(checkpoint, map_location='cpu', weights_only=False))
    config = official.HParams.load(str(args.repo / 'config/ChordMini.yaml'))
    device = official.get_device()
    model, _, _ = official.load_model(str(checkpoint), 'BTC', config, device)
    model.eval()
    seq_len = official._resolve_seq_len(config, model, str(checkpoint))
    features, frame_duration, duration = official._extract_song_features_root_compatible(str(args.audio), config)
    predictions = official.predict_sliding_windows(
        model=model, feature_matrix=features, mean=mean, std=std, seq_len=seq_len,
        batch_size=16, model_type='BTC', n_classes=170, vote_aggregation='logit',
        use_overlap=True, overlap_ratio=.5, smooth_logits=False,
        smooth_predictions=False, kernel_size=1, use_gaussian=False,
    )
    frames = int(np.floor(duration / frame_duration))
    if frames > 0:
        predictions = predictions[:frames]
    lines = official._prediction_segments(predictions, frame_duration, official.idx2voca_chord(), 0.)
    args.output.mkdir(parents=True, exist_ok=True)
    (args.output / 'chords.lab').write_text(''.join(lines), encoding='utf-8')
    metadata = dict(model='BTC', device=str(device), torch=torch.__version__, librosa=librosa.__version__,
                    mean=mean, std=std, sequenceLength=seq_len, frameDuration=frame_duration,
                    featureShape=list(features.shape), strict=True, seed=42, overlap=.5,
                    aggregation='logit', smoothLogits=False, gaussian=False,
                    kernelSize=1, minSegmentDuration=0)
    (args.output / 'inference.json').write_text(json.dumps(metadata, indent=2), encoding='utf-8')


if __name__ == '__main__':
    main()
