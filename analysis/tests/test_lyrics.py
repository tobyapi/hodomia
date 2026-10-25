import sys
import unittest
from pathlib import Path
from types import SimpleNamespace
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from lyrics import line_warning, transcript_rows


def segment(text, no_speech, start=0., end=1.):
    return SimpleNamespace(text=text, start=start, end=end, no_speech_prob=no_speech, avg_logprob=-.13, words=[])


class LineWarningTests(unittest.TestCase):
    def test_text_written_over_non_speech_is_flagged_but_kept(self):
        rows = transcript_rows([segment(' ご視聴ありがとうございました ', .881), segment(' 歌詞 ', .518)])
        self.assertEqual((rows[0]['text'], rows[0]['noSpeechProb'], rows[0]['avgLogprob']), ('ご視聴ありがとうございました', .881, -.13))
        found = [{'start': 0., 'end': 1.}]
        self.assertIn('発話なしの確率0.88', line_warning(rows[0], found, True))
        self.assertEqual(line_warning(rows[1], found, True), '自動推定・要確認')
        # The real hallucination also failed alignment; its null-time line must carry the hint.
        unaligned = line_warning(rows[0], [], True)
        self.assertIn('未確定', unaligned)
        self.assertIn('発話なしの確率0.88', unaligned)

    def test_supplied_lyrics_and_unaligned_lines_keep_their_warnings(self):
        supplied = {'text': '入力した歌詞', 'start': 0., 'end': 1., 'words': []}
        self.assertEqual(line_warning(supplied, [{'start': 0., 'end': 1.}], True), '自動推定・要確認')
        self.assertEqual(line_warning(supplied, [], True), '時刻は未確定。歌詞または探索区間を修正して再解析してください。')
        self.assertIn('ASR時刻の候補', line_warning({'noSpeechProb': .9}, [{'start': 0., 'end': 1.}], False))
