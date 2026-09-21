"""Opt-in check of chunked inference against the official full-waveform call."""
import csv
import sys
import tempfile
from pathlib import Path
import numpy as np
import soundfile as sf
import tensorflow as tf

root = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(root / 'analysis'))
from yamnet_runner import score_audio
from yamnet import verify
from vocal_labels import CLASSES

home = Path(sys.argv[1]) if len(sys.argv) > 1 else root / '.runtime/yamnet'
verify(home)
model = tf.saved_model.load(str(home / 'model'))
with (home / 'model/assets/yamnet_class_map.csv').open(encoding='utf-8') as stream:
    labels = {r['display_name']: int(r['index']) for r in csv.DictReader(stream)}
for duration in (.2, 10.095, 11.2, 19.695):
    audio = np.random.default_rng(42).normal(0, .1, round(duration * 16000)).astype(np.float32)
    with tempfile.TemporaryDirectory() as folder:
        source = Path(folder) / 'input.wav'
        sf.write(source, audio, 16000, subtype='FLOAT')
        frames, gain = score_audio(model, str(source), labels, duration)
    reference, _, _ = model(tf.convert_to_tensor(audio))
    assert len(frames) == reference.shape[0]
    assert gain == 1
    for name in (name for names in CLASSES.values() for name in names):
        np.testing.assert_allclose([frame['classScores'][name] for frame in frames], reference.numpy()[:, labels[name]], rtol=1e-4, atol=1e-6)
    print(f'{duration}s / {len(frames)} frames: matches official full-waveform inference')
