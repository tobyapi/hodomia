import sys
import unittest
from importlib.util import find_spec
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from engines import SECTION_LABELS


class SectionLabelTests(unittest.TestCase):
    @unittest.skipUnless(find_spec('allin1_infer'), 'All-In-One is installed only in the analysis runtime')
    def test_every_all_in_one_label_is_shown_in_japanese(self):
        from allin1_infer.config import HARMONIX_LABELS
        self.assertEqual(set(SECTION_LABELS), set(HARMONIX_LABELS))
        self.assertTrue(all(label != name for name, label in SECTION_LABELS.items()))
