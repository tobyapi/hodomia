import hashlib
import re
import sys
import tempfile
import unittest
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from candidates import BASELINE, CANDIDATES, COMBINATIONS, STEMS, Download, by_id
from installation import config_path, downloads
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
            for download in downloads(candidate):
                self.assertRegex(download.sha256, re.compile('^[0-9a-f]{64}$'))
            if not isinstance(candidate.config, Download):
                self.assertTrue(candidate.config.startswith('configs/'))
            self.assertIn(candidate.model_type, ('bs_roformer', 'mel_band_roformer', 'scnet'))

    def test_release_configs_are_read_from_the_download_folder(self):
        home = Path('runtime')
        released = by_id('bs_roformer_zfturbo_4stem')
        checkout = by_id('mel_roformer_kim')
        self.assertEqual(config_path(home, released), home / 'weights' / released.config.filename)
        self.assertEqual(config_path(home, checkout), home / 'msst' / checkout.config)
        self.assertEqual(downloads(checkout), [checkout.weights])

    def test_license_status_names_its_source(self):
        for candidate in CANDIDATES:
            self.assertTrue(candidate.license_source)

    def test_outputs_map_to_the_stems_analysis_reads(self):
        for candidate in CANDIDATES:
            names = [stem for stem, _ in candidate.stems]
            self.assertIn('vocals', names)
            self.assertLessEqual(set(names), set(STEMS))
            self.assertEqual(len(names), len(set(names)))

    def test_combinations_take_drums_and_bass_from_a_multi_stem_model(self):
        for combination in COMBINATIONS:
            self.assertEqual([stem for stem, _ in by_id(combination.vocals).stems], ['vocals'])
            self.assertLessEqual({'drums', 'bass'}, {stem for stem, _ in by_id(combination.rhythm).stems})


if __name__ == '__main__':
    unittest.main()
