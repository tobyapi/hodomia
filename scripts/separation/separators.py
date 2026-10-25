"""Run one vocal separation model; every function returns vocals as (frames, channels)."""
import time


def measure(device, action):
    """Return the action's result with wall-clock seconds and peak CUDA memory in MiB."""
    import torch
    cuda = device == 'cuda'
    if cuda:
        torch.cuda.reset_peak_memory_stats()
    started = time.perf_counter()
    vocals = action()
    elapsed = time.perf_counter() - started
    return vocals, elapsed, torch.cuda.max_memory_allocated() / 2 ** 20 if cuda else None


def demucs_vocals(mix_path, folder, models, device):
    """The app's own separation call, so the baseline matches analysis exactly."""
    import soundfile as sf
    from engines import separate
    paths = separate(mix_path, folder, models, device)
    vocals, _ = sf.read(str(paths['vocals']), dtype='float32', always_2d=True)
    return vocals


def roformer_vocals(candidate, config_path, weights, mix, device, batch_size=None):
    """Inference through the pinned MSST checkout, which must already be on sys.path.

    Multi-stem models return every stem; only vocals are compared."""
    import numpy as np
    import torch
    from engines import release
    from utils.model_utils import demix
    from utils.settings import get_model_from_config
    model, config = get_model_from_config(candidate.model_type, str(config_path))
    # weights_only refuses pickled code; strict loading refuses a checkpoint that does not fit the config.
    model.load_state_dict(torch.load(weights, map_location='cpu', weights_only=True), strict=True)
    if batch_size:
        config.inference.batch_size = batch_size
    model = model.to(device).eval()
    try:
        separated = demix(config, model, mix.T, torch.device(device), candidate.model_type)
    finally:
        del model
        release()
    # soundfile writes only C-contiguous arrays, and the transpose of MSST's (channels, frames) is not.
    return np.ascontiguousarray(separated['vocals'].T, dtype=np.float32)
