"""Vocal separation models compared against the analysis baseline, with their license status."""
from dataclasses import dataclass

MSST_REPOSITORY = 'https://github.com/ZFTurbo/Music-Source-Separation-Training.git'
MSST_COMMIT = '6fdad13686bb7e84d029ec66f9dbe76e65c93ebf'


@dataclass(frozen=True)
class Weights:
    url: str
    filename: str
    sha256: str


@dataclass(frozen=True)
class Candidate:
    id: str
    label: str
    # None means the distribution point states no license; such weights are fetched only on request.
    license: str | None
    license_source: str
    model_type: str | None = None
    config: str | None = None
    weights: Weights | None = None


BASELINE = Candidate(
    'htdemucs_ft', 'Demucs htdemucs_ft（解析と同じ設定）', 'MIT',
    'https://github.com/facebookresearch/demucs/blob/main/LICENSE')

CANDIDATES = (
    BASELINE,
    Candidate(
        'bs_roformer_viperx', 'BS-RoFormer viperx ep_317 sdr_12.9755', None,
        'https://github.com/TRvlvr/model_repo（LICENSEファイルもリリース上の記載もない）',
        'bs_roformer', 'configs/viperx/model_bs_roformer_ep_317_sdr_12.9755.yaml',
        Weights('https://github.com/TRvlvr/model_repo/releases/download/all_public_uvr_models/'
                'model_bs_roformer_ep_317_sdr_12.9755.ckpt',
                'model_bs_roformer_ep_317_sdr_12.9755.ckpt',
                '5b84f37e8d444c8cb30c79d77f613a41c05868ff9c9ac6c7049c00aefae115aa')),
    Candidate(
        'mel_roformer_kim', 'Mel-Band RoFormer Kimberley Jensen', 'MIT',
        'https://huggingface.co/KimberleyJSN/melbandroformer（モデルカードの license: mit）',
        'mel_band_roformer', 'configs/KimberleyJensen/config_vocals_mel_band_roformer_kj.yaml',
        Weights('https://huggingface.co/KimberleyJSN/melbandroformer/resolve/'
                'ac9b0614ab3cd7f77219e18ba494dfd93956c348/MelBandRoformer.ckpt',
                'MelBandRoformer.ckpt',
                '87201f4d31afb5bc79993230fc49446918425574db48c01c405e44f365c7559e')),
)


def by_id(identifier):
    return next(candidate for candidate in CANDIDATES if candidate.id == identifier)
