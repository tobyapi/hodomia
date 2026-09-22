import unittest
from unittest.mock import Mock, patch
from worker_cleanup import remove_worker_log


def sharing_violation():
    error = PermissionError('worker log is still open')
    error.winerror = 32
    return error


class WorkerCleanupTests(unittest.TestCase):
    def test_retries_until_the_worker_log_handle_is_released(self):
        log = Mock()
        log.unlink.side_effect = [sharing_violation(), sharing_violation(), None]
        with patch('worker_cleanup.time.monotonic', return_value=0):
            with patch('worker_cleanup.time.sleep') as sleep:
                remove_worker_log(log)
        self.assertEqual(log.unlink.call_count, 3)
        log.unlink.assert_called_with(missing_ok=True)
        self.assertEqual(sleep.call_count, 2)

    def test_permanent_access_denial_is_not_retried(self):
        error = PermissionError('access denied')
        error.winerror = 5
        log = Mock()
        log.unlink.side_effect = error
        with patch('worker_cleanup.time.sleep') as sleep:
            with self.assertRaises(PermissionError) as raised:
                remove_worker_log(log)
        self.assertIs(raised.exception, error)
        log.unlink.assert_called_once_with(missing_ok=True)
        sleep.assert_not_called()

    def test_unreleased_handle_stops_at_the_deadline(self):
        error = sharing_violation()
        log = Mock()
        log.unlink.side_effect = error
        with patch('worker_cleanup.time.monotonic', side_effect=[0, 0, 15]):
            with patch('worker_cleanup.time.sleep') as sleep:
                with self.assertRaises(PermissionError) as raised:
                    remove_worker_log(log)
        self.assertIs(raised.exception, error)
        self.assertEqual(log.unlink.call_count, 2)
        sleep.assert_called_once_with(.05)
