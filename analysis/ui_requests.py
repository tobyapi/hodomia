"""Durable requests to display a song in an existing or subsequently opened GUI."""
import re
import time
import uuid
from pathlib import Path
from control_errors import ControlError
from locking import file_lock
from storage import snapshot, read_json, write_json, TRACKS
from timeline_api import time_range


class UiRequests:
    def __init__(self, runtime):
        self.folder = Path(runtime) / 'control' / 'ui'
        self.folder.mkdir(parents=True, exist_ok=True)

    def path(self, request_id):
        if not isinstance(request_id, str) or not re.fullmatch('[a-f0-9]{32}', request_id):
            raise ValueError('requestIdが不正です。')
        return self.folder / (request_id + '.json')

    def get(self, request_id):
        path = self.path(request_id)
        if not path.is_file():
            raise ControlError('NOT_FOUND', '表示リクエストがありません。')
        value = read_json(path)
        if value['state'] == 'queued' and time.time() > value['expiresAt']:
            value['state'] = 'expired'
        return value

    def enqueue(self, root, start=0, end=None, stem='original', track='chords'):
        value = snapshot(root)
        start, end = time_range(start, end, value['project']['duration'])
        if track not in TRACKS or (stem != 'original' and stem not in value['result'].get('stems', {})):
            raise ValueError('トラックまたは音声が不正です。')
        request_id = uuid.uuid4().hex
        request = dict(requestId=request_id, root=str(Path(root).resolve()), start=start, end=end,
                       stem=stem, track=track, state='queued', createdAt=time.time(), expiresAt=time.time() + 600)
        write_json(self.path(request_id), request)
        return request

    def next(self):
        pending = [self.get(path.stem) for path in self.folder.glob('*.json')]
        pending = [item for item in pending if item['state'] == 'queued']
        return min(pending, key=lambda item: item['createdAt']) if pending else None

    def acknowledge(self, request_id, state, message=None):
        if state not in ('applied', 'failed'):
            raise ValueError('表示状態が不正です。')
        with file_lock(self.folder / 'queue.lock'):
            value = self.get(request_id)
            if value['state'] == 'queued':
                value.update(state=state, message=message, finishedAt=time.time())
                write_json(self.path(request_id), value)
            return value
