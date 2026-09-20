"""Offline integration harness using generated audio; requires prepared models."""
import json
import os
from pathlib import Path
import subprocess
import sys
import numpy as np
import soundfile as sf
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'analysis'))
from storage import create, snapshot, write_json
from pipeline import run

root = Path(__file__).resolve().parents[1]
work = root / 'test-results' / 'synthetic'
work.mkdir(parents=True, exist_ok=True)
sr, duration = 44100, 24
t = np.arange(sr * duration) / sr
signal = np.zeros(len(t))
for start, notes in [(0, [48, 52, 55]), (6, [45, 48, 52]), (12, [41, 45, 48]), (18, [43, 47, 50])]:
    mask = (t >= start) & (t < start + 6)
    for note in notes:
        signal[mask] += .1 * np.sin(2 * np.pi * 440 * 2 ** ((note - 69) / 12) * t[mask])
phase = t % .5
signal += .3 * np.exp(-phase * 60) * np.sin(2 * np.pi * 90 * t)
source = work / '合成インスト.wav'
sf.write(source, signal, sr)
import imageio_ffmpeg
ffmpeg = imageio_ffmpeg.get_ffmpeg_exe()
formats = []
for suffix, codec in [('mp3', 'libmp3lame'), ('m4a', 'aac'), ('mp4', 'aac'), ('flac', 'flac')]:
    target = work / ('形式検証.' + suffix)
    subprocess.run([ffmpeg, '-y', '-hide_banner', '-loglevel', 'error', '-i', str(source), '-c:a', codec, str(target)],
                   check=True, creationflags=0x08000000 if os.name == 'nt' else 0)
    value = create(target, work)
    assert abs(value['project']['duration'] - duration) < .1
    formats.append(suffix)
value = create(source, work)
run(value['root'], root / '.runtime', {'mode': 'instrumental', 'lyrics': ''})
result = snapshot(value['root'])
assert result['status']['state'] == 'complete', result['status']
assert not result['result']['tracks']['lyrics']
assert set(result['result']['stems']) == {'vocals', 'drums', 'bass', 'other'}
assert result['result']['series']['pitch']['points']
write_json(work / 'verification.json', {'formats': ['wav'] + formats, 'project': value['root'], 'status': result['status'],
                                       'bpm': result['result'].get('bpm'), 'expectedBpm': 120})
print(json.dumps({'formats': formats, 'project': value['root'], 'state': result['status']['state']}))
