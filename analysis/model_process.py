"""Run one offline model subprocess with its output logged, stopping it on cancel or timeout."""
import os
import subprocess
import time
from pathlib import Path


def run_logged(command, log_path, check_cancel, limit_seconds, timeout_message):
    """Return the exit code. The process never outlives this call, even when check_cancel raises."""
    started = time.monotonic()
    with Path(log_path).open('w', encoding='utf-8') as log:
        with subprocess.Popen(command, stdout=log, stderr=subprocess.STDOUT,
                              env={**os.environ, 'PYTHONUTF8': '1'},
                              creationflags=subprocess.CREATE_NO_WINDOW if os.name == 'nt' else 0) as process:
            try:
                while process.poll() is None:
                    check_cancel()
                    if time.monotonic() - started > limit_seconds:
                        raise TimeoutError(timeout_message)
                    time.sleep(.2)
            except BaseException:
                process.kill()
                process.wait()
                raise
            return process.returncode
