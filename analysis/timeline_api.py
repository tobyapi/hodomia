"""Bounded timeline reads and optimistic, idempotent segment edits."""
import copy
import hashlib
import json
import math
import re
import uuid
from pathlib import Path
from control_errors import ConflictError
from locking import file_lock
import storage


def time_range(start, end, duration):
    end = duration if end is None else end
    if any(type(t) not in (int, float) or not math.isfinite(t) for t in (start, end)) or not 0 <= start < end <= duration:
        raise ValueError('開始・終了秒を曲の範囲内で指定してください。')
    return start, end


def version_check(value, revision, run_id):
    if type(revision) is not int or revision != value['edits']['revision'] or run_id != value['project']['currentRun']:
        raise ConflictError()


def get_timeline(root, tracks=None, start=0, end=None, view='effective', offset=0, limit=100,
                 includeUntimed=False, expectedRevision=None, expectedRunId=None):
    value = storage.snapshot(root)
    if expectedRevision is not None:
        version_check(value, expectedRevision, expectedRunId)
    if tracks is None:
        tracks = list(storage.TRACKS)
    if not isinstance(tracks, list) or not tracks or any(t not in storage.TRACKS for t in tracks):
        raise ValueError('トラック名が不正です。')
    if type(offset) is not int or offset < 0 or type(limit) is not int or not 1 <= limit <= 500:
        raise ValueError('offsetは0以上、limitは1〜500で指定してください。')
    if view not in ('effective', 'automatic', 'manual') or type(includeUntimed) is not bool:
        raise ValueError('表示対象が不正です。')
    start, end = time_range(start, end, value['project']['duration'])
    sources = {'effective': storage.effective_tracks(value), 'automatic': value['result'].get('tracks', {}), 'manual': value['edits']['tracks']}
    rows = []
    for track in dict.fromkeys(tracks):
        origin = 'manual' if view == 'manual' or (view == 'effective' and track in value['edits']['tracks']) else 'automatic'
        for row in sources[view].get(track, []):
            a, b = row.get('start'), row.get('end')
            matches = includeUntimed if a is None else start <= a < end if a == b else a < end and b > start
            if matches:
                rows.append({**row, 'track': track, 'origin': origin})
    rows.sort(key=lambda r: (r['start'] is None, r['start'] or 0, r['track'], r['id']))
    return dict(revision=value['edits']['revision'], runId=value['project']['currentRun'], view=view,
                start=start, end=end, total=len(rows), rows=rows[offset:offset + limit],
                nextOffset=offset + limit if offset + limit < len(rows) else None,
                status=value['status']['state'])


EDIT_FIELDS = {'start', 'end', 'label', 'reviewed', 'language', 'category'}


def changed_tracks(value, operations):
    if not isinstance(operations, list) or not 1 <= len(operations) <= 100:
        raise ValueError('変更は1〜100件で指定してください。')
    effective = storage.effective_tracks(value)
    edits = copy.deepcopy(value['edits']['tracks'])
    changes = []
    for operation in operations:
        if not isinstance(operation, dict) or set(operation) - {'op', 'track', 'id', 'changes'}:
            raise ValueError('変更操作が不正です。')
        track, op = operation.get('track'), operation.get('op')
        fields = operation.get('changes', {})
        if track not in storage.TRACKS or op not in ('add', 'update', 'delete') or not isinstance(fields, dict) or set(fields) - EDIT_FIELDS:
            raise ValueError('トラック・操作・変更フィールドが不正です。')
        if 'reviewed' in fields and type(fields['reviewed']) is not bool:
            raise ValueError('reviewedは真偽値で指定してください。')
        if 'language' in fields and (not isinstance(fields['language'], str) or len(fields['language']) > 16):
            raise ValueError('languageは16文字以内の文字列で指定してください。')
        if op == 'delete' and fields:
            raise ValueError('削除操作にchangesは指定できません。')
        rows = edits.setdefault(track, copy.deepcopy(effective.get(track, [])))
        before = next((r for r in rows if r['id'] == operation.get('id')), None)
        if op == 'add':
            if operation.get('id') is not None:
                raise ValueError('追加項目のIDは自動生成します。')
            if not {'label', 'start', 'end'}.issubset(fields):
                raise ValueError('追加にはlabel、start、endが必要です。')
            after = {'id': uuid.uuid4().hex, 'reviewed': False, **fields}
            rows.append(after)
        else:
            if before is None:
                raise ValueError('変更対象の項目がありません。')
            after = {**before, **fields} if op == 'update' else None
            rows[rows.index(before):rows.index(before) + 1] = [after] if after else []
        changes.append(dict(track=track, before=before, after=after))
    storage.validate_tracks(edits, value['project']['duration'])
    for track in edits:
        edits[track].sort(key=lambda r: (r.get('start') is None, r.get('start') or 0, r['id']))
    return edits, changes


def update_segments(root, expectedRevision, expectedRunId, requestId, operations, dryRun=False):
    if not isinstance(requestId, str) or not re.fullmatch('[A-Za-z0-9_-]{1,128}', requestId) or type(dryRun) is not bool:
        raise ValueError('requestIdは英数字・_・-の128文字以内で指定してください。')
    root = Path(root)
    request_hash = hashlib.sha256(json.dumps([expectedRevision, expectedRunId, operations], sort_keys=True, ensure_ascii=False).encode()).hexdigest()
    receipt = root / 'history/operations' / (requestId + '.json')
    with file_lock(root / '.analysis.lock'), file_lock(root / '.write.lock'):
        value = storage.snapshot(root)
        if receipt.is_file() and not dryRun:
            saved = storage.read_json(receipt)
            if saved['requestHash'] != request_hash:
                raise ConflictError()
            history = root / 'history' / f"edits-{saved['revision']}.json"
            if value['edits']['revision'] >= saved['revision'] and history.is_file() and storage.read_json(history).get('lastMutation', {}).get('requestId') == requestId:
                return {**saved['result'], 'replayed': True, 'currentRevision': value['edits']['revision']}
        version_check(value, expectedRevision, expectedRunId)
        edits, changes = changed_tracks(value, operations)
        result = dict(revision=expectedRevision if dryRun else expectedRevision + 1, runId=expectedRunId,
                      changes=changes, dryRun=dryRun, replayed=False)
        if not dryRun:
            receipt.parent.mkdir(parents=True, exist_ok=True)
            storage.write_json(receipt, dict(requestHash=request_hash, revision=result['revision'], result=result))
            storage._save_edits(root, {'revision': expectedRevision, 'tracks': edits},
                                mutation={'requestId': requestId, 'requestHash': request_hash})
        return result
