"""Creation and publication of recoverable analysis runs."""
import copy
import sys
import time
import traceback
import uuid
from datetime import datetime, timezone
from pathlib import Path
from locking import file_lock
from storage import within, write_json, read_json


class Cancelled(Exception):
    pass


def create_run(root, project, options, on_run):
    with file_lock(root / '.write.lock'):
        run_id = datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S') + '-' + uuid.uuid4().hex[:8]
        folder = root / 'runs' / run_id
        folder.mkdir(parents=True)
        write_json(folder / 'request.json', options)
        previous = None
        if project.get('currentRun'):
            previous_file = within(root, 'runs/' + project['currentRun'] + '/result.json')
            if previous_file.exists():
                previous = read_json(previous_file)
        project['currentRun'] = run_id
        write_json(root / 'project.json', project)
        partial = options.get('region') or options.get('scope') in ('vocal-events', 'harmony')
        result = copy.deepcopy(previous) if partial and previous else {'tracks': {}, 'series': {}, 'stems': {}, 'engines': {}}
        result['runId'] = run_id
        if options.get('scope') not in ('vocal-events', 'harmony') or 'mode' not in result:
            result['mode'] = options['mode']
        result['sourceHash'] = project['source']['sha256']
        if on_run is not None:
            on_run(run_id)
    return run_id, folder, previous, result


class Checkpoint:
    def __init__(self, root, folder, result, cancel_path):
        self.root, self.folder, self.result = root, folder, result
        self.cancel_path = cancel_path
        self.started, self.errors = time.monotonic(), []
        self.status = {'state': 'running', 'stage': '準備', 'progress': 0, 'errors': self.errors}

    def cancelled(self):
        return (self.root / 'cancel.flag').exists() or (self.cancel_path is not None and Path(self.cancel_path).exists())

    def publish(self, stage, progress, state='running'):
        if self.cancelled():
            raise Cancelled()
        self.status.update(state=state, stage=stage, progress=progress, elapsed=time.monotonic() - self.started)
        self.persist()
        print(stage, flush=True, file=sys.stderr)

    def persist(self):
        write_json(self.folder / 'result.json', self.result)
        write_json(self.folder / 'status.json', self.status)

    def attempt(self, stage, progress, action):
        self.publish(stage, progress)
        try:
            action()
        except Cancelled:
            raise
        except Exception as error:
            self.errors.append({'stage': stage, 'message': str(error)})
            traceback.print_exc()
        finally:
            from engines import release
            release()
        self.publish(stage, progress)

    def finish_error(self, error=None):
        if error is not None:
            self.errors.append({'stage': self.status['stage'], 'message': str(error)})
        self.status.update(state='failed' if error else 'cancelled',
                           stage='解析に失敗しました' if error else '中止しました',
                           elapsed=time.monotonic() - self.started)
        self.persist()
