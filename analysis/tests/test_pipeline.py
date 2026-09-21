import json
import math
from pathlib import Path
import sys
import subprocess
import tempfile
import unittest
import wave
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from storage import create, save_edits, snapshot, export, within, write_json, validate_tracks, row, delete_analysis
from lyrics import match_lines


from project_fixture import ProjectFixture


class ProjectTests(ProjectFixture):
    def test_changed_source_fails_without_overwriting_edits(self):
        from pipeline import run
        before = (self.project / 'edits.json').read_bytes()
        source = self.project / snapshot(self.project)['project']['source']['path']
        source.write_bytes(b'changed')
        with self.assertRaisesRegex(ValueError, '変更'):
            run(self.project, self.root, {'mode': 'japanese'})
        self.assertEqual(snapshot(self.project)['status']['state'], 'failed')
        self.assertEqual((self.project / 'edits.json').read_bytes(), before)


    def test_cancelled_checkpoint_is_recoverable(self):
        project = snapshot(self.project)['project']
        project['currentRun'] = 'cancelled-run'
        run = self.project / 'runs/cancelled-run'
        run.mkdir(parents=True)
        write_json(run / 'result.json', {'tracks': {'beats': [row('b', 0, .5, .5, '1')]}})
        write_json(run / 'status.json', {'state': 'running', 'stage': '歌詞', 'errors': []})
        write_json(self.project / 'project.json', project)
        (self.project / 'cancel.flag').write_text('cancel')
        value = snapshot(self.project)
        self.assertEqual(value['status']['state'], 'cancelled')
        self.assertEqual(len(value['result']['tracks']['beats']), 1)


    def test_chord_run_uses_btc_original_audio_and_preserves_edits_and_history(self):
        from unittest.mock import patch
        from types import SimpleNamespace
        from pipeline import run
        project = snapshot(self.project)['project']
        original = {'sourceHash': project['source']['sha256'], 'mode': 'japanese',
                    'tracks': {'lyrics': [row('l', 0, .1, .8, '歌詞')], 'chords': [row('c', 0, 0, 1, 'C')]},
                    'series': {}, 'stems': {}, 'engines': {}, 'chordComparisons': {'template': {'rows': []}}}
        project['currentRun'] = 'previous'
        previous = self.project / 'runs/previous/result.json'
        previous.parent.mkdir(parents=True)
        write_json(previous, original)
        write_json(self.project / 'project.json', project)
        save_edits(self.project, {'revision': 0, 'tracks': {'chords': [row('manual', 0, 0, 1, 'G')]}})
        edits = snapshot(self.project)['edits']
        engines = SimpleNamespace(configure=lambda _: (self.root, 'cpu'), release=lambda: None,
                                  separate=None, beats=None, sections=None)
        chords = [row('chord', 0, 0, 1, 'A:min7')]
        keys = [row('key', 0, 0, 1, 'A minor')]
        with patch.dict(sys.modules, {'engines': engines}), patch('socket.create_connection'), patch('socket.socket.connect'), \
             patch('dsp.basics', return_value=([0], 22050, {}, [])), \
             patch('dsp.accompaniment', return_value=([1], 'bass + other')), \
             patch('dsp.estimate_key', return_value=keys) as key, \
             patch('chordmini.infer', return_value=(chords, {'backend': 'chordmini-btc', 'source': 'original'})) as infer:
            run(self.project, self.root, {'mode': 'japanese', 'scope': 'harmony'})
        value = snapshot(self.project)
        self.assertEqual(value['status']['state'], 'complete')
        self.assertEqual(value['result']['tracks']['chords'], chords)
        self.assertEqual(value['result']['tracks']['key'], keys)
        self.assertEqual(value['result']['tracks']['lyrics'], original['tracks']['lyrics'])
        self.assertEqual(value['edits'], edits)
        self.assertNotIn('chordComparisons', value['result'])
        self.assertEqual(json.loads(previous.read_text(encoding='utf-8')), original)
        self.assertEqual(infer.call_args.args[0], self.project / 'audio.wav')
        key.assert_called_once_with([1], 22050, 1.)


    def test_vocal_only_run_preserves_lyrics_original_run_and_manual_edits(self):
        from unittest.mock import patch
        from types import SimpleNamespace
        from pipeline import run
        original = {'tracks': {'lyrics': [row('l', 0, .1, .8, '元の歌詞')]},
                    'mode': 'japanese', 'series': {}, 'stems': {}, 'engines': {}}
        project = snapshot(self.project)['project']
        project['currentRun'] = 'previous'
        previous = self.project / 'runs/previous'
        previous.mkdir(parents=True)
        write_json(previous / 'result.json', original)
        write_json(self.project / 'project.json', project)
        save_edits(self.project, {'revision': 0, 'tracks': {'lyrics': [row('l', 0, .1, .8, '手修正')]}})
        def unexpected(*args):
            self.fail('声の表現のみの実行で他の解析を呼んではいけません')
        engines = SimpleNamespace(configure=lambda _: (self.root, 'cpu'), release=lambda: None,
                                  separate=unexpected, beats=unexpected, sections=unexpected)
        event = row('v', 0, 0, .5, 'ブレス', category='breath')
        with patch.dict(sys.modules, {'engines': engines}), patch('socket.create_connection'), patch('socket.socket.connect'), \
             patch('vocal_events.detect', return_value=([event], {'model': 'test'})):
            run(self.project, self.root, {'mode': 'instrumental', 'scope': 'vocal-events'})
        value = snapshot(self.project)
        self.assertEqual(value['status']['state'], 'complete')
        self.assertEqual(value['result']['mode'], 'japanese')
        self.assertEqual(value['result']['tracks']['lyrics'], original['tracks']['lyrics'])
        self.assertEqual(value['result']['tracks']['vocalEvents'], [event])
        self.assertEqual(value['edits']['tracks']['lyrics'][0]['label'], '手修正')
        self.assertEqual(json.loads((previous / 'result.json').read_text(encoding='utf-8')), original)

