import sys
import tempfile
import unittest
from pathlib import Path
import numpy as np
import soundfile as sf
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from vocal_percussion import detect, onset_regions
from dsp import accompaniment

class PercussionTests(unittest.TestCase):
    def test_isolated_hits_are_not_continuous_beatboxing(self):
        self.assertEqual(onset_regions([.1, 2, 4], 5), [])
        self.assertEqual(onset_regions([.1, .6, 3], 4), [(0., .8999999999999999)])

    def test_missing_and_silent_vocals_do_not_invent_candidates(self):
        self.assertEqual(detect(None, 5, []), [])
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / 'silent.wav'
            sf.write(path, np.zeros(16000), 16000)
            self.assertEqual(detect(path, 1, []), [])

    def test_chord_input_excludes_vocals_and_drums(self):
        with tempfile.TemporaryDirectory() as folder:
            paths = {}
            for name, level in [('bass', .1), ('other', .2), ('vocals', .4), ('drums', .5)]:
                paths[name] = Path(folder) / (name + '.wav')
                sf.write(paths[name], np.full(16000, level), 16000, subtype='FLOAT')
            mixed, source = accompaniment(paths, np.zeros(16000), 16000)
            np.testing.assert_allclose(mixed, .3, atol=1e-6)
            self.assertIn('bass + other', source)
