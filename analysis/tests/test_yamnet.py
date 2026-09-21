import copy
import sys
import unittest
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from vocal_comparison import intervals, variant
from vocal_labels import CLASSES
from yamnet import validate_frames
from analysis_options import validate_options


def frames(scores):
    return [{'start': i * .48, 'end': i * .48 + .975,
             'scores': {category: score for category in CLASSES},
             'classScores': {name: score for names in CLASSES.values() for name in names}}
            for i, score in enumerate(scores)]


class YamnetTests(unittest.TestCase):
    def test_hysteresis_keeps_weak_continuation_but_not_weak_start(self):
        value = frames([.12, .4, .12, .02, .12, .12])
        spans = intervals(value, 'breath', .15, .1)
        self.assertEqual(spans, [{'start': .48, 'end': 1.935, 'score': .4}])
        self.assertEqual(intervals(frames([0., 0.]), 'breath', .15, .1), [])
        with self.assertRaises(ValueError):
            intervals(value, 'breath', .1, .2)

    def test_short_events_and_coincident_categories_remain_unreviewed(self):
        value = frames([.7])
        value[0]['end'] = .2
        result = variant('yamnet', 'vocals', value, .975, .48, .15, .1)
        self.assertEqual(len(result['candidates']), 3)
        self.assertTrue(all(r['start'] == 0 and r['end'] == .2 and not r['reviewed'] for r in result['candidates']))
        self.assertEqual(len({r['id'] for r in result['candidates']}), 3)

    def test_model_output_rejects_nan_missing_source_class_and_window(self):
        value = frames([.1, .2, .3])
        duration = value[-1]['end']
        validate_frames({'original': value}, duration, ['original'])
        for mutation in ('nan', 'class', 'window', 'coverage'):
            bad = copy.deepcopy(value)
            if mutation == 'nan': bad[0]['scores']['breath'] = float('nan')
            if mutation == 'class': del bad[0]['classScores']['Humming']
            if mutation == 'window': bad.pop(1)
            if mutation == 'coverage': bad.pop()
            with self.assertRaises(ValueError):
                validate_frames({'original': bad}, duration, ['original'])
        with self.assertRaises(ValueError):
            validate_frames({'original': value}, duration, ['original', 'vocals'])

    def test_comparison_scope_cannot_be_combined_with_lyrics_region(self):
        validate_options({'mode': 'japanese', 'scope': 'vocal-comparison'}, 60)
        with self.assertRaises(ValueError):
            validate_options({'mode': 'japanese', 'scope': 'vocal-comparison', 'region': {'start': 0, 'end': 5, 'language': 'ja'}}, 60)
