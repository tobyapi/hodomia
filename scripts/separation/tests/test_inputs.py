import sys
import tempfile
import unittest
from pathlib import Path
import numpy as np
import soundfile as sf
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from inputs import RATE, excerpt, prepare


class ExcerptTests(unittest.TestCase):
    def setUp(self):
        self.samples = np.arange(RATE * 4 * 2, dtype=np.float32).reshape(-1, 2)

    def test_cuts_the_requested_seconds(self):
        part = excerpt(self.samples, 1, 2)
        self.assertEqual(len(part), RATE * 2)
        self.assertEqual(part[0, 0], self.samples[RATE, 0])

    def test_without_duration_keeps_the_rest(self):
        self.assertEqual(len(excerpt(self.samples, 3, None)), RATE)

    def test_rejects_a_start_outside_the_song(self):
        with self.assertRaises(ValueError):
            excerpt(self.samples, 4, None)

    def test_rejects_an_empty_duration(self):
        with self.assertRaises(ValueError):
            excerpt(self.samples, 0, 0)


class PrepareTests(unittest.TestCase):
    def setUp(self):
        self.work = tempfile.TemporaryDirectory()
        self.folder = Path(self.work.name)
        self.project = self.folder / 'project'
        self.project.mkdir()
        self.mix = np.random.default_rng(1).uniform(-.5, .5, (RATE * 2, 2)).astype(np.float32)
        sf.write(str(self.project / 'audio.wav'), self.mix, RATE, subtype='FLOAT')

    def tearDown(self):
        self.work.cleanup()

    def test_project_folder_uses_its_decoded_audio_and_aligns_the_reference(self):
        reference_path = self.folder / 'vocals.wav'
        sf.write(str(reference_path), self.mix * .5, RATE, subtype='FLOAT')
        mix_path, mix, reference = prepare(self.project, self.folder, .5, 1, reference_path)
        np.testing.assert_array_equal(mix, self.mix[RATE // 2:RATE // 2 + RATE])
        np.testing.assert_array_equal(reference, mix * .5)
        self.assertTrue(mix_path.is_file())

    def test_rejects_a_reference_of_another_length(self):
        reference_path = self.folder / 'vocals.wav'
        sf.write(str(reference_path), self.mix[:RATE], RATE, subtype='FLOAT')
        with self.assertRaises(ValueError):
            prepare(self.project, self.folder, 0, None, reference_path)

    def test_rejects_a_mono_reference(self):
        reference_path = self.folder / 'vocals.wav'
        sf.write(str(reference_path), self.mix[:, 0], RATE, subtype='FLOAT')
        with self.assertRaises(ValueError):
            prepare(self.project, self.folder, 0, None, reference_path)


if __name__ == '__main__':
    unittest.main()
