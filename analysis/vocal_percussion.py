"""High-recall vocal percussion proposals; not a semantic beatboxing classifier."""
import numpy as np
from storage import row


def onset_regions(times, duration):
    groups = []
    for time in times:
        if not groups or time - groups[-1][-1] > 1.0:
            groups.append([float(time)])
        else:
            groups[-1].append(float(time))
    return [(max(0., group[0] - .12), min(duration, group[-1] + .3)) for group in groups if len(group) >= 2]


def detect(vocal, duration, existing):
    if not vocal:
        return []
    import librosa
    samples, sr = librosa.load(str(vocal), sr=16000, mono=True)
    if not len(samples) or np.max(np.abs(samples)) < .005:
        return []
    hop = 256
    _, percussive = librosa.effects.hpss(samples, margin=(2., 2.))
    rms = librosa.feature.rms(y=samples, hop_length=hop)[0]
    percussion_rms = librosa.feature.rms(y=percussive, hop_length=hop)[0]
    envelope = librosa.onset.onset_strength(y=percussive, sr=sr, hop_length=hop)
    onsets = librosa.onset.onset_detect(onset_envelope=envelope, sr=sr, hop_length=hop, units='frames')
    level = max(.003, float(np.quantile(rms, .75)) * .18)
    times = [float(frame * hop / sr) for frame in onsets if frame < len(rms)
             and rms[frame] >= level and percussion_rms[frame] / max(rms[frame], 1e-8) >= .25]
    covered = [(r['start'], r['end']) for r in existing if r['category'] == 'beatbox']
    result = []
    for start, end in onset_regions(times, duration):
        pieces = [(start, end)]
        for left, right in covered:
            next_pieces = []
            for a, b in pieces:
                if b <= left or a >= right:
                    next_pieces.append((a, b))
                else:
                    if a < left: next_pieces.append((a, left))
                    if b > right: next_pieces.append((right, b))
            pieces = next_pieces
        for a, b in pieces:
            if b - a < .2:
                continue
            result.append(row('vocal-percussion', len(result), a, b, 'ビートボックス候補', category='beatbox',
                              method='vocal-percussion', evidenceSources=['vocals'], timingUncertainty=.3,
                              warning='補助検出：分離ボーカル中の連続した打撃音です。ラップの子音・ブレス・楽器漏れも含み得ます。ビートボックスか試聴して確認してください。'))
    return result
