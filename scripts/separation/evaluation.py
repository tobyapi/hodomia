"""Separate the compared excerpt with one model, or compose two models' stems, into one report row."""
from dataclasses import dataclass
from pathlib import Path

import inputs
import installation
import measures
import separators
import stem_sets
from candidates import BASELINE


@dataclass(frozen=True)
class Session:
    folder: Path
    home: Path
    runtime: Path
    device: str
    mix_path: Path
    mix: object
    reference: object
    batch_size: int | None


def separation(candidate, session, target):
    if candidate is BASELINE:
        return lambda: separators.app_stems(session.mix_path, target / 'stems', session.runtime, session.device,
                                            installation.python_path(session.runtime))
    installation.verify_downloads(session.home, candidate)
    config = installation.config_path(session.home, candidate)
    weights = installation.download_path(session.home, candidate.weights)
    return lambda: separators.roformer_stems(candidate, config, weights, session.mix,
                                             session.device, session.batch_size)


def save(target, session, stems):
    """Write vocals and the mix minus vocals, and the four analysis stems when there are all of them."""
    import soundfile as sf
    target.mkdir(exist_ok=True)
    for name, samples in (('vocals', stems['vocals']), ('instrumental', session.mix - stems['vocals'])):
        sf.write(str(target / f'{name}.wav'), samples, inputs.RATE, subtype='FLOAT')
    if stem_sets.has_all(stems):
        stem_sets.write(target / 'stems', stems, inputs.RATE)


def measured(row, session, stems):
    seconds = len(session.mix) / inputs.RATE
    row.update(realtimeFactor=row['elapsedSeconds'] / seconds, fourStems=stem_sets.has_all(stems),
               vocalsLevelDb=measures.level_db(stems['vocals']),
               instrumentalLevelDb=measures.level_db(session.mix - stems['vocals']))
    if session.reference is not None:
        row.update(sdrVocals=measures.sdr(session.reference, stems['vocals']),
                   sdrInstrumental=measures.sdr(session.mix - session.reference, session.mix - stems['vocals']))
    return row


def evaluate(candidate, session):
    print(f'分離: {candidate.label}', flush=True)
    target = session.folder / candidate.id
    target.mkdir(exist_ok=True)
    stems, elapsed, allocated, reserved = separators.measure(session.device, separation(candidate, session, target))
    stems = stem_sets.complete(session.mix, stems)
    save(target, session, stems)
    row = dict(id=candidate.id, label=candidate.label, license=candidate.license or '記載なし',
               licenseSource=candidate.license_source, elapsedSeconds=elapsed,
               peakGpuMemoryMiB=allocated, peakGpuReservedMiB=reserved)
    if candidate.weights:
        row['weightsSha256'] = candidate.weights.sha256
    return measured(row, session, stems)


def peak(*values):
    present = [value for value in values if value is not None]
    return max(present) if present else None


def combined(combination, rows, session):
    """Compose stems already written by two models; the time assumes they run one after the other."""
    parts = {row['id']: row for row in rows}
    vocal, rhythm = parts.get(combination.vocals), parts.get(combination.rhythm)
    if vocal is None or rhythm is None or not rhythm['fourStems']:
        return None
    vocals = stem_sets.read(session.folder / combination.vocals, ['vocals'])['vocals']
    drums_and_bass = stem_sets.read(session.folder / combination.rhythm / 'stems', ['drums', 'bass'])
    stems = stem_sets.combine(session.mix, vocals, drums_and_bass)
    save(session.folder / combination.id, session, stems)
    row = dict(id=combination.id, label=combination.label, license=f"{vocal['license']} + {rhythm['license']}",
               licenseSource=f"{vocal['licenseSource']} / {rhythm['licenseSource']}",
               elapsedSeconds=vocal['elapsedSeconds'] + rhythm['elapsedSeconds'],
               peakGpuMemoryMiB=peak(vocal['peakGpuMemoryMiB'], rhythm['peakGpuMemoryMiB']),
               peakGpuReservedMiB=peak(vocal['peakGpuReservedMiB'], rhythm['peakGpuReservedMiB']))
    return measured(row, session, stems)
