"""Project storage and portable interchange. This module has no ML dependencies."""
import csv
import hashlib
import io
import json
import math
import os
import shutil
import statistics
import uuid
from datetime import datetime, timezone
from pathlib import Path

TRACKS = ('beats', 'sections', 'lyrics', 'words', 'vocalEvents', 'chords', 'key')
FORMATS = ('.mp3', '.mp4', '.m4a', '.wav', '.flac')


def write_json(path, value):
    path = Path(path)
    temporary = path.with_name(path.name + '.' + uuid.uuid4().hex + '.tmp')
    try:
        temporary.write_text(json.dumps(value, ensure_ascii=False, allow_nan=False, indent=2), encoding='utf-8')
        os.replace(temporary, path)
    finally:
        temporary.unlink(missing_ok=True)


def read_json(path):
    return json.loads(Path(path).read_text(encoding='utf-8-sig'))


def within(root, relative):
    root = Path(root).resolve()
    path = (root / relative).resolve()
    if not path.is_relative_to(root):
        raise ValueError('プロジェクト外のパスは使用できません。')
    return path


def manifest(root):
    value = read_json(Path(root) / 'project.json')
    if value.get('schemaVersion') != 1 or value.get('kind') != 'music-sweeper':
        raise ValueError('Music Sweeper のプロジェクトではありません。')
    within(root, value['source']['path'])
    within(root, value['audio'])
    if type(value.get('duration')) not in (int, float) or not math.isfinite(value['duration']) or not 0 < value['duration'] <= 900:
        raise ValueError('プロジェクトの曲の長さが不正です。')
    return value


def snapshot(root):
    root = Path(root).resolve()
    project = manifest(root)
    edits = read_json(root / 'edits.json')
    result, status = {}, {'state': 'idle', 'stage': '未解析', 'errors': []}
    if project.get('currentRun'):
        run = within(root, 'runs/' + project['currentRun'])
        if (run / 'result.json').exists():
            result = read_json(run / 'result.json')
        if (run / 'status.json').exists():
            status = read_json(run / 'status.json')
        if status['state'] == 'running' and (root / 'cancel.flag').exists():
            status = {**status, 'state': 'cancelled', 'stage': '中止しました'}
    return {'root': str(root), 'project': project, 'edits': edits, 'result': result, 'status': status}


def create(source, parent):
    from media import decode
    source = Path(source).resolve()
    parent = Path(parent).resolve()
    if not source.is_file() or source.suffix.lower() not in FORMATS:
        raise ValueError('MP3・MP4・M4A・WAV・FLAC を選んでください。')
    if not parent.is_dir():
        raise ValueError('保存先フォルダーがありません。')
    if shutil.disk_usage(parent).free < source.stat().st_size + 2_000_000_000:
        raise ValueError('取り込みには元ファイルの容量に加えて2GB以上の空き容量が必要です。')
    root = parent / (source.stem[:60] + '-' + uuid.uuid4().hex[:8])
    root.mkdir()
    try:
        (root / 'source').mkdir()
        copied = root / 'source' / source.name
        shutil.copy2(source, copied)
        with copied.open('rb') as stream:
            digest = hashlib.file_digest(stream, 'sha256').hexdigest()
        duration = decode(copied, root / 'audio.wav')
        value = {'schemaVersion': 1, 'kind': 'music-sweeper', 'id': uuid.uuid4().hex,
                 'name': source.stem, 'createdAt': datetime.now(timezone.utc).isoformat(),
                 'duration': duration, 'source': {'path': 'source/' + source.name, 'sha256': digest},
                 'audio': 'audio.wav', 'currentRun': None}
        write_json(root / 'project.json', value)
        write_json(root / 'edits.json', {'revision': 0, 'tracks': {}})
        return snapshot(root)
    except Exception:
        # The folder was just created by this operation; never touch the input.
        shutil.rmtree(root)
        raise


def validate_tracks(tracks, duration):
    if not isinstance(tracks, dict) or set(tracks) - set(TRACKS):
        raise ValueError('編集トラックが不正です。')
    for track, rows in tracks.items():
        if not isinstance(rows, list) or len(rows) > 100000:
            raise ValueError('編集データが不正です。')
        ids = set()
        for row in rows:
            if not isinstance(row, dict) or not isinstance(row.get('id'), str) or row['id'] in ids:
                raise ValueError('項目IDは一意である必要があります。')
            ids.add(row['id'])
            if track == 'vocalEvents' and row.get('category') not in ('beatbox', 'breath', 'humming', 'other', 'rap', 'spoken'):
                raise ValueError('声の表現の分類が不正です。')
            if not isinstance(row.get('label', ''), str) or len(row.get('label', '')) > 10000:
                raise ValueError('項目のテキストが不正です。')
            start, end = row.get('start'), row.get('end')
            if start is None and end is None and track in ('lyrics', 'words'):
                continue
            if any(type(t) not in (float, int) or not math.isfinite(t) for t in (start, end)):
                raise ValueError('時刻は有限の数値で指定してください。')
            if not 0 <= start <= end <= duration or (track != 'beats' and start == end):
                raise ValueError('時刻は曲の長さの範囲内で、終了を開始より後にしてください。')


def save_edits(root, edits):
    root = Path(root)
    project = manifest(root)
    current = read_json(root / 'edits.json')
    if edits.get('revision') != current['revision']:
        raise ValueError('別の保存が先に行われました。プロジェクトを開き直してください。')
    validate_tracks(edits.get('tracks'), project['duration'])
    current = {'revision': current['revision'] + 1, 'tracks': edits['tracks']}
    (root / 'history').mkdir(exist_ok=True)
    write_json(root / 'history' / f"edits-{current['revision']}.json", current)
    write_json(root / 'edits.json', current)
    return current


def effective_tracks(value):
    return {**value['result'].get('tracks', {}), **value['edits']['tracks']}


def delete_analysis(root):
    root = Path(root).resolve()
    project = manifest(root)
    protected = [within(root, project['source']['path']), within(root, project['audio'])]
    targets = [within(root, name) for name in ('runs', 'history', 'exports')]
    if any(file.is_relative_to(target) for target in targets for file in protected):
        raise ValueError('音源が解析フォルダー内にあるため削除できません。')
    revision = read_json(root / 'edits.json')['revision']
    project['currentRun'] = None
    write_json(root / 'project.json', project)
    write_json(root / 'edits.json', {'revision': revision + 1, 'tracks': {}})
    for target in targets:
        if target.exists():
            shutil.rmtree(target)
    (root / 'cancel.flag').unlink(missing_ok=True)
    return snapshot(root)


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


def row(track, index, start, end, label, **extra):
    return {'id': f'{track}-{index}', 'start': start, 'end': end, 'label': label,
            'reviewed': False, **extra}
