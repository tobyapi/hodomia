"""Compare independent model/source evidence without replacing saved annotations."""
import math
from pathlib import Path
from storage import row, read_json, write_json
from vocal_labels import CATEGORIES


def intervals(frames, category, onset, offset):
    """Hysteresis over model windows, not precise acoustic boundaries."""
    if category not in CATEGORIES or not all(isinstance(v, (int, float)) and math.isfinite(v) for v in (onset, offset)) or not 0 < offset <= onset <= 1:
        raise ValueError('しきい値は0より大きく、継続≦開始≦1で指定してください。')
    result, active = [], None
    for frame in frames:
        score = frame['scores'][category]
        if score >= (offset if active else onset):
            if active is None:
                active = {'start': frame['start'], 'end': frame['end'], 'score': score}
            else:
                active['end'] = max(active['end'], frame['end'])
                active['score'] = max(active['score'], score)
        elif active:
            result.append(active)
            active = None
    if active:
        result.append(active)
    merged = []
    for item in result:
        if merged and item['start'] <= merged[-1]['end']:
            merged[-1]['end'] = max(merged[-1]['end'], item['end'])
            merged[-1]['score'] = max(merged[-1]['score'], item['score'])
        else:
            merged.append(item)
    return merged


def variant(model, source, frames, window, hop, onset, offset):
    thresholds = {category: {'onset': onset, 'offset': offset} for category in CATEGORIES}
    rows = []
    for category, label in CATEGORIES.items():
        for item in intervals(frames, category, onset, offset):
            rows.append(row(f'{model}-{source}', len(rows), item['start'], item['end'], label,
                            category=category, score=item['score'], evidenceSources=[source],
                            method=model, timingUncertainty=window / 2,
                            warning='分類窓が支持する候補範囲です。正確な発声境界・正解率ではありません。'))
    return dict(id=f'{model}-{source}', model=model, source=source, windowSeconds=window,
                hopSeconds=hop, thresholds=thresholds, frames=frames, candidates=sorted(rows, key=lambda r: r['start']))


def compare(audio, vocal, models, device, runtime, duration, folder, sensitivity, progress):
    from vocal_events import detect, WINDOW, HOP, THRESHOLDS
    from engines import release
    from yamnet import infer
    _, ast_engine = detect(audio, vocal, models, device, duration, folder, sensitivity,
                           progress=lambda f: progress(f * .7), beatbox_recall=False)
    evidence = read_json(Path(folder) / 'vocal-events-evidence.json')
    variants = [variant('ast', source, frames, WINDOW, HOP, THRESHOLDS[sensitivity], THRESHOLDS[sensitivity])
                for source, frames in evidence['sourceFrames'].items()]
    release()
    sources = {'original': audio, **({'vocals': vocal} if vocal else {})}
    yamnet_result = infer(sources, runtime, folder, duration, lambda: progress(.7))
    for source, frames in yamnet_result['sources'].items():
        variants.append(variant('yamnet', source, frames, .975, .48, .15, .1))
    result = dict(schemaVersion=1, runId=Path(folder).name, duration=duration, variants=variants, engines={'ast': ast_engine, 'yamnet': yamnet_result['engine']},
                  notice='未校正スコアの比較です。モデル間の値は同じ正解率を表しません。YAMNetの開始0.15・継続0.10は仮の基準です。通常の声の表現・手修正は変更しません。')
    write_json(Path(folder) / 'vocal-comparison.json', result)
    progress(1)
    return result
