"""Project storage and portable interchange. This module has no ML dependencies."""
import hashlib
import math
import shutil
import uuid
from locking import project_mutation, file_lock
from control_errors import ConflictError
from json_store import write_json, read_json
from project_export import export, effective_tracks, effective_bpm, srt_time
from datetime import datetime, timezone
from pathlib import Path

from track_schema import TRACKS, validate_tracks
FORMATS = ('.mp3', '.mp4', '.m4a', '.wav', '.flac')


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


@project_mutation
def save_edits(root, edits):
    return _save_edits(root, edits)


def _save_edits(root, edits, mutation=None):
    root = Path(root)
    project = manifest(root)
    current = read_json(root / 'edits.json')
    if edits.get('revision') != current['revision']:
        raise ConflictError()
    validate_tracks(edits.get('tracks'), project['duration'])
    current = {'revision': current['revision'] + 1, 'tracks': edits['tracks']}
    if mutation is not None:
        current['lastMutation'] = mutation
    (root / 'history').mkdir(exist_ok=True)
    write_json(root / 'history' / f"edits-{current['revision']}.json", current)
    write_json(root / 'edits.json', current)
    return current


def delete_analysis(root):
    with file_lock(Path(root) / '.analysis.lock'), file_lock(Path(root) / '.write.lock'):
        return _delete_analysis(root)


def _delete_analysis(root):
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


def row(track, index, start, end, label, **extra):
    return {'id': f'{track}-{index}', 'start': start, 'end': end, 'label': label,
            'reviewed': False, **extra}
