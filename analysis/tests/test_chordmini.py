import sys
import tempfile
import unittest
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from chordmini import read_lab
from chordmini_runner import normalization, strict_loader


class ChordMiniTests(unittest.TestCase):
    def read(self, text, duration=2):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / 'chords.lab'
            path.write_text(text, encoding='utf-8')
            return read_lab(path, duration)

    def test_preserves_extended_labels_without_inventing_confidence(self):
        rows = self.read('0 1 A:min7\n1 1.95 G:7\n')
        self.assertEqual([r['label'] for r in rows], ['A:min7', 'G:7'])
        self.assertFalse(rows[0]['reviewed'])
        self.assertNotIn('score', rows[0])
        self.assertNotIn('uncertain', rows[0])
        self.assertEqual(rows[-1]['end'], 1.95)

    def test_rejects_missing_invalid_nonfinite_overlapping_and_gapped_output(self):
        for text in ('', '0 nan C', '-1 2 C', '0 3 C', '0 0 C', '0 1 C\n.5 2 G',
                     '0 .5 C\n1 2 G', '0 1 C', '1 2 C', '0 2 C extra'):
            with self.subTest(text=text), self.assertRaises(ValueError):
                self.read(text)

    def test_checkpoint_mismatch_never_permits_non_strict_retry(self):
        calls = []
        def original(module, state, strict):
            calls.append(strict)
            raise RuntimeError('mismatch')
        guarded = strict_loader(original)
        with self.assertRaisesRegex(RuntimeError, 'mismatch'):
            guarded(None, {})
        with self.assertRaisesRegex(RuntimeError, 'prohibited'):
            guarded(None, {}, strict=False)
        self.assertEqual(calls, [True])

    def test_requires_real_finite_normalization_statistics(self):
        self.assertEqual(normalization({'normalization': {'mean': -2., 'std': 1.9}}), (-2., 1.9))
        for value in ({}, {'mean': 1}, {'mean': 0, 'std': 0}, {'mean': float('nan'), 'std': 1}):
            with self.subTest(value=value), self.assertRaises(ValueError):
                normalization(value)
