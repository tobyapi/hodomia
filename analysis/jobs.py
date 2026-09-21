"""Durable, detached analysis jobs shared by GUI, CLI and MCP adapters."""
import os
import re
import subprocess
import sys
import time
import traceback
import uuid
from pathlib import Path
from control_errors import BusyError, ControlError
from locking import file_lock
from process_identity import process_identity
from storage import manifest, read_json, write_json

ACTIVE = ('queued', 'running', 'cancelling')


def abandoned(value):
    return value['state'] in ACTIVE and (
        (value.get('pid') and process_identity(value['pid']) != value.get('processIdentity')) or
        (not value.get('pid') and time.time() - value['createdAt'] > 60))


class Jobs:
    def __init__(self, runtime):
        self.runtime = Path(runtime).resolve()
        self.home = self.runtime / 'control'
        self.folder = self.home / 'jobs'
        self.folder.mkdir(parents=True, exist_ok=True)

    def path(self, job_id):
        if not isinstance(job_id, str) or not re.fullmatch('[a-f0-9]{32}', job_id):
            raise ControlError('INVALID_ARGUMENT', 'jobIdが不正です。')
        return self.folder / (job_id + '.json')

    def cancel_path(self, job_id):
        return self.path(job_id).with_suffix('.cancel')

    def get(self, job_id, include_log=False):
        path = self.path(job_id)
        if not path.is_file():
            raise ControlError('NOT_FOUND', 'ジョブがありません。')
        value = read_json(path)
        if abandoned(value):
            with file_lock(path.with_suffix('.lock')):
                value = read_json(path)
                if abandoned(value):
                    value.update(state='interrupted', finishedAt=time.time(), error='解析プロセスが終了しました。再解析できます。')
                    write_json(path, value)
        public = {key: value.get(key) for key in ('jobId', 'root', 'state', 'createdAt', 'startedAt', 'finishedAt', 'runId', 'error')}
        public.update(running=value['state'] in ACTIVE, kind='analysis', success=value['state'] == 'complete' if value['state'] not in ACTIVE else None)
        public['cancelRequested'] = self.cancel_path(job_id).exists()
        if public['running'] and public['cancelRequested']:
            public['state'] = 'cancelling'
        try:
            if value.get('runId'):
                public['progress'] = read_json(Path(value['root']) / 'runs' / value['runId'] / 'status.json')
        except (OSError, ValueError):
            pass
        if include_log:
            log = self.folder / (job_id + '.log')
            if log.exists():
                with log.open('rb') as stream:
                    stream.seek(max(0, log.stat().st_size - 12000))
                    public['log'] = stream.read(12000).decode('utf-8', errors='replace')[-3000:]
            else:
                public['log'] = ''
        return public

    def latest(self, include_log=False):
        latest = self.home / 'latest.json'
        return self.get(read_json(latest)['jobId'], include_log) if latest.is_file() else {'running': False, 'kind': None, 'log': ''}

    def start(self, root, options):
        root = Path(root).resolve()
        project = manifest(root)
        from analysis_options import validate_options
        validate_options(options, project['duration'])
        if not (self.runtime / 'ready.json').is_file():
            raise ControlError('MODEL_NOT_READY', '解析環境をセットアップしてください。')
        if options.get('scope') != 'vocal-events' and not options.get('region') and not (self.runtime / 'chordmini/installation.json').is_file():
            raise ControlError('MODEL_NOT_READY', 'BTCモデルをセットアップしてください。')
        with file_lock(self.home / 'coordinator.lock'):
            if self.latest()['running']:
                raise BusyError()
            # Check direct CLI/other-runtime analysis too; the worker acquires these again.
            with file_lock(self.home / 'analysis.lock'), file_lock(root / '.analysis.lock'):
                pass
            job_id = uuid.uuid4().hex
            value = dict(jobId=job_id, root=str(root), options=options, previousRun=project.get('currentRun'),
                         state='queued', createdAt=time.time())
            write_json(self.path(job_id), value)
            write_json(self.home / 'latest.json', {'jobId': job_id})
            try:
                with (self.folder / (job_id + '.log')).open('wb') as log:
                    process = subprocess.Popen(
                        [sys.executable, str(Path(__file__).with_name('job_worker.py')), '--runtime', str(self.runtime), '--job', job_id],
                        stdin=subprocess.DEVNULL, stdout=log, stderr=log,
                        env={**os.environ, 'PYTHONUTF8': '1', 'HF_HUB_OFFLINE': '1', 'TRANSFORMERS_OFFLINE': '1'},
                        creationflags=(subprocess.CREATE_NO_WINDOW | subprocess.CREATE_NEW_PROCESS_GROUP) if os.name == 'nt' else 0,
                        start_new_session=os.name != 'nt')
                    # The worker records its own PID/creation identity, avoiding parent/child write races.
                    if os.name == 'nt':
                        process._handle.Close()
                        process._child_created = False
            except Exception:
                value.update(state='failed', error='ワーカーを起動できませんでした。', finishedAt=time.time())
                write_json(self.path(job_id), value)
                raise
        return {'jobId': job_id, 'state': 'queued', 'root': str(root)}

    def cancel(self, job_id):
        value = self.get(job_id)
        if value['running']:
            self.cancel_path(job_id).touch()
        return self.get(job_id)

    def run(self, job_id):
        path = self.path(job_id)
        with file_lock(path.with_suffix('.lock')):
            value = read_json(path)
            if value['state'] != 'queued':
                raise BusyError()
            value.update(state='running', pid=os.getpid(), processIdentity=process_identity(os.getpid()), startedAt=time.time())
            write_json(path, value)
        try:
            if self.cancel_path(job_id).exists():
                value['state'] = 'cancelled'
            else:
                from pipeline import run
                def record_run(run_id):
                    value['runId'] = run_id
                    with file_lock(path.with_suffix('.lock')):
                        write_json(path, value)
                run(value['root'], self.runtime, value['options'], cancel_path=self.cancel_path(job_id), on_run=record_run)
                status = read_json(Path(value['root']) / 'runs' / value['runId'] / 'status.json')
                value['state'] = status['state']
        except Exception as error:
            traceback.print_exc()
            value.update(state='failed', error=str(error))
        finally:
            value['finishedAt'] = time.time()
            with file_lock(path.with_suffix('.lock')):
                write_json(path, value)
