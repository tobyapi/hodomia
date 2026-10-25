import sys
import unittest
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from agreement import activity_overlap, boundaries, boundary_f, character_error_rate, label_agreement
from downstream_report import against


def section(start, end, label):
    return dict(start=start, end=end, label=label)


class BoundaryTests(unittest.TestCase):
    def test_song_edges_are_not_boundaries(self):
        sections = [section(0, 10, 'intro'), section(10, 30, 'verse'), section(30, 40, 'outro')]
        self.assertEqual(boundaries(sections, 40), [10, 30])

    def test_each_reference_boundary_counts_once(self):
        self.assertEqual(boundary_f([10, 30], [10.2, 10.3, 29], .5), 2 * 1 / 5)
        self.assertEqual(boundary_f([10, 30], [10.2, 10.3, 29], 3), 2 * 2 / 5)

    def test_no_boundaries_on_both_sides_agree(self):
        self.assertEqual(boundary_f([], [], .5), 1.0)
        self.assertEqual(boundary_f([10], [], .5), 0.0)


class LabelTests(unittest.TestCase):
    def test_share_of_time_with_the_same_label(self):
        reference = [section(0, 5, 'verse'), section(5, 10, 'chorus')]
        estimate = [section(0, 7.5, 'verse'), section(7.5, 10, 'chorus')]
        self.assertAlmostEqual(label_agreement(reference, estimate, 10), .75)


class TextTests(unittest.TestCase):
    def test_character_error_rate_counts_edits_per_reference_character(self):
        self.assertEqual(character_error_rate('あいうえ', 'あいえお'), .5)
        self.assertEqual(character_error_rate('abc', 'abc'), 0)
        self.assertIsNone(character_error_rate('', 'abc'))


class ActivityTests(unittest.TestCase):
    def test_overlap_is_intersection_over_union(self):
        reference = [dict(start=0, end=4), dict(start=6, end=8)]
        estimate = [dict(start=2, end=7)]
        self.assertAlmostEqual(activity_overlap(reference, estimate), 3 / 8)

    def test_silent_stems_on_both_sides_agree(self):
        self.assertEqual(activity_overlap([], []), 1.0)


class AgainstTests(unittest.TestCase):
    def test_a_vocal_only_model_is_compared_on_lyrics_alone(self):
        lyrics = dict(text='あいうえ', lines=2, untimedLines=0, noSpeechLines=0, meanAvgLogprob=-.3)
        baseline = dict(id='htdemucs_ft', lyrics=lyrics, sections=[section(0, 10, 'verse')],
                        activity={name: [] for name in ('bass', 'drums', 'other', 'vocals')})
        row = against(baseline, dict(id='mel_roformer_kim', lyrics=dict(lyrics, text='あいえお')), 10)
        self.assertEqual(row['lyricsCer'], .5)
        self.assertNotIn('boundaryF05', row)


if __name__ == '__main__':
    unittest.main()
