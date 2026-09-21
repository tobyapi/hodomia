"""Online-only preparation of the pinned official YAMNet SavedModel."""
import csv
import shutil
import sys
import tarfile
import tempfile
import urllib.request
from pathlib import Path
from storage import write_json
from yamnet import MODEL_URL, ARCHIVE_SHA256, digest, verify
from vocal_labels import CLASSES


def install(home):
    home = Path(home).resolve()
    home.mkdir(parents=True, exist_ok=True)
    archive = home / 'model-v1.tar.gz'
    if not archive.exists() or digest(archive) != ARCHIVE_SHA256:
        with urllib.request.urlopen(MODEL_URL, timeout=120) as response, archive.open('wb') as stream:
            shutil.copyfileobj(response, stream)
    if digest(archive) != ARCHIVE_SHA256:
        raise ValueError('公式YAMNet v1のモデルハッシュが一致しません。')
    if not (home / 'model').exists():
        with tempfile.TemporaryDirectory(dir=home) as staging:
            with tarfile.open(archive) as bundle:
                for member in bundle.getmembers():
                    destination = (Path(staging) / member.name).resolve()
                    if not destination.is_relative_to(Path(staging)) or not (member.isdir() or member.isfile()):
                        raise ValueError('モデルアーカイブに不正なパスがあります。')
                bundle.extractall(staging)
            Path(staging).rename(home / 'model')
    files = {str(path.relative_to(home)).replace('\\', '/'): digest(path) for path in (home / 'model').rglob('*') if path.is_file()}
    # Confirm extracted bytes match the pinned archive, including on repair runs.
    with tarfile.open(archive) as bundle:
        for member in bundle.getmembers():
            if member.isfile():
                import hashlib
                if files.get('model/' + member.name) != hashlib.sha256(bundle.extractfile(member).read()).hexdigest():
                    raise ValueError('保存済みYAMNetモデルが公式アーカイブと一致しません。')
    import tensorflow as tf
    import numpy as np
    model = tf.saved_model.load(str(home / 'model'))
    scores, _, _ = model(tf.zeros([16000], dtype=tf.float32))
    if scores.shape[1] != 521 or not np.isfinite(scores.numpy()).all():
        raise ValueError('YAMNetの動作確認に失敗しました。')
    with (home / 'model/assets/yamnet_class_map.csv').open(encoding='utf-8') as stream:
        labels = {r['display_name'] for r in csv.DictReader(stream)}
    if any(name not in labels for names in CLASSES.values() for name in names):
        raise ValueError('YAMNetの分類ラベルが不足しています。')
    write_json(home / 'installation.json', {'modelUrl': MODEL_URL, 'archiveSha256': ARCHIVE_SHA256, 'tensorflow': tf.__version__, 'files': files})
    verify(home)
    print('YAMNetの準備とローカル推論確認が完了しました。')


if __name__ == '__main__':
    install(sys.argv[1])
