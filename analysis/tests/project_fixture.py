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


class ProjectFixture(unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory()
        self.root = Path(self.directory.name)
        audio = self.root / '日本語 test.wav'
        import array
        samples = array.array('h', [int(math.sin(i * .1) * 2000) for i in range(16000)])
        with wave.open(str(audio), 'wb') as f:
            f.setnchannels(1); f.setsampwidth(2); f.setframerate(16000); f.writeframes(samples.tobytes())
        self.project = Path(create(audio, self.root)['root'])

    def tearDown(self):
        self.directory.cleanup()

