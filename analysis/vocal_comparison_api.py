"""Bounded access to saved voice comparison evidence for CLI/MCP clients."""
from pathlib import Path
from control_errors import ConflictError, ControlError
from locking import file_lock
from storage import snapshot
from timeline_api import time_range
from vocal_labels import CATEGORIES


def get_comparison(root, variantId=None, category=None, start=0, end=None, kind='frames',
                   offset=0, limit=100, expectedRunId=None):
    with file_lock(Path(root) / '.analysis.lock'), file_lock(Path(root) / '.write.lock'):
        value = snapshot(root)
    data = value['result'].get('vocalComparisons')
    if data is None:
        raise ControlError('NOT_FOUND', '保存した声の比較がありません。scope=vocal-comparisonで実行してください。')
    run_id = data.get('runId', value['project']['currentRun'])
    if expectedRunId is not None and expectedRunId != run_id:
        raise ConflictError()
    start, end = time_range(start, end, value['project']['duration'])
    if category is not None and category not in CATEGORIES:
        raise ValueError('比較する声の分類が不正です。')
    if kind not in ('frames', 'candidates') or type(offset) is not int or offset < 0 or type(limit) is not int or not 1 <= limit <= 500:
        raise ValueError('kind、offset、limitが不正です。')
    if variantId is None:
        summaries = []
        for variant in data['variants']:
            frames = [f for f in variant['frames'] if f['start'] < end and f['end'] > start]
            summaries.append({k: v for k, v in variant.items() if k not in ('frames', 'candidates')} | {
                'frameCount': len(frames),
                'peakScores': {c: max((f['scores'][c] for f in frames), default=0.) for c in CATEGORIES},
                'candidateCounts': {c: sum(r['category'] == c and r['start'] < end and r['end'] > start for r in variant['candidates']) for c in CATEGORIES},
            })
        return {'runId': run_id, 'start': start, 'end': end, 'variants': summaries, 'notice': data['notice'], 'engines': data['engines']}
    variant = next((v for v in data['variants'] if v['id'] == variantId), None)
    if variant is None:
        raise ControlError('NOT_FOUND', '指定したモデル・音声の比較がありません。')
    rows = [r for r in variant[kind] if r['start'] < end and r['end'] > start and (kind == 'frames' or category is None or r['category'] == category)]
    if kind == 'frames' and category:
        rows = [{**r, 'scores': {category: r['scores'][category]}} for r in rows]
    return {'runId': run_id, 'variantId': variantId, 'kind': kind, 'start': start, 'end': end,
            'total': len(rows), 'rows': rows[offset:offset + limit], 'nextOffset': offset + limit if offset + limit < len(rows) else None}
