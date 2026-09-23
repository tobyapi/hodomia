"""Small synthetic WAV shared by macOS model smoke checks."""
import math
import struct
import wave


def write_tone(path, seconds=12, rate=22050):
    samples = (int(2000 * math.sin(2 * math.pi * 440 * index / rate))
               for index in range(seconds * rate))
    with wave.open(str(path), 'wb') as output:
        output.setnchannels(1)
        output.setsampwidth(2)
        output.setframerate(rate)
        output.writeframes(b''.join(struct.pack('<h', sample) for sample in samples))
