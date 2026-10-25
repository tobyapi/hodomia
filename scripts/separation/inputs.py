"""Load the song and an optional reference vocal stem as aligned 44.1 kHz stereo arrays."""
from pathlib import Path

RATE = 44100


def excerpt(samples, start, duration):
    """Cut [start, start + duration) seconds; duration None keeps the rest of the song."""
    first = round(start * RATE)
    if first < 0 or first >= len(samples):
        raise ValueError('開始位置が曲の範囲外です。')
    if duration is None:
        return samples[first:]
    if duration <= 0:
        raise ValueError('区間の長さは0より大きくしてください。')
    return samples[first:first + round(duration * RATE)]


def read(path):
    import soundfile as sf
    samples, rate = sf.read(str(path), dtype='float32', always_2d=True)
    if rate != RATE or samples.shape[1] != 2:
        raise ValueError(f'{Path(path).name}: 44.1 kHzステレオの音声が必要です。')
    return samples


def decoded_song(song, folder):
    """hodomia project folders already hold the decoded PCM that analysis uses."""
    if song.is_dir():
        audio = song / 'audio.wav'
        if not audio.is_file():
            raise FileNotFoundError('プロジェクトフォルダーに audio.wav がありません。')
        return audio
    from media import decode
    target = folder / 'decoded.wav'
    decode(song, target)
    return target


def prepare(song, folder, start, duration, reference_path):
    """Write the compared excerpt to mix.wav and return it with the matching reference."""
    import soundfile as sf
    mix = excerpt(read(decoded_song(song, folder)), start, duration)
    mix_path = folder / 'mix.wav'
    sf.write(str(mix_path), mix, RATE, subtype='FLOAT')
    if reference_path is None:
        return mix_path, mix, None
    reference = excerpt(read(reference_path), start, duration)
    if reference.shape != mix.shape:
        raise ValueError('参照ボーカルと曲の長さが一致しません。同じミックスから書き出したWAVを指定してください。')
    return mix_path, mix, reference
