"""Short, lossless WAV excerpts from the original or a saved stem."""
import math
import uuid
from pathlib import Path
from locking import file_lock
from storage import snapshot, within
from timeline_api import time_range


def extract_clip(root, start, end, stem='original'):
    import soundfile as sf
    root = Path(root)
    with file_lock(root / '.analysis.lock'):
        value = snapshot(root)
        start, end = time_range(start, end, value['project']['duration'])
        if end - start > 30:
            raise ValueError('音声切り出しは1回30秒以内で指定してください。')
        relative = value['project']['audio'] if stem == 'original' else value['result'].get('stems', {}).get(stem)
        if not relative:
            raise ValueError('指定した分離音声がありません。')
        source = within(root, relative)
        folder = within(root, 'exports/clips')
        folder.mkdir(parents=True, exist_ok=True)
        output = folder / (uuid.uuid4().hex + '.wav')
        with sf.SoundFile(source) as stream:
            first, last = math.floor(start * stream.samplerate), min(len(stream), math.ceil(end * stream.samplerate))
            if first >= last:
                raise ValueError('指定した区間の音声がありません。')
            stream.seek(first)
            samples = stream.read(last - first, dtype='float32', always_2d=True)
            sf.write(output, samples, stream.samplerate, subtype='FLOAT')
            return dict(path=str(output), start=first / stream.samplerate, end=last / stream.samplerate,
                        sampleRate=stream.samplerate, channels=stream.channels, stem=stem,
                        sourceHash=value['project']['source']['sha256'], runId=value['project']['currentRun'])
