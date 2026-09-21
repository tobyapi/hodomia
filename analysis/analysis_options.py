"""Validate analysis requests before creating a run or launching a job."""
import math


def validate_options(options, duration):
    if not isinstance(options, dict) or set(options) - {'mode', 'scope', 'region', 'lyrics', 'eventSensitivity', 'beatboxRecall', 'chordBackend'}:
        raise ValueError('解析オプションが不正です。')
    if options.get('mode') not in ('multilingual', 'japanese', 'instrumental'):
        raise ValueError('解析モードが不正です。')
    if options.get('scope') not in (None, 'vocal-events', 'vocal-comparison', 'separation-comparison', 'harmony') or (options.get('scope') and options.get('region')):
        raise ValueError('解析の対象が不正です。')
    if options.get('chordBackend', 'chordmini-btc') != 'chordmini-btc':
        raise ValueError('コード推定はBTCのみ対応しています。')
    if options.get('eventSensitivity', 'standard') not in ('standard', 'sensitive'):
        raise ValueError('声の表現の検出感度が不正です。')
    if not isinstance(options.get('beatboxRecall', True), bool):
        raise ValueError('beatboxRecallは真偽値で指定してください。')
    if not isinstance(options.get('lyrics', ''), str) or len(options.get('lyrics', '')) > 100000:
        raise ValueError('歌詞は10万文字以内で指定してください。')
    region = options.get('region')
    if region is not None:
        if not isinstance(region, dict) or set(region) != {'start', 'end', 'language'}:
            raise ValueError('再解析区間が不正です。')
        if region['language'] not in ('ja', 'en') or any(type(region[k]) not in (float, int) or not math.isfinite(region[k]) for k in ('start', 'end')) or not 0 <= region['start'] < region['end'] <= duration:
            raise ValueError('再解析区間が不正です。')
