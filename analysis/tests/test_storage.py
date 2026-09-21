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
    def test_copy_decode_reopen(self):
        value = snapshot(self.project)
        self.assertAlmostEqual(value['project']['duration'], 1, places=2)
        self.assertTrue((self.project / 'audio.wav').exists())
        self.assertEqual(value['edits']['revision'], 0)


    def test_delete_analysis_preserves_original_and_playback_audio(self):
        before = snapshot(self.project)
        source = self.project / before['project']['source']['path']
        audio = self.project / before['project']['audio']
        originals = (source.read_bytes(), audio.read_bytes())
        for name in ('runs', 'history', 'exports'):
            folder = self.project / name
            folder.mkdir()
            (folder / 'result.txt').write_text('analysis')
        result = delete_analysis(self.project)
        self.assertIsNone(result['project']['currentRun'])
        self.assertEqual(result['edits']['tracks'], {})
        self.assertEqual((source.read_bytes(), audio.read_bytes()), originals)
        self.assertTrue(all(not (self.project / name).exists() for name in ('runs','history','exports')))


    def test_delete_analysis_refuses_audio_inside_analysis_folder(self):
        project = snapshot(self.project)['project']
        (self.project / 'runs').mkdir()
        protected = self.project / 'runs' / 'keep.wav'
        protected.write_bytes(b'original audio')
        project['audio'] = 'runs/keep.wav'
        write_json(self.project / 'project.json', project)
        with self.assertRaises(ValueError):
            delete_analysis(self.project)
        self.assertEqual(protected.read_bytes(), b'original audio')
        self.assertEqual(snapshot(self.project)['edits']['revision'], 0)


    def test_delivery_categories_round_trip_and_export(self):
        rows = [row('v', 0, 0, .6, 'ラップ', category='rap'),
                row('v', 1, .3, .9, '朗読・語り', category='spoken')]
        save_edits(self.project, {'revision': 0, 'tracks': {'vocalEvents': rows}})
        self.assertEqual(snapshot(self.project)['edits']['tracks']['vocalEvents'], rows)
        out = Path(export(self.project)['path'])
        csv = (out / 'timeline.csv').read_text(encoding='utf-8-sig')
        self.assertIn(',rap,', csv)
        self.assertIn(',spoken,', csv)
        self.assertEqual((out / 'lyrics.srt').read_text(encoding='utf-8').strip(), '')


    def test_edits_survive_reanalysis_and_export(self):
        edits = {'revision': 0, 'tracks': {'lyrics': [row('l', 0, .1, .8, '修正'), row('l', 1, None, None, '未確定')]}}
        save_edits(self.project, edits)
        project = snapshot(self.project)['project']
        project['currentRun'] = 'new'
        run = self.project / 'runs/new'
        run.mkdir(parents=True)
        write_json(run / 'result.json', {'tracks': {'lyrics': [row('l', 0, 0, .3, '自動')]}})
        write_json(self.project / 'project.json', project)
        value = snapshot(self.project)
        self.assertEqual(value['edits']['tracks']['lyrics'][0]['label'], '修正')
        out = export(self.project)
        self.assertEqual(out['untimedLyrics'], 1)
        text = (Path(out['path']) / 'lyrics.srt').read_text(encoding='utf-8')
        self.assertIn('00:00:00,100 --> 00:00:00,800', text)
        self.assertNotIn('未確定', text)
        with self.assertRaises(ValueError):
            save_edits(self.project, edits)


    def test_paths_and_invalid_time(self):
        with self.assertRaises(ValueError):
            within(self.project, '../outside')
        with self.assertRaises(ValueError):
            validate_tracks({'lyrics': [row('l', 0, float('nan'), 1, 'x')]}, 1)
        with self.assertRaises(ValueError):
            validate_tracks({'sections': [row('s', 0, 0, 2, 'x')]}, 1)


    def test_failed_import_leaves_original(self):
        invalid = self.root / 'broken.mp3'
        invalid.write_bytes(b'not music')
        before = set(self.root.iterdir())
        with self.assertRaises(Exception):
            create(invalid, self.root)
        self.assertEqual(set(self.root.iterdir()), before)


    def test_unmatched_lyrics_are_not_evenly_distributed(self):
        values = match_lines('こんにちは\n全く異なる文章', [{'text': 'こんにちは', 'start': .1, 'end': .7}], 1)
        self.assertIsNotNone(values[0]['start'])
        self.assertIsNone(values[1]['start'])


    def test_cli_round_trip_and_error_response(self):
        cli = Path(__file__).resolve().parents[1] / 'cli.py'
        process = subprocess.run([sys.executable, str(cli), '--runtime', str(self.root)],
                                 input=json.dumps({'operation': 'snapshot', 'args': {'root': str(self.project)}}),
                                 text=True, encoding='utf-8', capture_output=True)
        self.assertEqual(process.returncode, 0, process.stderr)
        self.assertEqual(json.loads(process.stdout)['value']['project']['name'], '日本語 test')
        process = subprocess.run([sys.executable, str(cli), '--runtime', str(self.root)],
                                 input=json.dumps({'operation': 'invalid'}), text=True, capture_output=True)
        self.assertNotEqual(process.returncode, 0)
        self.assertFalse(json.loads(process.stdout)['ok'])


    def test_vocal_events_persist_and_export_without_becoming_subtitles(self):
        edits = {'revision': 0, 'tracks': {
            'lyrics': [row('l', 0, .1, .8, '歌詞')],
            'vocalEvents': [row('v', 0, 0, .5, 'ブレス', category='breath', score=.4)],
        }}
        save_edits(self.project, edits)
        self.assertEqual(snapshot(self.project)['edits']['tracks']['vocalEvents'][0]['category'], 'breath')
        path = Path(export(self.project)['path'])
        self.assertIn('vocalEvents', (path / 'timeline.csv').read_text(encoding='utf-8-sig'))
        self.assertNotIn('ブレス', (path / 'lyrics.srt').read_text(encoding='utf-8'))
        self.assertIn('歌詞', (path / 'lyrics.srt').read_text(encoding='utf-8'))

