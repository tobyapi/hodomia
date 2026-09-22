"""Remove a test worker's log after Windows releases its inherited handles."""
import time


def remove_worker_log(path):
    deadline = time.monotonic() + 15
    while True:
        try:
            path.unlink(missing_ok=True)
            return
        except PermissionError as error:
            if getattr(error, 'winerror', None) != 32 or time.monotonic() >= deadline:
                raise
        time.sleep(.05)
