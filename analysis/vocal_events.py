"""Vocal delivery and non-lexical candidates, independent from lyric recognition."""
from pathlib import Path
import numpy as np
from storage import row, write_json
from vocal_labels import CLASSES, CATEGORIES

MODEL_REPO = 'MIT/ast-finetuned-audioset-10-10-0.4593'
MODEL_REVISION = 'f826b80d28226b62986cc218e5cec390b1096902'
EVENTS = {
    'rap': ('ラップ', ('Rapping',)),
    'spoken': ('朗読・語り', ('Narration, monologue',)),
    **{key: (label, CLASSES[key]) for key, label in CATEGORIES.items()},
    'other': ('その他の非言語発声', ('Groan', 'Grunt', 'Whimper', 'Laughter')),
}
THRESHOLDS = {'standard': .15, 'sensitive': .06}
WINDOW = 2.0
HOP = .5


def candidates(frames, duration, sensitivity='standard'):
    """Keep simultaneous categories; a score is not a calibrated probability."""
    threshold = THRESHOLDS[sensitivity]
    rows = []
    for category, (label, _) in EVENTS.items():
        active = None
        for frame in [*frames, None]:
            evidence = frame['events'][category] if frame else None
            on = evidence is not None and evidence['score'] >= threshold
            if on:
                start, end = max(0., frame['time'] - WINDOW / 2), min(duration, frame['time'] + WINDOW / 2)
                if end <= start:
                    continue
                if active is None:
                    active = row('vocal-event', 0, start, end, label, category=category, detectedCategory=category,
                                 score=evidence['score'], evidenceSources=[evidence['source']],
                                 evidenceLabels=[evidence['class']], timingUncertainty=WINDOW / 2,
                                 warning='2秒の解析窓から得た候補範囲です。発声境界は未確定。試聴して時刻・分類を修正してください。')
                    if category in ('rap', 'spoken'):
                        active['warning'] += ' ラップ・朗読／語りの検出は実験的で、見逃しがあります。'
                else:
                    active['end'] = end
                    active['score'] = max(active['score'], evidence['score'])
                    active['evidenceSources'] = sorted(set(active['evidenceSources'] + [evidence['source']]))
                    active['evidenceLabels'] = sorted(set(active['evidenceLabels'] + [evidence['class']]))
            elif active:
                rows.append(active)
                active = None
    merged = []
    for item in sorted(rows, key=lambda r: (r['category'], r['start'])):
        if merged and item['category'] == merged[-1]['category'] and item['start'] <= merged[-1]['end']:
            previous = merged[-1]
            previous['end'] = max(previous['end'], item['end'])
            previous['score'] = max(previous['score'], item['score'])
            for field in ('evidenceSources', 'evidenceLabels'):
                previous[field] = sorted(set(previous[field] + item[field]))
        else:
            merged.append(item)
    rows = sorted(merged, key=lambda r: (r['start'], r['category']))
    for i, item in enumerate(rows):
        item['id'] = f'vocal-event-{i}'
        item['score'] = round(item['score'], 4)
    return rows


def detect(audio, vocal, models, device, duration, folder, sensitivity='standard', progress=None, beatbox_recall=True):
    import librosa
    import torch
    from transformers import ASTFeatureExtractor, ASTForAudioClassification
    if sensitivity not in THRESHOLDS:
        raise ValueError('声の表現の検出感度が不正です。')
    model_path = Path(models) / 'vocal-events'
    if not (model_path / 'model.safetensors').is_file():
        raise RuntimeError('声の表現モデルが未準備です。「環境を再確認・修復」を実行してください。')
    extractor = ASTFeatureExtractor.from_pretrained(str(model_path), local_files_only=True)
    model = ASTForAudioClassification.from_pretrained(str(model_path), local_files_only=True,
                                                     attn_implementation='sdpa').to(device).eval()
    labels = {label: int(index) for index, label in model.config.id2label.items()}
    for _, names in EVENTS.values():
        for name in names:
            if name not in labels:
                raise RuntimeError('音声分類モデルのラベルが想定と異なります: ' + name)
    sources = {'original': audio}
    if vocal:
        sources['vocals'] = vocal
    times = np.arange(0, duration, HOP)
    frames = [{'time': round(float(t), 4), 'events': {name: {'score': 0., 'source': 'original', 'class': ''}
                                                   for name in EVENTS}} for t in times]
    batch_size = 4 if device == 'cuda' else 1
    source_frames = {}
    for source_index, (source, path) in enumerate(sources.items()):
        source_frames[source] = [{'start': max(0., round(float(t) - WINDOW / 2, 4)),
                                  'end': min(duration, round(float(t) + WINDOW / 2, 4)),
                                  'scores': {category: 0. for category in CLASSES}, 'classScores': {name: 0. for names in CLASSES.values() for name in names}}
                                 for t in times]
        samples, sr = librosa.load(str(path), sr=16000, mono=True)
        for offset in range(0, len(times), batch_size):
            indices = list(range(offset, min(offset + batch_size, len(times))))
            clips, audible = [], []
            for index in indices:
                left = int((times[index] - WINDOW / 2) * sr)
                right = left + int(WINDOW * sr)
                clip = samples[max(0, left):min(len(samples), right)]
                energy = float(np.sqrt(np.mean(clip * clip))) if len(clip) else 0.
                audible.append(energy >= .001)
                clips.append(np.pad(clip, (max(0, -left), max(0, right - len(samples)))))
            if any(audible):
                inputs = extractor(clips, sampling_rate=sr, return_tensors='pt').to(device)
                with torch.inference_mode():
                    # AudioSet is multi-label: softmax would force unrelated sounds to compete.
                    scores = model(**inputs).logits.sigmoid().cpu().numpy()
                for index, values, is_audible in zip(indices, scores, audible):
                    if not is_audible:
                        continue
                    source_frames[source][index]['classScores'] = {name: float(values[labels[name]]) for names in CLASSES.values() for name in names}
                    source_frames[source][index]['scores'] = {category: max(float(values[labels[name]]) for name in names) for category, names in CLASSES.items()}
                    for category, (_, names) in EVENTS.items():
                        name = max(names, key=lambda name: values[labels[name]])
                        score = float(values[labels[name]])
                        if score > frames[index]['events'][category]['score']:
                            frames[index]['events'][category] = {'score': score, 'source': source, 'class': name}
            if progress:
                progress((source_index + (indices[-1] + 1) / len(times)) / len(sources))
    engine = {'model': MODEL_REPO, 'revision': MODEL_REVISION, 'windowSeconds': WINDOW, 'hopSeconds': HOP,
              'sensitivity': sensitivity, 'threshold': THRESHOLDS[sensitivity], 'sources': list(sources),
              'categories': list(EVENTS),
              'notice': '短い窓での分類候補。ラップと語りは重複する場合があります。朗読・語りはNarration, monologueに基づく候補で、詩の内容の判定ではありません。歌詞を削除しません。'}
    rows = candidates(frames, duration, sensitivity)
    if beatbox_recall:
        from vocal_percussion import detect as percussion
        rows.extend(percussion(vocal, duration, rows))
        rows.sort(key=lambda item: item['start'])
    engine['vocalPercussion'] = bool(beatbox_recall and vocal)
    write_json(Path(folder) / 'vocal-events-evidence.json', {'engine': engine, 'frames': frames, 'sourceFrames': source_frames})
    return rows, engine
