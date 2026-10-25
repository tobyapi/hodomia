"""Complete the four stems that analysis reads, and store them as a folder that All-In-One accepts."""
from candidates import STEMS


def residual_other(mix, stems):
    """The part of the mix that the vocal, drum and bass estimates leave, so the four stems sum to the mix."""
    return mix - stems['vocals'] - stems['drums'] - stems['bass']


def complete(mix, stems):
    """Add other as the residual when a model gives vocals, drums and bass but no other stem."""
    if 'other' in stems or not {'vocals', 'drums', 'bass'} <= set(stems):
        return stems
    return dict(stems, other=residual_other(mix, stems))


def combine(mix, vocals, rhythm):
    """Vocals from one model with drums and bass from another; other is always the residual."""
    stems = dict(vocals=vocals, drums=rhythm['drums'], bass=rhythm['bass'])
    return dict(stems, other=residual_other(mix, stems))


def has_all(stems):
    return set(STEMS) <= set(stems)


def write(folder, stems, rate):
    import soundfile as sf
    folder.mkdir(parents=True, exist_ok=True)
    for name in STEMS:
        sf.write(str(folder / f'{name}.wav'), stems[name], rate, subtype='FLOAT')


def read(folder, names):
    import soundfile as sf
    return {name: sf.read(str(folder / f'{name}.wav'), dtype='float32', always_2d=True)[0] for name in names}
