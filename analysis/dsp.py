"""Signal-derived features. Heuristic estimates are explicitly labelled."""
import numpy as np
from storage import row

NOTES = ['C', 'C#', 'D', 'D#', 'E', 'F', 'F#', 'G', 'G#', 'A', 'A#', 'B']


def series(values, rate, stride=1):
    return [{'time': round(i * rate, 4), 'value': float(v) if np.isfinite(v) else None}
            for i, v in enumerate(values) if i % stride == 0]


def basics(path):
    import librosa
    y, sr = librosa.load(str(path), sr=22050, mono=True)
    hop = 512
    rms = librosa.feature.rms(y=y, hop_length=hop)[0]
    onset = librosa.onset.onset_strength(y=y, sr=sr, hop_length=hop)
    peak = max(float(np.max(np.abs(y))), 1e-8)
    waveform = [float(np.max(np.abs(block))) / max(1.0, peak) for block in np.array_split(y, min(len(y), 4000))]
    from scipy.ndimage import gaussian_filter1d
    envelope = gaussian_filter1d(rms, 22050 / hop * 1.5)
    lo, hi = np.quantile(envelope, [.05, .95])
    energy = np.clip((envelope - lo) / max(hi - lo, 1e-8), 0, 1)
    return y, sr, {'waveform': waveform, 'energy': series(energy, hop / sr, 10),
                    'peak': peak, 'silence': bool(peak < 1e-5)}, onset


def harmony(y, sr, duration, beats):
    import librosa
    from scipy.ndimage import median_filter
    harmonic = librosa.effects.harmonic(y, margin=3)
    chroma = librosa.feature.chroma_cqt(y=harmonic, sr=sr, hop_length=1024)
    chroma = median_filter(chroma, size=(1, 9))
    templates, labels = [], []
    for root in range(12):
        for suffix, intervals in [('', [0, 4, 7]), ('m', [0, 3, 7])]:
            template = np.full(12, -.25)
            template[[(root + i) % 12 for i in intervals]] = 1
            templates.append(template / np.linalg.norm(template))
            labels.append(NOTES[root] + suffix)
    boundaries = sorted(set([0.0] + [float(t) for t in beats if 0 < t < duration] + [duration]))
    if len(boundaries) < 3:
        boundaries = list(np.arange(0, duration, 1.0)) + [duration]
    observations = []
    for a, b in zip(boundaries[:-1], boundaries[1:]):
        left, right = int(a * sr / 1024), max(int(b * sr / 1024), int(a * sr / 1024) + 1)
        frame = chroma[:, left:right].mean(axis=1)
        norm = np.linalg.norm(frame)
        scores = np.array(templates) @ (frame / max(norm, 1e-8))
        observations.append((a, b, scores, norm))
    # Penalize brief chord flips; keep genuine changes possible at each beat.
    scores = np.array([item[2] for item in observations])
    costs = scores[0].copy()
    back = []
    transition = np.full((len(labels), len(labels)), -.22)
    np.fill_diagonal(transition, 0)
    for frame in scores[1:]:
        candidates = costs[:, None] + transition
        parents = np.argmax(candidates, axis=0)
        back.append(parents)
        costs = candidates[parents, np.arange(len(labels))] + frame
    states = [int(np.argmax(costs))]
    for parents in reversed(back):
        states.append(int(parents[states[-1]]))
    states.reverse()
    chords = []
    for (a, b, _, norm), state in zip(observations, states):
        label = labels[state] if norm > .01 else 'N'
        if chords and chords[-1]['label'] == label:
            chords[-1]['end'] = b
        else:
            chords.append(row('chord', len(chords), a, b, label, warning='CQT・長短三和音の推定。7th等の拡張音は手動確認。'))
    average = chroma.mean(axis=1)
    major = np.array([6.35, 2.23, 3.48, 2.33, 4.38, 4.09, 2.52, 5.19, 2.39, 3.66, 2.29, 2.88])
    minor = np.array([6.33, 2.68, 3.52, 5.38, 2.60, 3.53, 2.54, 4.75, 3.98, 2.69, 3.34, 3.17])
    candidates = [(float(np.corrcoef(average, np.roll(profile, root))[0, 1]), NOTES[root] + suffix)
                  for root in range(12) for suffix, profile in [(' major', major), (' minor', minor)]]
    candidates = [(score, label) for score, label in candidates if np.isfinite(score)]
    key = max(candidates)[1] if candidates and np.std(average) > .01 else '未確定'
    return {'chords': chords, 'key': [row('key', 0, 0, duration, key, warning='曲全体の調性候補・転調は手動で区間を追加')]}




def pitch(path, instrumental=False):
    import librosa
    y, sr = librosa.load(str(path), sr=16000, mono=True)
    values = []
    # Bound pYIN's memory footprint and keep all offsets on the original clock.
    for offset in range(0, len(y), sr * 20):
        block = y[offset:offset + sr * 20]
        if len(block) < 2048:
            break
        f0, voiced, probability = librosa.pyin(block, fmin=65, fmax=1600, sr=sr, hop_length=256)
        for i in range(0, len(f0), 3):
            value = float(librosa.hz_to_midi(f0[i])) if voiced[i] and probability[i] > .3 and np.isfinite(f0[i]) else None
            values.append({'time': (offset + i * 256) / sr, 'value': value})
    return {'points': values, 'warning': 'インストの複音では主旋律を特定できないことがあります。' if instrumental else 'ボーカルの推定音高。ハモリ・伸ばし音は要確認。'}


def stem_activity(path, name, duration):
    import soundfile as sf
    samples, sr = sf.read(str(path), always_2d=True)
    mono = samples.mean(axis=1)
    window = sr // 2
    levels = np.array([np.sqrt(np.mean(b * b)) for b in np.array_split(mono, max(1, len(mono) // window))])
    maximum = float(np.max(levels))
    active = levels > max(.002, maximum * .08)
    rows, start = [], None
    step = duration / len(levels)
    for i, on in enumerate(list(active) + [False]):
        if on and start is None:
            start = i * step
        if not on and start is not None:
            if i * step - start >= .5:
                rows.append(row(name, len(rows), start, min(i * step, duration), name, warning='分離音声の相対音量から推定'))
            start = None
    return {'regions': rows, 'levels': series(levels / max(maximum, 1e-8), step)}
