"""Separation models compared against the analysis baseline, with their license status."""
from dataclasses import dataclass

MSST_REPOSITORY = 'https://github.com/ZFTurbo/Music-Source-Separation-Training.git'
MSST_COMMIT = '6fdad13686bb7e84d029ec66f9dbe76e65c93ebf'
MSST_RELEASES = 'https://github.com/ZFTurbo/Music-Source-Separation-Training/releases/download/'

# Stems that hodomia analysis reads, in the order All-In-One stacks them.
STEMS = ('bass', 'drums', 'other', 'vocals')
# (hodomia stem, model output) pairs for the usual four-stem models.
FOUR_STEMS = tuple((name, name) for name in STEMS)


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
    # Usable outputs as (hodomia stem, model output). A vocal model's instrumental is not the "other" stem.
    stems: tuple[tuple[str, str], ...] = (('vocals', 'vocals'),)


@dataclass(frozen=True)
class Combination:
    """Vocals from one model and drums and bass from another; other is what the mix leaves."""
    id: str
    label: str
    vocals: str
    rhythm: str


def released(tag, filename, sha256):
    return Download(MSST_RELEASES + tag + '/' + filename, filename, sha256)


# The app's own separation (analysis/separation.py): Kim's vocals with the drums and bass of ep_17.
BASELINE = Candidate(
    'hodomia', 'hodomiaの分離（Kim版ボーカル＋ZFTurbo 4分離のドラム・ベース）', 'MIT（ep_17は作者表明）',
    'https://huggingface.co/KimberleyJSN/melbandroformer / '
    'https://github.com/ZFTurbo/Music-Source-Separation-Training/issues/254', stems=FOUR_STEMS)

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
        'bs_roformer_zfturbo_4stem', 'BS-RoFormer ZFTurbo 4分離 ep_17 sdr_9.6568', 'MIT（作者表明）',
        'https://github.com/ZFTurbo/Music-Source-Separation-Training/issues/254'
        '（学習データはMUSDB18HQのみ。データセットは商用利用に権利者の許可が必要）',
        'bs_roformer',
        released('v1.0.12', 'config_bs_roformer_384_8_2_485100.yaml',
                 'd8afb980318d0c08b9c2e24a7adc00d4f3150320c127a7e4de861800d1321939'),
        released('v1.0.12', 'model_bs_roformer_ep_17_sdr_9.6568.ckpt',
                 '3e9daecd70aaed5b5a0d1f861cc4d77eaa45afb3fc6301b1cf32c1be0f5868fb'),
        FOUR_STEMS),
    Candidate(
        'scnet_xl_ihf', 'SCNet XL IHF ep_36 sdr_10.0891', 'MIT（作者の包括的な表明）',
        'https://github.com/ZFTurbo/Music-Source-Separation-Training/issues/245'
        '（作者が自作の重みはMITと回答。このファイル個別の確認依頼は未回答。学習データはMUSDB18のみ）',
        'scnet',
        released('v1.0.15', 'config_musdb18_scnet_xl_more_wide_v5.yaml',
                 '54ddcb8aeeae85c8d0e148741e7d87b0fbd38bd21cffa5d59ba124fe1e672f40'),
        released('v1.0.15', 'model_scnet_ep_36_sdr_10.0891.ckpt',
                 'ac25975f0f5704f3d1a3c3c251505b7a0f417a22eafe82773440ee4f7e14b74f'),
        FOUR_STEMS),
    Candidate(
        'mvsep_53_stems', 'MVSep Mega 53分離 v1', 'MIT（作者表明）',
        'https://github.com/ZFTurbo/Music-Source-Separation-Training/issues/245'
        '（作者は学習音源の著作権を持たないと明記）',
        'bs_roformer',
        released('v1.0.21', 'mvsep_mega_model_bs_roformer_53_stems.yaml',
                 '7e198062a251587088adb91215a4f44ab59e67bd62fcc805cf54d6e7dfc51103'),
        released('v1.0.21', 'mvsep_mega_model_bs_roformer_53_stems_v1.ckpt',
                 'c62820893bbf86d4e734f966bd142d9157cfc8bb8e79e9d8f9ea553f3ff3519f'),
        (('vocals', 'vocal'), ('drums', 'drums'), ('bass', 'bass'))),
    Candidate(
        'mel_roformer_kim', 'Mel-Band RoFormer Kimberley Jensen', 'MIT',
        'https://huggingface.co/KimberleyJSN/melbandroformer（モデルカードの license: mit）',
        'mel_band_roformer', 'configs/KimberleyJensen/config_vocals_mel_band_roformer_kj.yaml',
        Download('https://huggingface.co/KimberleyJSN/melbandroformer/resolve/'
                 'ac9b0614ab3cd7f77219e18ba494dfd93956c348/MelBandRoformer.ckpt',
                 'MelBandRoformer.ckpt',
                 '87201f4d31afb5bc79993230fc49446918425574db48c01c405e44f365c7559e')),
)

COMBINATIONS = (
    Combination('kim_scnet', 'Kim版ボーカル＋SCNet XL IHFのドラム・ベース', 'mel_roformer_kim', 'scnet_xl_ihf'),
)


def by_id(identifier):
    return next(candidate for candidate in CANDIDATES if candidate.id == identifier)
