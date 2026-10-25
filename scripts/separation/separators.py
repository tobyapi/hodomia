"""Run one separation model; every function returns hodomia stems as (frames, channels) arrays."""
import time


def measure(device, action):
    """Return the action's result with wall-clock seconds and peak CUDA memory in MiB.

    Allocated memory is what tensors used; reserved memory is what the allocator kept from the GPU."""
    import torch
    cuda = device == 'cuda'
    if cuda:
        torch.cuda.reset_peak_memory_stats()
    started = time.perf_counter()
    stems = action()
    elapsed = time.perf_counter() - started
    if not cuda:
        return stems, elapsed, None, None
    return stems, elapsed, torch.cuda.max_memory_allocated() / 2 ** 20, torch.cuda.max_memory_reserved() / 2 ** 20


def app_stems(mix_path, folder, runtime, device, python):
    """The app's own separation, run by the analysis Python, so the baseline matches analysis exactly."""
    import soundfile as sf
    from separation import separate
    paths = separate(mix_path, folder, runtime, device, python=python)
    return {name: sf.read(str(path), dtype='float32', always_2d=True)[0] for name, path in paths.items()}


def roformer_stems(candidate, config_path, weights, mix, device, batch_size=None):
    """Inference through the pinned MSST checkout, which must already be on sys.path.

    Only the outputs listed in candidate.stems are returned, renamed to hodomia's stem names."""
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
    return {stem: np.ascontiguousarray(separated[output].T, dtype=np.float32) for stem, output in candidate.stems}
