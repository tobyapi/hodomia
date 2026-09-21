import unittest
import test_control as fixtures
from test_yamnet import frames
from vocal_comparison import variant
from storage import write_json, read_json
from control_errors import ConflictError, BusyError
from locking import file_lock


class ComparisonApiTests(unittest.TestCase):
    setUp = fixtures.ControlTests.setUp
    tearDown = fixtures.ControlTests.tearDown

    def test_summary_pagination_version_and_analysis_lock(self):
        project = read_json(self.root / 'project.json')
        project['currentRun'] = 'comparison'
        write_json(self.root / 'project.json', project)
        run = self.root / 'runs/comparison'
        run.mkdir(parents=True)
        values = frames([.4, .2])
        for value in values: value['end'] = min(1., value['end'])
        write_json(run / 'result.json', {'tracks': {}, 'vocalComparisons': {
            'runId': 'comparison', 'variants': [variant('yamnet', 'original', values, .975, .48, .15, .1)], 'notice': 'uncalibrated', 'engines': {}}})
        args = {'root': str(self.root)}
        summary = self.service.dispatch('get_vocal_comparison', args)
        self.assertNotIn('frames', summary['variants'][0])
        page = self.service.dispatch('get_vocal_comparison', {**args, 'variantId': 'yamnet-original', 'limit': 1, 'category': 'breath'})
        self.assertEqual(page['nextOffset'], 1)
        self.assertEqual(set(page['rows'][0]['scores']), {'breath'})
        page = self.service.dispatch('get_vocal_comparison', {**args, 'variantId': 'yamnet-original', 'kind': 'candidates', 'category': 'breath'})
        self.assertEqual(len(page['rows']), 1)
        with self.assertRaises(ConflictError):
            self.service.dispatch('get_vocal_comparison', {**args, 'expectedRunId': 'old'})
        with file_lock(self.root / '.analysis.lock'), self.assertRaises(BusyError):
            self.service.dispatch('get_vocal_comparison', args)
        exported = self.service.dispatch('export_project', args)
        self.assertEqual(len(exported['artifacts']), 4)
        csv = self.service.dispatch('read_artifact', {'artifactId': exported['artifacts'][-1]['artifactId']})
        self.assertIn('window_start', csv['text'])
        self.assertIn('yamnet,original', csv['text'])
