import sys
import tempfile
import unittest
from pathlib import Path
import numpy as np
import soundfile as sf
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from dsp import estimate_key, basics
from storage import effective_bpm, row


class SignalTests(unittest.TestCase):
    def test_known_major_key(self):
        sr = 22050
        t = np.arange(sr * 3) / sr
        signal = sum(np.sin(2 * np.pi * (440 * 2 ** ((note - 69) / 12)) * t) for note in [48, 52, 55]) / 4
        keys = estimate_key(signal, sr, 3)
        self.assertEqual(keys[0]['label'], 'C major')
        self.assertEqual((keys[0]['start'], keys[0]['end']), (0, 3))
        self.assertFalse(keys[0]['reviewed'])

    def test_silence_is_explicit(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / 'silence.wav'
            sf.write(path, np.zeros(22050), 22050)
            _, _, features, _ = basics(path)
            self.assertTrue(features['silence'])
            self.assertFalse(any(features['waveform']))

    def test_manual_beats_drive_export_bpm(self):
        tracks = {'beats': [row('b', i, i * .75, i * .75, '拍') for i in range(8)]}
        self.assertEqual(effective_bpm(tracks), 80)


if __name__ == '__main__':
    unittest.main()
