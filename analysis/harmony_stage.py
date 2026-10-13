"""Chord and key stage. BTC reads only the original audio, so it can run while stems are separated."""
import threading
from concurrent.futures import ThreadPoolExecutor
from checkpoints import Cancelled


class BackgroundChords:
    """BTC inference started early; the chord stage collects it, or the run stops it."""

    def __init__(self, audio, runtime, folder, duration, cancelled):
        self.abandoned = threading.Event()
        self.executor = ThreadPoolExecutor(max_workers=1)
        self.future = self.executor.submit(self._infer, audio, runtime, folder, duration, cancelled)

    def _infer(self, audio, runtime, folder, duration, cancelled):
        from chordmini import infer
        def check_cancel():
            if cancelled() or self.abandoned.is_set():
                raise Cancelled()
        return infer(audio, runtime, folder, duration, check_cancel)

    def result(self):
        return self.future.result()

    def stop(self):
        """Kill an uncollected inference and wait, so its process never outlives the run."""
        self.abandoned.set()
        self.executor.shutdown(wait=True)


def analyze_harmony(result, chords, paths, y, sr, duration):
    from dsp import accompaniment, estimate_key
    try:
        signal, source = accompaniment(paths, y, sr)
        # Estimating the key first overlaps it with whatever BTC inference remains.
        key = estimate_key(signal, sr, duration)
        rows, engine = chords.result()
    finally:
        # A failed key estimate must not leave BTC holding the GPU during later stages.
        chords.stop()
    result['tracks'].update(chords=rows, key=key)
    result.pop('chordComparisons', None)
    result['engines'].update(chords=engine, harmonySource=engine['source'], keySource=source)
