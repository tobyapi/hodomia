import tempfile
import unittest
import sys
from pathlib import Path
from unittest.mock import patch
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from storage import write_json, read_json


class AtomicWriteTests(unittest.TestCase):
    def test_transient_windows_reader_retries_without_losing_previous_value(self):
        import os
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp) / 'status.json'
            write_json(path, {'progress': 0})
            replace = os.replace
            error = PermissionError('Windows reader')
            error.winerror = 5
            def sharing_violation(source, target):
                self.assertEqual(read_json(target), {'progress': 0})
                if operation.call_count == 1:
                    raise error
                replace(source, target)
            with patch('json_store.os.replace', side_effect=sharing_violation) as operation, patch('json_store.time.sleep'):
                write_json(path, {'progress': 1})
            self.assertEqual(read_json(path), {'progress': 1})
            self.assertEqual(list(Path(temp).glob('*.tmp')), [])

    def test_permanent_denial_stays_visible_and_preserves_destination(self):
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp) / 'status.json'
            write_json(path, {'progress': 0})
            error = PermissionError('denied')
            error.winerror = 5
            with patch('json_store.os.replace', side_effect=error) as operation, patch('json_store.time.sleep'), self.assertRaises(PermissionError):
                write_json(path, {'progress': 1})
            self.assertEqual(operation.call_count, 6)
            self.assertEqual(read_json(path), {'progress': 0})
            self.assertEqual(list(Path(temp).glob('*.tmp')), [])
