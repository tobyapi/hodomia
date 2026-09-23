"""Explicit online setup. No media or lyrics are accepted by this command."""
import argparse
import json
import os
import hashlib
import subprocess
from pathlib import Path
from vocal_events import MODEL_REPO, MODEL_REVISION


def prepare_vocal_events(runtime):
    from huggingface_hub import snapshot_download
    print('Download: vocal expression classifier', flush=True)
    snapshot_download(MODEL_REPO, revision=MODEL_REVISION, local_dir=str(runtime / 'models' / 'vocal-events'),
                      allow_patterns=['config.json', 'preprocessor_config.json', 'model.safetensors'])


def prepare(runtime):
    (runtime / 'ready.json').unlink(missing_ok=True)
    from huggingface_hub import snapshot_download
    import nltk
    import torch
    from demucs.pretrained import get_model
    from beat_this.inference import File2Beats

    models = runtime / 'models'
    models.mkdir(parents=True, exist_ok=True)
    torch.hub.set_dir(str(models / 'torch'))
    os.environ['HF_HOME'] = str(models / 'huggingface')
    for name, repo in [
        ('large-v3', 'Systran/faster-whisper-large-v3'),
        ('japanese', 'jonatasgrosman/wav2vec2-large-xlsr-53-japanese'),
        ('english', 'jonatasgrosman/wav2vec2-large-xlsr-53-english'),
    ]:
        print(f'Download: {name}', flush=True)
        snapshot_download(repo, local_dir=str(models / name),
                          allow_patterns=['*.json', 'model.bin', 'vocabulary.*', '*.safetensors', 'pytorch_model.bin'])
    print('Download: htdemucs_ft', flush=True)
    get_model('htdemucs_ft')
    print('Download: Beat This', flush=True)
    checkpoint = models / 'torch' / 'checkpoints' / 'beat_this-final0.ckpt'
    if not checkpoint.exists():
        subprocess.run(['curl', '--fail', '--location', '--retry', '3', '--output', str(checkpoint),
                        'https://cloud.cp.jku.at/public.php/dav/files/7ik4RrBKTS273gp/final0.ckpt'], check=True)
    with checkpoint.open('rb') as stream:
        if hashlib.file_digest(stream, 'sha256').hexdigest() != '8c328b45f59d8dd3dff219253ff6a8d6482be57d0133a29140e2febbf8eb8331':
            checkpoint.unlink()
            raise RuntimeError('Beat This model checksum mismatch; run setup again')
    File2Beats(checkpoint_path=str(checkpoint), device='cpu', dbn=False)
    print('Download: All-In-One harmonix ensemble', flush=True)
    snapshot_download('taejunkim/allinone', cache_dir=str(models / 'allin1'), allow_patterns=['*.pth'])
    prepare_vocal_events(runtime)
    if not nltk.download('punkt_tab', download_dir=str(models / 'nltk'), quiet=True):
        raise RuntimeError('NLTK tokenizer download failed')
    manifest = {'schemaVersion': 1, 'asr': 'large-v3', 'alignment': ['ja', 'en'],
                'separation': 'htdemucs_ft', 'beats': 'final0', 'structure': 'harmonix-all',
                'vocalEvents': MODEL_REVISION, 'cudaAvailable': torch.cuda.is_available(), 'torch': torch.__version__}
    (runtime / 'ready.json').write_text(json.dumps(manifest, indent=2), encoding='utf-8')
    print(json.dumps(manifest), flush=True)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--runtime', type=Path, required=True)
    parser.add_argument('--vocal-events-only', action='store_true')
    args = parser.parse_args()
    runtime = args.runtime.resolve()
    if args.vocal_events_only:
        from storage import read_json, write_json
        ready = read_json(runtime / 'ready.json')
        prepare_vocal_events(runtime)
        ready['vocalEvents'] = MODEL_REVISION
        write_json(runtime / 'ready.json', ready)
    else:
        prepare(runtime)
