"""Explicit resource handles for generated files, never an arbitrary file reader."""
import base64
import uuid
from pathlib import Path
from control_errors import ControlError
from storage import read_json, within, write_json


class Artifacts:
    def __init__(self, runtime):
        self.folder = Path(runtime) / 'control/artifacts'

    def register(self, root, path, mime):
        root, path = Path(root).resolve(), Path(path).resolve()
        relative = path.relative_to(root).as_posix()
        artifact_id = uuid.uuid4().hex
        self.folder.mkdir(parents=True, exist_ok=True)
        write_json(self.folder / (artifact_id + '.json'), dict(root=str(root), path=relative, mimeType=mime))
        return dict(artifactId=artifact_id, uri='music-sweeper://artifact/' + artifact_id, path=str(path), mimeType=mime)

    def read(self, artifact_id, authorize):
        if not isinstance(artifact_id, str) or len(artifact_id) != 32 or any(c not in '0123456789abcdef' for c in artifact_id):
            raise ValueError('artifactIdが不正です。')
        value = read_json(self.folder / (artifact_id + '.json'))
        root = authorize(value['root'])
        path = within(root, value['path'])
        if path.stat().st_size > 16_000_000:
            raise ControlError('TOO_LARGE', 'ファイルが大きすぎます。時間範囲を絞って取得してください。')
        data = path.read_bytes()
        result = dict(uri='music-sweeper://artifact/' + artifact_id, mimeType=value['mimeType'])
        if value['mimeType'] == 'audio/wav':
            result['blob'] = base64.b64encode(data).decode('ascii')
        else:
            result['text'] = data.decode('utf-8-sig')
        return result
