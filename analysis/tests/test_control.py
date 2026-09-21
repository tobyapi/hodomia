import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import time
import unittest
from unittest.mock import patch
import wave
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from control import Control
from control_errors import BusyError, ConflictError, ControlError
from locking import file_lock
from process_identity import process_identity
from storage import save_edits, snapshot, write_json


class ControlTests(unittest.TestCase):
    def test_removed_comparison_scopes_are_rejected_before_job_creation(self):
        from analysis_options import validate_options
        for scope in ('vocal-comparison', 'separation-comparison'):
            with self.assertRaises(ValueError):
                validate_options({'mode': 'japanese', 'scope': scope}, 60)
        validate_options({'mode': 'japanese', 'scope': 'vocal-events'}, 60)

    def setUp(self):
        self.worker_jobs = []
        self.temp = tempfile.TemporaryDirectory()
        self.home = Path(self.temp.name)
        self.runtime = self.home / 'runtime'
        self.projects = self.home / 'projects'
        self.source = self.home / 'input.wav'
        with wave.open(str(self.source), 'wb') as stream:
            stream.setparams((1, 2, 16000, 0, 'NONE', 'not compressed'))
            stream.writeframes(b'\0\0' * 16000)
        self.service = Control(self.runtime, self.projects, self.home / 'registry', [self.home])
        self.root = Path(self.service.dispatch('import_audio', {'source': str(self.source)})['root'])

    def tearDown(self):
        for job_id in self.worker_jobs:
            self.wait_for_worker_exit(job_id)
        self.temp.cleanup()

    def wait_for_worker_exit(self, job_id):
        # A terminal job state is written before the worker closes its log.
        deadline = time.monotonic() + 15
        while time.monotonic() < deadline:
            job = json.loads(self.service.jobs.path(job_id).read_text(encoding='utf-8'))
            if job.get('pid'):
                if process_identity(job['pid']) != job.get('processIdentity'):
                    return
            elif job['state'] == 'failed':
                return
            time.sleep(.05)
        self.fail(f'Worker did not exit before cleanup: {job_id}')

    def test_summary_and_library_do_not_return_full_arrays(self):
        summary = self.service.dispatch('get_project', {'root': str(self.root)})
        self.assertNotIn('series', summary)
        self.assertEqual(summary['revision'], 0)
        self.assertEqual(self.service.dispatch('list_projects', {})['projects'][0]['root'], str(self.root))

    def test_cleanup_waits_for_worker_exit_after_terminal_state(self):
        job_id = 'c' * 32
        write_json(self.service.jobs.path(job_id), dict(
            state='failed', pid=123, processIdentity='worker'))
        with patch('test_control.process_identity', side_effect=['worker', 'worker', None]) as identity:
            with patch('test_control.time.sleep') as sleep:
                self.wait_for_worker_exit(job_id)
        self.assertEqual(identity.call_count, 3)
        self.assertEqual(sleep.call_count, 2)

    def test_scope_rejects_unapproved_input(self):
        restricted = Control(self.runtime, self.projects, self.home / 'empty-registry')
        with self.assertRaisesRegex(ControlError, '--allow-root'):
            restricted.dispatch('import_audio', {'source': str(self.source)})

    def test_save_compare_and_swap_and_process_lock(self):
        before = snapshot(self.root)['edits']
        with file_lock(self.root / '.write.lock'), self.assertRaises(BusyError):
            save_edits(self.root, before)
        save_edits(self.root, before)
        with self.assertRaises(ConflictError):
            save_edits(self.root, before)
        code = 'from locking import file_lock; import sys;\nwith file_lock(sys.argv[1]): print("acquired")'
        with file_lock(self.root / '.write.lock'):
            process = subprocess.run([sys.executable, '-c', code, str(self.root / '.write.lock')],
                                     env={**os.environ, 'PYTHONPATH': str(Path(__file__).resolve().parents[1])}, capture_output=True)
        self.assertNotEqual(process.returncode, 0)

    def test_dead_pid_is_interrupted_and_cancel_does_not_touch_project_flag(self):
        job_id = 'a' * 32
        write_json(self.service.jobs.path(job_id), dict(jobId=job_id, root=str(self.root), state='running',
                   previousRun=None, createdAt=time.time(), pid=os.getpid(), processIdentity='different-process'))
        self.assertEqual(self.service.jobs.get(job_id)['state'], 'interrupted')
        self.assertIsNotNone(process_identity(os.getpid()))
        queued = 'b' * 32
        write_json(self.service.jobs.path(queued), dict(jobId=queued, root=str(self.root), state='queued', previousRun=None, createdAt=time.time()))
        self.assertEqual(self.service.jobs.cancel(queued)['state'], 'cancelling')
        self.assertFalse((self.root / 'cancel.flag').exists())

    def test_cli_has_one_json_response_and_stable_error(self):
        command = [sys.executable, str(Path(__file__).resolve().parents[1] / 'headless.py'),
                   '--runtime', str(self.runtime), '--projects', str(self.projects), '--registry', str(self.home / 'registry')]
        for operation, ok in [('list_projects', True), ('unknown', False)]:
            result = subprocess.run(command, input=json.dumps({'operation': operation}), encoding='utf-8', capture_output=True)
            self.assertEqual(len(result.stdout.splitlines()), 1)
            response = json.loads(result.stdout)
            self.assertEqual(response['ok'], ok)
            if not ok:
                self.assertEqual(response['error']['code'], 'UNKNOWN_OPERATION')

    def test_detached_job_reaches_failed_state_without_loading_models(self):
        write_json(self.runtime / 'ready.json', {})
        (self.runtime / 'chordmini').mkdir()
        write_json(self.runtime / 'chordmini/installation.json', {})
        manifest = snapshot(self.root)['project']
        (self.root / manifest['source']['path']).write_bytes(b'changed source')
        job = self.service.dispatch('start_analysis', {'root': str(self.root), 'options': {'mode': 'japanese', 'scope': 'harmony'}})
        self.worker_jobs.append(job['jobId'])
        deadline = time.monotonic() + 15
        while time.monotonic() < deadline:
            state = self.service.dispatch('get_job', {'jobId': job['jobId']})
            if not state['running']:
                break
            time.sleep(.05)
        self.assertEqual(state['state'], 'failed', state)
        self.assertFalse(state['success'])
