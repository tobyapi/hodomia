"""Level and SDR measures of separated stems; arrays are (frames, channels)."""
import numpy as np

# Same stabilizer as utils/metrics.py in MSST, so values line up with the MVSEP leaderboards.
DELTA = 1e-7


def sdr(reference, estimate):
    """Global signal-to-distortion ratio in dB, as used by the MDX challenge and MVSEP."""
    if reference.shape != estimate.shape:
        raise ValueError('参照と推定の長さとチャンネル数が一致しません。')
    signal = np.sum(np.square(reference, dtype=np.float64))
    error = np.sum(np.square(reference.astype(np.float64) - estimate))
    return float(10 * np.log10((signal + DELTA) / (error + DELTA)))


def level_db(samples):
    """RMS level in dBFS, or None for digital silence."""
    rms = float(np.sqrt(np.mean(np.square(samples, dtype=np.float64))))
    return 20 * float(np.log10(rms)) if rms > 0 else None
