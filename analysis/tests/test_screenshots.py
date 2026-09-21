import base64
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from control import Control
from control_errors import ControlError
from screenshots import capture
from storage import write_json


class ScreenshotTests(unittest.TestCase):
    def test_capture_returns_png_and_removes_queue_files(self):
        with tempfile.TemporaryDirectory() as folder:
            def desktop_response(_seconds):
                request = next(Path(folder).glob('control/screenshots/*.request.json'))
                prefix = request.name.removesuffix('.request.json')
                (request.parent / (prefix + '.png')).write_bytes(b'\x89PNG\r\n\x1a\nexample')
                write_json(request.parent / (prefix + '.response.json'), dict(ok=True, width=40, height=20))
            with patch('screenshots.time.sleep', side_effect=desktop_response):
                value = Control(folder).dispatch('capture_app', {})
            self.assertEqual(value['mimeType'], 'image/png')
            self.assertTrue(base64.b64decode(value['blob']).startswith(b'\x89PNG'))
            self.assertTrue(Path(value['path']).is_file())
            self.assertEqual(list(Path(folder).rglob('*.json')), [])

    def test_unavailable_gui_times_out_without_leaving_request(self):
        with tempfile.TemporaryDirectory() as folder:
            with patch('screenshots.time.monotonic', side_effect=[0, 2]):
                with self.assertRaises(ControlError) as error:
                    capture(folder, 1)
            self.assertEqual(error.exception.code, 'GUI_TIMEOUT')
            self.assertEqual(list(Path(folder).rglob('*.request.json')), [])

    def test_capture_failure_propagates(self):
        with tempfile.TemporaryDirectory() as folder:
            def desktop_response(_seconds):
                request = next(Path(folder).glob('control/screenshots/*.request.json'))
                response = request.with_name(request.name.replace('.request.', '.response.'))
                write_json(response, dict(ok=False, message='minimized'))
            with patch('screenshots.time.sleep', side_effect=desktop_response):
                with self.assertRaises(ControlError) as error:
                    capture(folder)
            self.assertEqual(error.exception.code, 'CAPTURE_FAILED')

    def test_rejects_invalid_timeout_and_arbitrary_target(self):
        with tempfile.TemporaryDirectory() as folder:
            for value in [0, 31, True, '10', float('nan')]:
                with self.assertRaises(ValueError):
                    capture(folder, value)
            with self.assertRaises(TypeError):
                Control(folder).dispatch('capture_app', {'path': '../outside.png'})
