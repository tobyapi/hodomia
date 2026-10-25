import re
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
import numpy as np
import soundfile as sf
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import separation
from separation_runner import analysis_stems
from storage import write_json


def stereo(frames, value=0.):
    return np.full((frames, 2), value, dtype=np.float32)


class InstalledFixture(unittest.TestCase):
    def setUp(self):
        self.work = tempfile.TemporaryDirectory()
        self.runtime = Path(self.work.name)
        self.folder = separation.home(self.runtime)
        (self.folder / 'weights').mkdir(parents=True)
        (self.folder / 'weights/model.ckpt').write_bytes(b'weights')
        write_json(self.folder / 'installation.json', dict(setup=separation.SETUP_ID, commit=separation.COMMIT,
                                                           files={'weights/model.ckpt': separation.digest(self.folder / 'weights/model.ckpt')}))

    def tearDown(self):
        self.work.cleanup()


class InstallationTests(InstalledFixture):
    def test_recorded_files_pass(self):
        separation.verify_installation(self.folder)

    def test_a_runtime_without_separation_setup_is_told_to_run_setup(self):
        (self.folder / 'installation.json').unlink()
        with self.assertRaisesRegex(RuntimeError, 'セットアップ'):
            separation.verify_installation(self.folder)

    def test_an_older_setup_is_told_to_run_setup_again(self):
        write_json(self.folder / 'installation.json', dict(setup='htdemucs_ft', commit=separation.COMMIT, files={'x': 'y'}))
        with self.assertRaisesRegex(RuntimeError, '更新'):
            separation.verify_installation(self.folder)

    def test_a_changed_weight_file_is_refused(self):
        (self.folder / 'weights/model.ckpt').write_bytes(b'other weights')
        with self.assertRaisesRegex(ValueError, 'weights/model.ckpt'):
            separation.verify_installation(self.folder)

    def test_rust_readiness_expects_the_same_setup(self):
        source = Path(__file__).resolve().parents[2] / 'src-tauri/src/workspace/separation_setup.rs'
        constant = re.search(r'const SETUP_ID: &str = "([^"]+)";', source.read_text(encoding='utf-8'))
        self.assertEqual(constant.group(1), separation.SETUP_ID)


class SeparateTests(InstalledFixture):
    def setUp(self):
        super().setUp()
        self.audio = self.runtime / 'audio.wav'
        sf.write(str(self.audio), stereo(441), separation.RATE)
        self.stems = self.runtime / 'run/stems'

    def runner(self, frames, code=0):
        def run(command, log_path, check_cancel, limit_seconds, timeout_message):
            output = Path(command[command.index('--output') + 1])
            for name in separation.STEMS:
                sf.write(str(output / f'{name}.wav'), stereo(frames), separation.RATE, subtype='FLOAT')
            Path(command[command.index('--metadata') + 1]).write_text('{"device": "cpu"}', encoding='utf-8')
            return code
        return run

    def test_four_stems_and_provenance_are_returned(self):
        with patch('separation.run_logged', self.runner(441)):
            paths = separation.separate(self.audio, self.stems, self.runtime, 'cpu')
        self.assertEqual(paths, {name: self.stems / f'{name}.wav' for name in separation.STEMS})
        metadata = (self.runtime / 'run/separation/separation.json').read_text(encoding='utf-8')
        self.assertIn(separation.ENGINE, metadata)
        self.assertIn(separation.COMMIT, metadata)

    def test_the_time_limit_grows_with_the_song(self):
        limits = []
        def run(command, log_path, check_cancel, limit_seconds, timeout_message):
            limits.append(limit_seconds)
            return self.runner(441)(command, log_path, check_cancel, limit_seconds, timeout_message)
        with patch('separation.run_logged', run):
            separation.separate(self.audio, self.stems, self.runtime, 'cpu')
        self.assertAlmostEqual(limits[0], separation.LIMIT_MARGIN_SECONDS + separation.LIMIT_PER_SECOND * .01)

    def test_a_failed_runner_points_to_its_log(self):
        with patch('separation.run_logged', self.runner(441, code=1)):
            with self.assertRaisesRegex(RuntimeError, 'separation.log'):
                separation.separate(self.audio, self.stems, self.runtime, 'cpu')

    def test_stems_of_another_length_are_refused(self):
        with patch('separation.run_logged', self.runner(440)):
            with self.assertRaisesRegex(ValueError, '長さ'):
                separation.separate(self.audio, self.stems, self.runtime, 'cpu')


class StemTests(unittest.TestCase):
    def test_other_is_what_vocals_drums_and_bass_leave(self):
        mix = stereo(4, 1.)
        stems = analysis_stems(mix, dict(vocals=stereo(4, .5)),
                               dict(drums=stereo(4, .2), bass=stereo(4, .1), vocals=stereo(4, .9), other=stereo(4, .9)))
        np.testing.assert_allclose(stems['other'], stereo(4, .2), atol=1e-6)
        np.testing.assert_allclose(sum(stems.values()), mix, atol=1e-6)
        np.testing.assert_allclose(stems['vocals'], stereo(4, .5))


if __name__ == '__main__':
    unittest.main()
