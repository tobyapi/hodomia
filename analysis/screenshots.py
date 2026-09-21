"""Request a PNG from the running desktop app; never select other windows."""
import base64
import time
import uuid
from pathlib import Path
from control_errors import ControlError
from storage import read_json, write_json


def capture(runtime, timeoutSeconds=10):
    if isinstance(timeoutSeconds, bool) or not isinstance(timeoutSeconds, (int, float)) or not 1 <= timeoutSeconds <= 30:
        raise ValueError('timeoutSecondsは1〜30秒で指定してください。')
    folder = Path(runtime) / 'control/screenshots'
    folder.mkdir(parents=True, exist_ok=True)
    request_id = uuid.uuid4().hex
    request = folder / (request_id + '.request.json')
    response = folder / (request_id + '.response.json')
    png = folder / (request_id + '.png')
    deadline = time.monotonic() + timeoutSeconds
    write_json(request, {'expiresAt': time.time() + timeoutSeconds})
    try:
        while time.monotonic() < deadline:
            if response.exists():
                return read_capture(response, png, request_id)
            time.sleep(0.1)
        raise ControlError('GUI_TIMEOUT', 'GUIから撮影結果を受信できません。同じruntimeのhodomiaを開いてください。')
    finally:
        request.unlink(missing_ok=True)
        response.unlink(missing_ok=True)


def read_capture(response, png, request_id):
    value = read_json(response)
    if not value['ok']:
        raise ControlError('CAPTURE_FAILED', value['message'])
    if png.stat().st_size > 16_000_000:
        raise ControlError('TOO_LARGE', '画像が大きすぎます。ウィンドウを小さくしてください。')
    data = png.read_bytes()
    if not data.startswith(b'\x89PNG\r\n\x1a\n'):
        raise ControlError('CAPTURE_FAILED', '撮影結果がPNGではありません。')
    return dict(captureId=request_id, path=str(png.resolve()), mimeType='image/png',
                width=value['width'], height=value['height'], blob=base64.b64encode(data).decode('ascii'))
