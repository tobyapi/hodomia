"""Atomic JSON files with Windows sharing retries."""
import json
import os
import time
import uuid
from pathlib import Path


def write_json(path, value):
    path = Path(path)
    temporary = path.with_name(path.name + '.' + uuid.uuid4().hex + '.tmp')
    try:
        temporary.write_text(json.dumps(value, ensure_ascii=False, allow_nan=False, indent=2), encoding='utf-8')
        # Windows readers briefly hold the destination without FILE_SHARE_DELETE.
        for attempt in range(6):
            try:
                os.replace(temporary, path)
                break
            except PermissionError as error:
                if getattr(error, 'winerror', None) not in (5, 32, 33) or attempt == 5:
                    raise
                time.sleep(.02 * (attempt + 1))
    finally:
        temporary.unlink(missing_ok=True)


def read_json(path):
    return json.loads(Path(path).read_text(encoding='utf-8-sig'))

