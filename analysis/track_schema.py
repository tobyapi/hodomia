"""Validation of editable timeline tracks."""
import math

TRACKS = ('beats', 'sections', 'lyrics', 'words', 'vocalEvents', 'chords', 'key')


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

