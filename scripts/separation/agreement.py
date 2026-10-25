"""How far downstream estimates from candidate stems move away from those of the baseline stems.

None of these measures says which side is right; they show how much a change of stems changes the result."""


def boundaries(sections, duration):
    """Section starts and ends inside the song; the song's own edges are not estimates."""
    times = {round(s[key], 3) for s in sections for key in ('start', 'end') if s.get(key) is not None}
    return sorted(t for t in times if .5 < t < duration - .5)


def boundary_f(reference, estimate, window):
    """F-measure of boundary hits, each reference boundary matched at most once within the window."""
    if not reference and not estimate:
        return 1.0
    pairs = sorted((abs(r - e), i, j) for i, r in enumerate(reference) for j, e in enumerate(estimate)
                   if abs(r - e) <= window)
    used_reference, used_estimate = set(), set()
    for _, i, j in pairs:
        if i not in used_reference and j not in used_estimate:
            used_reference.add(i)
            used_estimate.add(j)
    hits = len(used_reference)
    return 2 * hits / (len(reference) + len(estimate))


def label_at(sections, time):
    return next((s['label'] for s in sections if s['start'] <= time < s['end']), None)


def label_agreement(reference, estimate, duration, step=.1):
    """Share of the song where both estimates give the same section label."""
    times = [i * step for i in range(int(duration / step))]
    if not times:
        return None
    return sum(label_at(reference, t) == label_at(estimate, t) for t in times) / len(times)


def edit_distance(a, b):
    previous = list(range(len(b) + 1))
    for i, x in enumerate(a, 1):
        current = [i]
        for j, y in enumerate(b, 1):
            current.append(min(previous[j] + 1, current[j - 1] + 1, previous[j - 1] + (x != y)))
        previous = current
    return previous[-1]


def character_error_rate(reference, estimate):
    """Edit distance per reference character; None when the reference has no characters."""
    return edit_distance(reference, estimate) / len(reference) if reference else None


def active_seconds(regions):
    return sum(r['end'] - r['start'] for r in regions)


def activity_overlap(reference, estimate):
    """Intersection over union of the time where a stem is judged active."""
    intersection = sum(max(0, min(r['end'], e['end']) - max(r['start'], e['start'])) for r in reference for e in estimate)
    union = active_seconds(reference) + active_seconds(estimate) - intersection
    return intersection / union if union > 0 else 1.0
