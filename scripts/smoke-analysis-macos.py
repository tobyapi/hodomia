"""Exercise the full offline analysis pipeline with prepared macOS models."""
import sys
import tempfile
from pathlib import Path

from smoke_audio import write_tone


def main(runtime):
    source = Path(__file__).resolve().parent.parent
    sys.path.insert(0, str(source / 'analysis'))
    from pipeline import run
    from storage import create, snapshot

    with tempfile.TemporaryDirectory() as folder:
        home = Path(folder)
        audio, projects = home / 'tone.wav', home / 'projects'
        projects.mkdir()
        write_tone(audio)
        project = Path(create(audio, projects)['root'])
        run(project, runtime, {'mode': 'instrumental'})
        result = snapshot(project)
        status = result['status']
        if status['state'] != 'complete' or status['errors']:
            raise RuntimeError(f'Full analysis did not complete: {status}')
        assert result['result']['tracks']['chords']
        print('Full offline analysis completed on Apple Silicon.', flush=True)


if __name__ == '__main__':
    main(Path(sys.argv[1]).resolve())
