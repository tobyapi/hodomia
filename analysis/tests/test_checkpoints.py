import json
import sys
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from checkpoints import Checkpoint


class CheckpointTimingTests(unittest.TestCase):
    def test_failed_stage_keeps_its_error_and_seconds(self):
        def fail():
            raise RuntimeError('broken')
        with tempfile.TemporaryDirectory() as directory, \
             patch.dict(sys.modules, {'engines': SimpleNamespace(release=lambda: None)}):
            folder = Path(directory)
            Checkpoint(folder, folder, {}, None).attempt('拍・BPM', .42, fail)
            status = json.loads((folder / 'status.json').read_text(encoding='utf-8'))
        self.assertEqual(status['errors'], [{'stage': '拍・BPM', 'message': 'broken'}])
        self.assertEqual([t['stage'] for t in status['timings']], ['拍・BPM'])
        self.assertGreaterEqual(status['timings'][0]['seconds'], 0)
