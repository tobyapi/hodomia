import hashlib
import re
import sys
import tempfile
import unittest
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from candidates import BASELINE, CANDIDATES
from prepare import fetch


class FetchTests(unittest.TestCase):
    def setUp(self):
        self.work = tempfile.TemporaryDirectory()
        self.folder = Path(self.work.name)
        self.source = self.folder / 'source.ckpt'
        self.source.write_bytes(b'weights')
        self.digest = hashlib.sha256(b'weights').hexdigest()
        self.target = self.folder / 'target.ckpt'

    def tearDown(self):
        self.work.cleanup()

    def test_keeps_a_verified_download_and_skips_it_next_time(self):
        self.assertTrue(fetch(self.source.as_uri(), self.target, self.digest))
        self.assertEqual(self.target.read_bytes(), b'weights')
        self.assertFalse(fetch(self.source.as_uri(), self.target, self.digest))

    def test_discards_a_download_with_another_digest(self):
        with self.assertRaises(ValueError):
            fetch(self.source.as_uri(), self.target, '0' * 64)
        self.assertEqual(list(self.folder.iterdir()), [self.source])


class CandidateTests(unittest.TestCase):
    def test_every_downloaded_model_is_pinned_by_digest_and_config(self):
        self.assertEqual(len({candidate.id for candidate in CANDIDATES}), len(CANDIDATES))
        for candidate in CANDIDATES:
            if candidate is BASELINE:
                continue
            self.assertRegex(candidate.weights.sha256, re.compile('^[0-9a-f]{64}$'))
            self.assertTrue(candidate.config.startswith('configs/'))
            self.assertIn(candidate.model_type, ('bs_roformer', 'mel_band_roformer'))

    def test_license_status_names_its_source(self):
        for candidate in CANDIDATES:
            self.assertTrue(candidate.license_source)


if __name__ == '__main__':
    unittest.main()
