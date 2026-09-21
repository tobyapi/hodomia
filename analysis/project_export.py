"""Portable JSON, CSV and subtitle export from saved project data."""
import csv
import statistics
import uuid
from datetime import datetime
from pathlib import Path
from locking import file_lock


def effective_tracks(value):
    return {**value['result'].get('tracks', {}), **value['edits']['tracks']}


def effective_bpm(tracks):
    times = sorted(r['start'] for r in tracks.get('beats', []) if r.get('start') is not None)
    intervals = [b - a for a, b in zip(times, times[1:]) if b > a]
    return 60 / statistics.median(intervals) if intervals else None


def srt_time(seconds):
    millis = round(seconds * 1000)
    hours, millis = divmod(millis, 3600000)
    minutes, millis = divmod(millis, 60000)
    seconds, millis = divmod(millis, 1000)
    return f'{hours:02d}:{minutes:02d}:{seconds:02d},{millis:03d}'


def export(root):
    with file_lock(Path(root) / '.analysis.lock'), file_lock(Path(root) / '.write.lock'):
        return _export(root)


def _export(root):
    from storage import snapshot, write_json
    value = snapshot(root)
    tracks = effective_tracks(value)
    out = Path(root) / 'exports' / (datetime.now().strftime('%Y%m%d-%H%M%S') + '-' + uuid.uuid4().hex[:6])
    out.mkdir(parents=True)
    write_json(out / 'analysis.json', {**value, 'tracks': tracks, 'bpm': effective_bpm(tracks), 'notice': '自動推定には未確認の情報を含みます。'})
    with (out / 'timeline.csv').open('w', encoding='utf-8-sig', newline='') as stream:
        writer = csv.writer(stream)
        writer.writerow(['track', 'start', 'end', 'label', 'reviewed', 'warning', 'category', 'model_score', 'evidence_sources'])
        for track, rows in tracks.items():
            for row in rows:
                label = row.get('label', '')
                # Prevent spreadsheet formula execution while preserving JSON verbatim.
                if label.startswith(('=', '+', '-', '@')):
                    label = "'" + label
                writer.writerow([track, row.get('start'), row.get('end'), label, row.get('reviewed', False), row.get('warning', ''),
                                 row.get('category', ''), row.get('score', ''), '|'.join(row.get('evidenceSources', []))])
    rows = sorted((r for r in tracks.get('lyrics', []) if r.get('start') is not None and r.get('end') is not None), key=lambda r: r['start'])
    text = '\n\n'.join(f"{i}\n{srt_time(r['start'])} --> {srt_time(r['end'])}\n{r['label']}" for i, r in enumerate(rows, 1))
    (out / 'lyrics.srt').write_text(text + '\n', encoding='utf-8')
    return {'path': str(out), 'untimedLyrics': sum(r.get('start') is None for r in tracks.get('lyrics', []))}

