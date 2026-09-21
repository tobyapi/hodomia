"""Voice event inference and throttled checkpoint progress."""
import time
from checkpoints import Cancelled


def vocal_events(start_progress, end_progress, audio, paths, models, device, duration, folder, options, checkpoint, result):
    cancelled, publish = checkpoint.cancelled, checkpoint.publish
    from vocal_events import detect
    last_update = 0.
    def update_progress(fraction):
        nonlocal last_update
        if cancelled():
            raise Cancelled()
        now = time.monotonic()
        if now - last_update >= 1 or fraction >= 1:
            publish(f'声の表現を検出 {round(fraction * 100)}%',
                    start_progress + fraction * (end_progress - start_progress))
            last_update = now
    rows, engine = detect(audio, paths.get('vocals'), models, device, duration, folder, options.get('eventSensitivity', 'standard'),
                          progress=update_progress, beatbox_recall=options.get('beatboxRecall', True))
    result['tracks']['vocalEvents'] = rows
    result['engines']['vocalEvents'] = engine
