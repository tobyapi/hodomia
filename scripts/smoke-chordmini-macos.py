"""Run the installed ChordMini model on synthetic audio in macOS CI."""
import subprocess
import sys
import tempfile
from pathlib import Path

from smoke_audio import write_tone


def main(runtime):
    source = Path(__file__).resolve().parent.parent
    sys.path.insert(0, str(source / 'analysis'))
    from chordmini import read_lab, verify_installation

    home = runtime / 'chordmini'
    verify_installation(home)
    with tempfile.TemporaryDirectory() as folder:
        audio, result = Path(folder) / 'tone.wav', Path(folder) / 'output'
        write_tone(audio)
        subprocess.run([
            str(home / 'venv/bin/python'), str(source / 'analysis/chordmini_runner.py'),
            '--repo', str(home / 'repo'), '--audio', str(audio), '--output', str(result),
        ], check=True)
        rows = read_lab(result / 'chords.lab', 12)
        assert rows and (result / 'inference.json').is_file()
        print(f'ChordMini produced {len(rows)} intervals offline.', flush=True)


if __name__ == '__main__':
    main(Path(sys.argv[1]).resolve())
