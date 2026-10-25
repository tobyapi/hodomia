import sys
import tempfile
import time
import unittest
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from model_process import run_logged


class ProcessTests(unittest.TestCase):
    def setUp(self):
        self.work = tempfile.TemporaryDirectory()
        self.log = Path(self.work.name) / 'run.log'

    def tearDown(self):
        self.work.cleanup()

    def test_exit_code_and_output_reach_the_caller(self):
        code = run_logged([sys.executable, '-c', 'print("ok"); raise SystemExit(3)'], self.log, lambda: None, 30, '')
        self.assertEqual(code, 3)
        self.assertIn('ok', self.log.read_text(encoding='utf-8'))

    def test_cancel_stops_the_process_at_once(self):
        def cancel():
            raise KeyboardInterrupt()
        started = time.monotonic()
        with self.assertRaises(KeyboardInterrupt):
            run_logged([sys.executable, '-c', 'import time; time.sleep(30)'], self.log, cancel, 30, '')
        self.assertLess(time.monotonic() - started, 10)

    def test_a_process_past_its_limit_is_stopped(self):
        with self.assertRaisesRegex(TimeoutError, '時間切れ'):
            run_logged([sys.executable, '-c', 'import time; time.sleep(30)'], self.log, lambda: None, .3, '時間切れ')


if __name__ == '__main__':
    unittest.main()
