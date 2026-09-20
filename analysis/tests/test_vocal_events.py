import sys
import unittest
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from vocal_events import candidates, EVENTS


def frame(time, **scores):
    return {'time': time, 'events': {category: {'score': scores.get(category, 0.), 'source': 'vocals',
                                               'class': names[0]} for category, (_, names) in EVENTS.items()}}


class VocalEventTests(unittest.TestCase):
    def test_rap_and_narration_overlap_without_becoming_lyrics(self):
        rows = candidates([frame(2, rap=.7, spoken=.6, beatbox=.4), frame(2.5)], 5)
        self.assertEqual({r['category'] for r in rows}, {'rap', 'spoken', 'beatbox'})
        self.assertTrue(all(not r['reviewed'] for r in rows))
        self.assertEqual(next(r for r in rows if r['category'] == 'spoken')['evidenceLabels'], ['Narration, monologue'])

    def test_no_positive_evidence_does_not_invent_events(self):
        self.assertEqual(candidates([frame(0), frame(.5)], 1), [])

    def test_coincident_categories_survive_and_intervals_are_bounded(self):
        rows = candidates([frame(0, beatbox=.8, breath=.5), frame(.5, beatbox=.7), frame(1)], 1.2)
        self.assertEqual({r['category'] for r in rows}, {'beatbox', 'breath'})
        self.assertEqual(len({r['id'] for r in rows}), 2)
        self.assertTrue(all(0 <= r['start'] < r['end'] <= 1.2 for r in rows))
        self.assertTrue(all(not r['reviewed'] for r in rows))
        self.assertEqual(rows[0]['start'], 0)

    def test_context_windows_merge_only_overlapping_same_categories(self):
        rows = candidates([frame(0, beatbox=.5), frame(.5), frame(1, beatbox=.7), frame(1.5),
                           frame(5, beatbox=.6), frame(5.5)], 6)
        self.assertEqual([(r['start'], r['end']) for r in rows], [(0., 2.), (4., 6.)])
        self.assertEqual(rows[0]['score'], .7)

    def test_sensitive_mode_adds_weak_candidates_without_promoting_to_reviewed(self):
        frames = [frame(1, humming=.1)]
        self.assertEqual(candidates(frames, 3), [])
        rows = candidates(frames, 3, 'sensitive')
        self.assertEqual(rows[0]['category'], 'humming')
        self.assertFalse(rows[0]['reviewed'])
        self.assertEqual(rows[0]['detectedCategory'], 'humming')


if __name__ == '__main__':
    unittest.main()
