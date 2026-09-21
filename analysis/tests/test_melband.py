import copy
import tempfile
import unittest
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import numpy as np
import soundfile as sf
from melband import cached_result, digest, validate_outputs, verify, FILES
from playback_sources import stems
from analysis_options import validate_options
from storage import write_json


class MelbandTests(unittest.TestCase):
    def test_cache_requires_identical_settings_and_untouched_outputs(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            key = {'inputHash': 'source', 'settings': {'segmentSize': 801}}
            paths = {name: name + '.wav' for name in ('melband_vocals', 'melband_instrumental')}
            for path in paths.values(): (root / path).write_bytes(b'audio')
            previous = {'stems': paths, 'engine': {'cacheKey': key, 'outputHashes': {name: digest(root / path) for name, path in paths.items()}}}
            self.assertEqual(cached_result(root, previous, key), previous)
            changed = copy.deepcopy(key)
            changed['settings']['segmentSize'] = 401
            self.assertIsNone(cached_result(root, previous, changed))
            (root / paths['melband_vocals']).write_bytes(b'changed')
            self.assertIsNone(cached_result(root, previous, key))

    def test_output_rejects_duration_channels_and_nan(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            for name in ('melband_vocals', 'melband_instrumental'):
                sf.write(root / (name + '.wav'), np.zeros((44100, 2)), 44100, subtype='FLOAT')
            self.assertEqual(len(validate_outputs(root, 1)), 2)
            with self.assertRaises(ValueError): validate_outputs(root, 2)
            for data in (np.zeros(44100), np.full((44100, 2), np.nan)):
                sf.write(root / 'melband_vocals.wav', data, 44100, subtype='FLOAT')
                with self.assertRaises(ValueError): validate_outputs(root, 1)

    def test_tampered_model_manifest_cannot_select_other_weights(self):
        with tempfile.TemporaryDirectory() as temp:
            write_json(Path(temp) / 'installation.json', {'version': '0.47.0', 'files': {k: 'bad' for k in FILES}})
            with self.assertRaises(ValueError): verify(temp)

    def test_playback_sources_do_not_mutate_four_stems(self):
        result = {'stems': {'vocals': 'demucs.wav'}, 'separationComparison': {'stems': {'melband_vocals': 'mel.wav'}}}
        self.assertEqual(stems(result), {'vocals': 'demucs.wav', 'melband_vocals': 'mel.wav'})
        self.assertEqual(result['stems'], {'vocals': 'demucs.wav'})
        validate_options({'mode': 'japanese', 'scope': 'separation-comparison'}, 60)
        with self.assertRaises(ValueError):
            validate_options({'mode': 'japanese', 'scope': 'separation-comparison', 'region': {'start': 0, 'end': 1, 'language': 'ja'}}, 60)
