import sys
import tempfile
import unittest
from pathlib import Path
import numpy as np
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from candidates import STEMS
from stem_sets import combine, complete, has_all, read, write


def tone(value):
    return np.full((8, 2), value, dtype=np.float32)


class StemSetTests(unittest.TestCase):
    def setUp(self):
        self.mix = tone(1)

    def test_missing_other_is_what_the_mix_leaves(self):
        stems = complete(self.mix, dict(vocals=tone(.4), drums=tone(.2), bass=tone(.1)))
        np.testing.assert_allclose(stems['other'], tone(.3), atol=1e-6)
        self.assertTrue(has_all(stems))

    def test_a_vocal_model_gets_no_other_stem(self):
        stems = complete(self.mix, dict(vocals=tone(.4)))
        self.assertEqual(set(stems), {'vocals'})
        self.assertFalse(has_all(stems))

    def test_a_model_own_other_stem_is_kept(self):
        stems = complete(self.mix, dict(vocals=tone(.4), drums=tone(.2), bass=tone(.1), other=tone(.25)))
        np.testing.assert_allclose(stems['other'], tone(.25))

    def test_combined_stems_sum_to_the_mix(self):
        stems = combine(self.mix, tone(.5), dict(drums=tone(.2), bass=tone(.1), other=tone(.9), vocals=tone(.9)))
        np.testing.assert_allclose(sum(stems[name] for name in STEMS), self.mix, atol=1e-6)
        np.testing.assert_allclose(stems['vocals'], tone(.5))

    def test_written_stems_read_back_unchanged(self):
        stems = complete(self.mix, dict(vocals=tone(.4), drums=tone(.2), bass=tone(.1)))
        with tempfile.TemporaryDirectory() as work:
            folder = Path(work) / 'stems'
            write(folder, stems, 44100)
            self.assertEqual(sorted(path.name for path in folder.iterdir()), [f'{name}.wav' for name in STEMS])
            np.testing.assert_array_equal(read(folder, ['other'])['other'], stems['other'])


if __name__ == '__main__':
    unittest.main()
