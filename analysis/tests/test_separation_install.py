import hashlib
import sys
import tempfile
import unittest
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from separation_install import fetch


class FetchTests(unittest.TestCase):
    def setUp(self):
        self.work = tempfile.TemporaryDirectory()
        self.folder = Path(self.work.name)
        self.source = self.folder / 'source.ckpt'
        self.source.write_bytes(b'weights')
        self.target = self.folder / 'weights/target.ckpt'

    def tearDown(self):
        self.work.cleanup()

    def test_keeps_only_a_download_with_the_pinned_digest(self):
        fetch(self.source.as_uri(), self.target, hashlib.sha256(b'weights').hexdigest())
        self.assertEqual(self.target.read_bytes(), b'weights')

    def test_discards_a_download_with_another_digest(self):
        with self.assertRaisesRegex(RuntimeError, 'SHA-256'):
            fetch(self.source.as_uri(), self.target, '0' * 64)
        self.assertEqual(list(self.target.parent.iterdir()), [])


if __name__ == '__main__':
    unittest.main()
