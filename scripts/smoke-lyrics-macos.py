"""Load the prepared Japanese ASR and alignment models on Apple Silicon."""
import sys
import tempfile
from pathlib import Path

from smoke_audio import write_tone


def main(runtime):
    source = Path(__file__).resolve().parent.parent
    sys.path.insert(0, str(source / 'analysis'))
    from engines import configure
    from lyrics import transcribe

    models, device = configure(runtime)
    with tempfile.TemporaryDirectory() as folder:
        audio = Path(folder) / 'tone.wav'
        write_tone(audio)
        tracks, engine = transcribe(audio, models, device, 'japanese', '', 12, Path(folder))
        assert set(tracks) == {'lyrics', 'words'}
        assert engine['asr'] == 'large-v3' and engine['alignment'] == 'japanese'
        print('Japanese ASR and alignment models loaded on Apple Silicon.', flush=True)


if __name__ == '__main__':
    main(Path(sys.argv[1]).resolve())
