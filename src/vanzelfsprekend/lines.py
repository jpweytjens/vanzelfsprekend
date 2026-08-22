"""End-of-line direct labels: label each line at one end instead of in a legend."""

import numpy as np


def _pava(y: np.ndarray) -> np.ndarray:
    """Return best non-decreasing least-squares fit to `y` (pool adjacent violators)."""
    means: list[float] = []
    counts: list[int] = []
    for value in y:
        mean, count = float(value), 1
        while means and means[-1] > mean:
            mean = (mean * count + means[-1] * counts[-1]) / (count + counts[-1])
            count += counts[-1]
            means.pop()
            counts.pop()
        means.append(mean)
        counts.append(count)
    return np.repeat(means, counts)


def _stack(desired: np.ndarray, heights: np.ndarray, gap: float) -> np.ndarray:
    """Return positions closest to `desired` that keep order and clear each other.

    Minimizes the total squared displacement subject to adjacent positions
    (in sorted order) being at least half of each height plus `gap` apart.
    Subtracting the cumulative separations reduces the constraints to plain
    monotonicity, which `_pava` solves exactly.
    """
    order = np.argsort(desired, kind="stable")
    d = np.asarray(desired, dtype=float)[order]
    h = np.asarray(heights, dtype=float)[order]
    margins = np.concatenate(([0.0], np.cumsum((h[:-1] + h[1:]) / 2 + gap)))
    placed = _pava(d - margins) + margins
    out = np.empty_like(placed)
    out[order] = placed
    return out
