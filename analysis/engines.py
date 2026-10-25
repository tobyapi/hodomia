"""Locally cached neural inference, loaded one model at a time."""
import gc
import os
from pathlib import Path

# Every label in allin1_infer.config.HARMONIX_LABELS, shown in Japanese.
SECTION_LABELS = {'intro': 'イントロ', 'verse': 'ヴァース', 'chorus': 'サビ', 'bridge': 'ブリッジ',
                  'outro': 'アウトロ', 'inst': 'インスト', 'break': 'ブレイク', 'start': '開始', 'end': '終了',
                  'solo': 'ソロ'}


def configure(runtime):
    import torch
    models = Path(runtime) / 'models'
    os.environ.update(HF_HUB_OFFLINE='1', TRANSFORMERS_OFFLINE='1', HF_HUB_DISABLE_TELEMETRY='1')
    torch.hub.set_dir(str(models / 'torch'))
    torch.set_num_threads(min(8, os.cpu_count() or 1))
    return models, 'cuda' if torch.cuda.is_available() else 'cpu'


def release():
    import torch
    gc.collect()
    if torch.cuda.is_available():
        torch.cuda.empty_cache()


def beats(audio, models, device):
    from beat_this.inference import File2Beats
    checkpoint = models / 'torch' / 'hub' / 'checkpoints' / 'beat_this-final0.ckpt'
    if not checkpoint.exists():
        checkpoint = models / 'torch' / 'checkpoints' / 'beat_this-final0.ckpt'
    if not checkpoint.is_file():
        raise RuntimeError('拍モデルが未準備です。初回セットアップを実行してください。')
    tracker = File2Beats(checkpoint_path=str(checkpoint), device=device, dbn=False)
    beat_times, downbeats = tracker(str(audio))
    del tracker
    release()
    return [float(t) for t in beat_times], [float(t) for t in downbeats]


def sections(paths, folder, models, device, duration):
    import torch
    from allin1_infer.models import load_pretrained_model
    from allin1_infer.spectrogram import extract_spectrograms
    from allin1_infer.helpers import run_inference
    from storage import row
    model = load_pretrained_model('harmonix-all', cache_dir=models / 'allin1', device=device)
    spectra = extract_spectrograms([paths['bass'].parent], folder / 'spectrograms', multiprocess=False)
    with torch.inference_mode():
        result = run_inference(path=paths['bass'], spec_path=spectra[0], model=model,
                               device=device, include_activations=False, include_embeddings=False)
    rows = [row('section', i, max(0, float(s.start)), min(duration, float(s.end)), SECTION_LABELS.get(s.label, s.label),
                warning='モデル推定・区間名と境界は試聴して確認してください。')
            for i, s in enumerate(result.segments) if s.start < min(duration, s.end)]
    del model, result
    release()
    return rows
