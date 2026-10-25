import sys
import unittest
from pathlib import Path
import numpy as np
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from measures import level_db, sdr
from report import markdown


class MeasureTests(unittest.TestCase):
    def setUp(self):
        self.reference = np.sin(np.linspace(0, 200, 44100 * 2)).reshape(-1, 2).astype(np.float32)

    def test_sdr_of_a_scaled_estimate_is_twenty_decibels(self):
        self.assertAlmostEqual(sdr(self.reference, self.reference * .9), 20, places=3)

    def test_sdr_rejects_misaligned_stems(self):
        with self.assertRaises(ValueError):
            sdr(self.reference, self.reference[1:])

    def test_level_of_half_scale_square_wave_is_minus_six_dbfs(self):
        square = np.full((100, 2), .5, dtype=np.float32)
        square[::2] *= -1
        self.assertAlmostEqual(level_db(square), -6.0206, places=3)

    def test_silence_has_no_level(self):
        self.assertIsNone(level_db(np.zeros((10, 2), dtype=np.float32)))


class ReportTests(unittest.TestCase):
    def test_missing_measures_are_shown_as_dashes(self):
        text = markdown(dict(input='song.wav', excerpt=dict(start=0, seconds=30), device='cpu', torch='2.8.0',
                             msstCommit='abc', models=[dict(id='htdemucs_ft', license='MIT', elapsedSeconds=12.345)]))
        row = next(line for line in text.splitlines() if line.startswith('| htdemucs_ft'))
        self.assertEqual(row, '| htdemucs_ft | MIT | 12.35 | - | - | - | - | - | - |')


if __name__ == '__main__':
    unittest.main()
