"""Finite-population-normalized Gini used by the current paper.

The arena retains all four original seats. This normalization rescales the
maximum to one; it is not a claim of statistical unbiasedness.
"""


def distribution(values):
    n = len(values)
    assert n >= 2 and min(values) >= 0
    total = sum(values)
    mu = total / n
    gap = sum(abs(a - b) for a in values for b in values)
    g = gap / (2 * (n - 1) * total) if total else None
    return {'mu': mu, 'G': g, 'S': mu - gap / (2 * n * (n - 1))}


def gini(values):
    return distribution(values)['G']


def sen(values):
    return distribution(values)['S']
