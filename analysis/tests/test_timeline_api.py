import base64
import hashlib
import unittest
from unittest.mock import patch
import test_control as fixtures
from control import Control
from control_errors import BusyError, ConflictError, ControlError
from locking import file_lock
from storage import read_json, row, snapshot, write_json


class TimelineApiTests(unittest.TestCase):
    setUp = fixtures.ControlTests.setUp
    tearDown = fixtures.ControlTests.tearDown

    def seed(self):
        project = snapshot(self.root)['project']
        project['currentRun'] = 'run-1'
        folder = self.root / 'runs/run-1'
        folder.mkdir(parents=True)
        write_json(folder / 'result.json', {'tracks': {
            'chords': [row('c', 0, 0, .5, 'A:min7'), row('c', 1, .5, 1, 'G:7')],
            'words': [row('w', 0, None, None, '未確定')],
            'beats': [row('b', 0, .5, .5, '拍')],
        }})
        write_json(self.root / 'project.json', project)

    def test_range_paging_and_untimed_rows(self):
        self.seed()
        args = dict(root=str(self.root), tracks=['chords', 'beats'], start=.5, end=1, limit=1)
        first = self.service.dispatch('get_timeline', args)
        self.assertEqual(first['total'], 2)
        self.assertEqual(first['rows'][0]['track'], 'beats')
        second = self.service.dispatch('get_timeline', {**args, 'offset': first['nextOffset'], 'expectedRevision': 0, 'expectedRunId': 'run-1'})
        self.assertEqual(second['rows'][0]['label'], 'G:7')
        self.assertIsNone(second['nextOffset'])
        untimed = self.service.dispatch('get_timeline', dict(root=str(self.root), tracks=['words'], includeUntimed=True))
        self.assertIsNone(untimed['rows'][0]['start'])
        with self.assertRaises(ConflictError):
            self.service.dispatch('get_timeline', {**args, 'expectedRevision': 0, 'expectedRunId': 'old-run'})

    def test_segment_patch_dry_run_retry_and_atomic_validation(self):
        self.seed()
        args = dict(root=str(self.root), expectedRevision=0, expectedRunId='run-1', requestId='request-1',
                    operations=[dict(op='update', track='chords', id='c-0', changes={'label': 'C:maj7', 'reviewed': True}),
                                dict(op='add', track='vocalEvents', changes={'start': .1, 'end': .3, 'label': 'ブレス', 'category': 'breath'})])
        before = snapshot(self.root)
        preview = self.service.dispatch('update_segments', {**args, 'dryRun': True})
        self.assertEqual(preview['revision'], 0)
        self.assertEqual(snapshot(self.root), before)
        applied = self.service.dispatch('update_segments', args)
        replay = self.service.dispatch('update_segments', args)
        self.assertTrue(replay['replayed'])
        self.assertEqual(applied['changes'], replay['changes'])
        self.assertEqual(snapshot(self.root)['edits']['revision'], 1)
        self.assertEqual(snapshot(self.root)['result'], before['result'])
        self.assertEqual(snapshot(self.root)['edits']['tracks']['chords'][1]['label'], 'G:7')
        with self.assertRaises(ConflictError):
            self.service.dispatch('update_segments', {**args, 'requestId': 'stale'})
        bad = {**args, 'expectedRevision': 1, 'requestId': 'invalid', 'operations': [dict(op='delete', track='chords', id='c-0'), dict(op='update', track='chords', id='missing', changes={})]}
        with self.assertRaises(ValueError):
            self.service.dispatch('update_segments', bad)
        self.assertEqual(snapshot(self.root)['edits']['revision'], 1)

    def test_retry_after_uncommitted_receipt_and_analysis_lock(self):
        self.seed()
        args = dict(root=str(self.root), expectedRevision=0, expectedRunId='run-1', requestId='retry',
                    operations=[dict(op='delete', track='chords', id='c-0')])
        with patch('storage._save_edits', side_effect=OSError('interrupted')), self.assertRaises(OSError):
            self.service.dispatch('update_segments', args)
        self.assertFalse(self.service.dispatch('update_segments', args)['replayed'])
        with file_lock(self.root / '.analysis.lock'), self.assertRaises(BusyError):
            self.service.dispatch('update_segments', args)

    def test_clip_preserves_source_and_resource_is_scoped(self):
        import soundfile as sf
        audio = self.root / 'audio.wav'
        before = hashlib.sha256(audio.read_bytes()).hexdigest()
        clip = self.service.dispatch('extract_audio_clip', dict(root=str(self.root), start=.25, end=.5))
        info = sf.info(clip['path'])
        self.assertAlmostEqual(info.duration, .25)
        self.assertEqual(hashlib.sha256(audio.read_bytes()).hexdigest(), before)
        resource = self.service.dispatch('read_artifact', {'artifactId': clip['artifact']['artifactId']})
        self.assertEqual(base64.b64decode(resource['blob'])[:4], b'RIFF')
        isolated = Control(self.runtime, self.home / 'other', self.home / 'other-registry')
        with self.assertRaises(ControlError):
            isolated.dispatch('read_artifact', {'artifactId': clip['artifact']['artifactId']})
        with self.assertRaises(ValueError):
            self.service.dispatch('extract_audio_clip', dict(root=str(self.root), start=0, end=1, stem='../../secret'))
