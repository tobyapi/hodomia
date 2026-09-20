import sys
import tempfile
import unittest
from pathlib import Path
import numpy as np
import soundfile as sf
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from dsp import harmony, basics
from storage import effective_bpm, row


class SignalTests(unittest.TestCase):
    def test_known_major_and_minor_chords(self):
        sr = 22050
        t = np.arange(sr * 3) / sr
        def chord(notes):
            return sum(np.sin(2 * np.pi * (440 * 2 ** ((note - 69) / 12)) * t) for note in notes) / 4
        signal = np.concatenate([chord([48, 52, 55]), chord([45, 48, 52])])
        value = harmony(signal, sr, 6, np.arange(0, 6, .5))
        for time, expected in [(1.5, 'C'), (4.5, 'Am')]:
            actual = next(r['label'] for r in value['chords'] if r['start'] <= time < r['end'])
            self.assertEqual(actual, expected)

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
