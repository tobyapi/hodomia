import sys
import threading
import time
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from checkpoints import Cancelled
from harmony_stage import BackgroundChords, analyze_harmony
from storage import row, snapshot
from project_fixture import ProjectFixture


def infer_until_cancelled(started, cancelled):
    def infer(audio, runtime, folder, duration, check_cancel):
        started.set()
        while True:
            try:
                check_cancel()
            except Cancelled:
                cancelled.set()
                raise
            time.sleep(.01)
    return infer


class BackgroundChordTests(unittest.TestCase):
    def test_stop_cancels_an_uncollected_inference_and_waits_for_it(self):
        started, cancelled = threading.Event(), threading.Event()
        with patch('chordmini.infer', infer_until_cancelled(started, cancelled)):
            chords = BackgroundChords('audio.wav', 'runtime', 'run', 1., lambda: False)
            self.assertTrue(started.wait(5))
            chords.stop()
        self.assertTrue(cancelled.is_set())
        self.assertTrue(chords.future.done())

    def test_setup_error_surfaces_when_the_chord_stage_collects(self):
        with patch('chordmini.infer', side_effect=ValueError('ChordMiniが未準備です。')):
            chords = BackgroundChords('audio.wav', 'runtime', 'run', 1., lambda: False)
            with self.assertRaisesRegex(ValueError, '未準備'):
                chords.result()
            chords.stop()

    def test_failed_key_estimate_stops_btc_and_keeps_previous_harmony(self):
        started, cancelled = threading.Event(), threading.Event()
        result = {'tracks': {'chords': [row('c', 0, 0, 1, 'C')]}, 'engines': {}}
        with patch('chordmini.infer', infer_until_cancelled(started, cancelled)), \
             patch('dsp.accompaniment', return_value=([1.], 'bass + other')), \
             patch('dsp.estimate_key', side_effect=RuntimeError('key failed')):
            chords = BackgroundChords('audio.wav', 'runtime', 'run', 1., lambda: False)
            with self.assertRaisesRegex(RuntimeError, 'key failed'):
                analyze_harmony(result, chords, {}, [1.], 22050, 1.)
        self.assertTrue(cancelled.is_set())
        self.assertEqual(result['tracks']['chords'][0]['label'], 'C')
        self.assertEqual(result['engines'], {})


def write_stems(out):
    out.mkdir()
    for name in ('vocals', 'drums', 'bass', 'other'):
        (out / (name + '.wav')).write_bytes(b'')
    return {name: out / (name + '.wav') for name in ('vocals', 'drums', 'bass', 'other')}


def chords_at_once(audio, runtime, folder, duration, check_cancel):
    return [row('chord', 0, 0, 1, 'C')], {'backend': 'chordmini-btc', 'source': 'original'}


class FullRunTests(ProjectFixture):
    def analyze(self, separate, infer=chords_at_once):
        from pipeline import run
        engines = SimpleNamespace(configure=lambda _: (self.root, 'cpu'), release=lambda: None,
                                  beats=lambda *_: ([.5], [.5]), sections=lambda *_: [])
        with patch.dict(sys.modules, {'engines': engines}), patch('socket.create_connection'),              patch('socket.socket.connect'), patch('chordmini.infer', infer), patch('separation.separate', separate),              patch('dsp.basics', return_value=([0.], 22050, {'silence': False}, [])),              patch('dsp.stem_activity', return_value={}), patch('dsp.pitch', return_value={}),              patch('dsp.accompaniment', return_value=([1.], 'bass + other')),              patch('dsp.estimate_key', return_value=[row('key', 0, 0, 1, 'C major')]),              patch('vocal_events.detect', return_value=([], {'model': 'test'})):
            run(self.project, self.root, {'mode': 'instrumental'})
        return snapshot(self.project)

    def test_btc_runs_during_separation_and_each_stage_records_seconds(self):
        btc_started = threading.Event()
        def infer(audio, runtime, folder, duration, check_cancel):
            btc_started.set()
            return chords_at_once(audio, runtime, folder, duration, check_cancel)
        def separate(audio, out, runtime, device, check_cancel):
            # Separation finishes only if BTC was launched before it.
            if not btc_started.wait(5):
                raise AssertionError('BTCが分離と並行して起動していません')
            return write_stems(out)
        value = self.analyze(separate, infer)
        self.assertEqual(value['status']['state'], 'complete', value['status']['errors'])
        self.assertEqual(value['result']['tracks']['chords'][0]['label'], 'C')
        self.assertEqual([t['stage'] for t in value['status']['timings']],
                         ['波形・音量', 'ボーカル・楽器の分離', '拍・BPM', 'コード・キー', '曲構成・サビの推定',
                          '声の表現を検出', '主旋律の音高'])
        self.assertTrue(all(t['seconds'] >= 0 for t in value['status']['timings']))

    def test_stems_are_reused_only_from_the_same_separation_models(self):
        from separation import ENGINE
        older = self.analyze(lambda audio, out, *_: write_stems(out))
        result = self.project / 'runs' / older['project']['currentRun'] / 'result.json'
        result.write_text(result.read_text(encoding='utf-8').replace(ENGINE, 'htdemucs_ft / shifts=2 / overlap=.5'),
                          encoding='utf-8')
        separated = []
        def separate(audio, out, *_):
            separated.append(out)
            return write_stems(out)
        current = self.analyze(separate)
        self.assertEqual(len(separated), 1)
        self.assertEqual(current['result']['engines']['separation'], ENGINE)
        def unexpected(*_):
            raise AssertionError('同じ分離モデルのステムを再利用していません')
        reused = self.analyze(unexpected)
        self.assertEqual(reused['result']['engines']['separationCache'], current['project']['currentRun'])
        self.assertEqual(reused['result']['stems'], current['result']['stems'])
