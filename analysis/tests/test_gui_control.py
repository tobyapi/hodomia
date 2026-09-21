import os
import subprocess
import sys
import time
import unittest
from pathlib import Path
import test_control as fixtures
from storage import read_json, write_json
from locking import file_lock
from ui_requests import UiRequests
from cli import execute


class GuiControlTests(unittest.TestCase):
    setUp = fixtures.ControlTests.setUp
    tearDown = fixtures.ControlTests.tearDown

    def test_display_queue_validation_acknowledgement_and_expiry(self):
        requests = UiRequests(self.runtime)
        with self.assertRaises(ValueError):
            self.service.dispatch('show_in_app', {'root': str(self.root), 'start': 2})
        item = self.service.dispatch('show_in_app', {'root': str(self.root), 'start': .2, 'end': .8, 'track': 'vocalEvents'})
        self.assertEqual(execute({'operation': 'next_ui_request'}, self.runtime), item)
        execute({'operation': 'ack_ui_request', 'args': {'requestId': item['requestId'], 'state': 'applied'}}, self.runtime)
        self.assertIsNone(requests.next())
        self.assertEqual(self.service.dispatch('get_ui_request', {'requestId': item['requestId']})['state'], 'applied')
        item = requests.enqueue(self.root)
        item['expiresAt'] = time.time() - 1
        write_json(requests.path(item['requestId']), item)
        self.assertEqual(requests.get(item['requestId'])['state'], 'expired')
        self.assertIsNone(requests.next())

    def test_completed_job_keeps_its_run_after_later_analysis(self):
        manifest = read_json(self.root / 'project.json')
        manifest['currentRun'] = 'newer'
        write_json(self.root / 'project.json', manifest)
        for run, stage in [('older', 'first result'), ('newer', 'second result')]:
            (self.root / 'runs' / run).mkdir(parents=True)
            write_json(self.root / 'runs' / run / 'result.json', {'tracks': {}})
            write_json(self.root / 'runs' / run / 'status.json', {'state': 'complete', 'stage': stage})
        job_id = 'e' * 32
        write_json(self.service.jobs.path(job_id), dict(jobId=job_id, root=str(self.root), state='complete', previousRun=None, runId='older', createdAt=time.time()))
        result = self.service.jobs.get(job_id)
        self.assertEqual(result['runId'], 'older')
        self.assertEqual(result['progress']['stage'], 'first result')

    @unittest.skipUnless(os.name == 'nt', 'Windows setup lock interoperability')
    def test_powershell_setup_and_python_analysis_share_the_os_lock(self):
        helper = Path(__file__).resolve().parents[2] / 'scripts/runtime-lock.ps1'
        script = self.home / 'probe.ps1'
        script.write_text("param($Helper, $Runtime)\n$ErrorActionPreference='Stop'\n. $Helper\nInvoke-WithRuntimeLock -RuntimeRoot $Runtime -Action { Write-Output 'acquired' }", encoding='utf-8')
        command = ['powershell', '-NoProfile', '-File', str(script), str(helper), str(self.runtime)]
        with file_lock(self.runtime / 'control/analysis.lock'):
            result = subprocess.run(command, capture_output=True)
        self.assertNotEqual(result.returncode, 0)
        result = subprocess.run(command, capture_output=True)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn(b'acquired', result.stdout)
