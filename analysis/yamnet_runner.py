"""Offline CPU inference in the isolated TensorFlow environment."""
import argparse
import csv
import math
import socket
from pathlib import Path
import numpy as np
import soundfile as sf
from scipy.signal import resample_poly
from storage import read_json, write_json
from vocal_labels import CLASSES
from yamnet import verify


def deny_network(*args, **kwargs):
    raise RuntimeError('YAMNet推論中の通信は禁止しています。')


def score_audio(model, path, labels, duration):
    import tensorflow as tf
    audio, sr = sf.read(path, dtype='float32', always_2d=True)
    audio = audio.mean(axis=1)
    if not len(audio) or not np.isfinite(audio).all():
        raise ValueError('音声が空、または不正な値を含んでいます。')
    if sr != 16000:
        divisor = math.gcd(sr, 16000)
        audio = resample_poly(audio, 16000 // divisor, sr // divisor).astype(np.float32)
    peak = float(np.max(np.abs(audio)))
    gain = min(1., 1. / peak) if peak else 1.
    audio *= gain
    # Exact hop-aligned chunks preserve the official framing without a whole-song CNN batch.
    hop, window, batch = 7680, 15600, 20
    count = max(1, math.ceil(max(0, len(audio) - window) / hop) + 1)
    frames = []
    for offset in range(0, count, batch):
        size = min(batch, count - offset)
        start = offset * hop
        length = (size - 1) * hop + window
        final = offset + batch >= count
        clip = audio[start:] if final else audio[start:start + length]
        scores, _, _ = model(tf.convert_to_tensor(clip, dtype=tf.float32))
        values = scores.numpy()
        # The SavedModel may add an extra padded patch at an exact hop boundary.
        # Keep the natural final padding; overlap patches in intermediate chunks
        # belong to the next chunk and must not be emitted twice.
        if values.ndim != 2 or values.shape[1] != 521 or not size <= len(values) <= size + 1:
            raise ValueError('YAMNet出力の形が想定と異なります。')
        if not final:
            values = values[:size]
        for i, values_at_time in enumerate(values):
            a = (offset + i) * .48
            if a >= duration:
                break
            class_scores = {name: float(values_at_time[labels[name]]) for names in CLASSES.values() for name in names}
            frames.append({'start': round(a, 6), 'end': round(min(a + .975, duration), 6),
                           'classScores': class_scores,
                           'scores': {category: max(class_scores[name] for name in names) for category, names in CLASSES.items()}})
    return frames, gain


def main(home, output):
    verify(home)
    socket.create_connection = deny_network
    socket.socket.connect = deny_network
    import tensorflow as tf
    tf.config.threading.set_intra_op_parallelism_threads(4)
    tf.config.threading.set_inter_op_parallelism_threads(1)
    model = tf.saved_model.load(str(home / 'model'))
    with (home / 'model/assets/yamnet_class_map.csv').open(encoding='utf-8') as stream:
        labels = {r['display_name']: int(r['index']) for r in csv.DictReader(stream)}
    request = read_json(output / 'request.json')
    sources, gains = {}, {}
    for source, path in request['sources'].items():
        sources[source], gains[source] = score_audio(model, path, labels, request['duration'])
    write_json(output / 'scores.json', {'sources': sources, 'engine': {'tensorflow': tf.__version__, 'device': 'cpu',
               'sampleRate': 16000, 'windowSeconds': .975, 'hopSeconds': .48, 'inputGains': gains, 'resampling': 'scipy.signal.resample_poly'}})


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--home', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    main(args.home, args.output)
