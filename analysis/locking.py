"""Non-blocking, process-wide file locks released by the OS on process exit."""
import os
from contextlib import contextmanager
from functools import wraps
from pathlib import Path
from control_errors import BusyError


@contextmanager
def file_lock(path):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open('a+b') as stream:
        stream.seek(0, os.SEEK_END)
        if stream.tell() == 0:
            stream.write(b'0')
            stream.flush()
        stream.seek(0)
        try:
            if os.name == 'nt':
                import msvcrt
                msvcrt.locking(stream.fileno(), msvcrt.LK_NBLCK, 1)
            else:
                import fcntl
                fcntl.flock(stream.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
        except OSError as error:
            raise BusyError() from error
        try:
            yield
        finally:
            stream.seek(0)
            if os.name == 'nt':
                msvcrt.locking(stream.fileno(), msvcrt.LK_UNLCK, 1)
            else:
                fcntl.flock(stream.fileno(), fcntl.LOCK_UN)


def project_mutation(function):
    @wraps(function)
    def guarded(root, *args, **kwargs):
        with file_lock(Path(root) / '.write.lock'):
            return function(root, *args, **kwargs)
    return guarded


def analysis_operation(function):
    @wraps(function)
    def guarded(root, runtime, *args, **kwargs):
        with file_lock(Path(runtime) / 'control/analysis.lock'), file_lock(Path(root) / '.analysis.lock'):
            return function(root, runtime, *args, **kwargs)
    return guarded
