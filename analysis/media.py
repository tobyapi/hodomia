"""Decode all supported containers to one stereo clock using PyAV."""
from pathlib import Path


def decode(source, output):
    import av
    import numpy as np
    import soundfile as sf
    rate = 44100
    count = 0
    with av.open(str(source)) as container, sf.SoundFile(str(output), mode='w', samplerate=rate, channels=2, subtype='PCM_24') as target:
        if not container.streams.audio:
            raise ValueError('音声トラックがありません。')
        resampler = av.AudioResampler(format='fltp', layout='stereo', rate=rate)
        for frame in container.decode(container.streams.audio[0]):
            for converted in resampler.resample(frame):
                count += converted.samples
                if count > rate * 900:
                    raise ValueError('初期版は15分以内の曲に対応しています。')
                samples = converted.to_ndarray().T
                if not np.isfinite(samples).all():
                    raise ValueError('音声に不正なサンプルがあります。')
                target.write(samples)
        for converted in resampler.resample(None):
            count += converted.samples
            target.write(converted.to_ndarray().T)
    if count < rate // 10 or count > rate * 900:
        raise ValueError('曲の長さは0.1秒から15分までにしてください。')
    return count / rate
