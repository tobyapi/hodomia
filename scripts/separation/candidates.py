"""Vocal separation models compared against the analysis baseline, with their license status."""
from dataclasses import dataclass

MSST_REPOSITORY = 'https://github.com/ZFTurbo/Music-Source-Separation-Training.git'
MSST_COMMIT = '6fdad13686bb7e84d029ec66f9dbe76e65c93ebf'


@dataclass(frozen=True)
class Download:
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
    # A path inside the pinned MSST checkout, or a Download for configs published only with a release.
    config: str | Download | None = None
    weights: Download | None = None


BASELINE = Candidate(
    'htdemucs_ft', 'Demucs htdemucs_ft（解析と同じ設定）', 'MIT',
    'https://github.com/facebookresearch/demucs/blob/main/LICENSE')

CANDIDATES = (
    BASELINE,
    Candidate(
        'bs_roformer_viperx', 'BS-RoFormer viperx ep_317 sdr_12.9755', None,
        'https://github.com/TRvlvr/model_repo（LICENSEファイルもリリース上の記載もない）',
        'bs_roformer', 'configs/viperx/model_bs_roformer_ep_317_sdr_12.9755.yaml',
        Download('https://github.com/TRvlvr/model_repo/releases/download/all_public_uvr_models/'
                 'model_bs_roformer_ep_317_sdr_12.9755.ckpt',
                 'model_bs_roformer_ep_317_sdr_12.9755.ckpt',
                 '5b84f37e8d444c8cb30c79d77f613a41c05868ff9c9ac6c7049c00aefae115aa')),
    Candidate(
        'bs_roformer_zfturbo_4stem', 'BS-RoFormer ZFTurbo 4分離 ep_17 sdr_9.6568', None,
        'https://github.com/ZFTurbo/Music-Source-Separation-Training/releases/tag/v1.0.12'
        '（リポジトリはMITだが重みの記載はない。学習データはMUSDB18HQのみ）',
        'bs_roformer',
        Download('https://github.com/ZFTurbo/Music-Source-Separation-Training/releases/download/v1.0.12/'
                 'config_bs_roformer_384_8_2_485100.yaml',
                 'config_bs_roformer_384_8_2_485100.yaml',
                 'd8afb980318d0c08b9c2e24a7adc00d4f3150320c127a7e4de861800d1321939'),
        Download('https://github.com/ZFTurbo/Music-Source-Separation-Training/releases/download/v1.0.12/'
                 'model_bs_roformer_ep_17_sdr_9.6568.ckpt',
                 'model_bs_roformer_ep_17_sdr_9.6568.ckpt',
                 '3e9daecd70aaed5b5a0d1f861cc4d77eaa45afb3fc6301b1cf32c1be0f5868fb')),
    Candidate(
        'mel_roformer_kim', 'Mel-Band RoFormer Kimberley Jensen', 'MIT',
        'https://huggingface.co/KimberleyJSN/melbandroformer（モデルカードの license: mit）',
        'mel_band_roformer', 'configs/KimberleyJensen/config_vocals_mel_band_roformer_kj.yaml',
        Download('https://huggingface.co/KimberleyJSN/melbandroformer/resolve/'
                 'ac9b0614ab3cd7f77219e18ba494dfd93956c348/MelBandRoformer.ckpt',
                 'MelBandRoformer.ckpt',
                 '87201f4d31afb5bc79993230fc49446918425574db48c01c405e44f365c7559e')),
)


def by_id(identifier):
    return next(candidate for candidate in CANDIDATES if candidate.id == identifier)
