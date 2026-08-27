"""Exact 1-D no-overlap placement, shared by line labels and tick labels.

`stack` returns the positions closest (least squares) to the desired
ones that keep their order and clear each other; `pava` is its solver.
Sizes and positions are in the same unit, one dimension: heights for a
vertical stack of line labels, widths for a row of x tick labels.
"""

import numpy as np

GAP = 2.0
"""Default minimum clearance between placed boxes, in points."""


def pava(y: np.ndarray) -> np.ndarray:
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


def stack(desired: np.ndarray, sizes: np.ndarray, gap: float) -> np.ndarray:
    """Return positions closest to `desired` that keep order and clear each other.

    Minimizes the total squared displacement subject to adjacent positions
    (in sorted order) being at least half of each size plus `gap` apart.
    Subtracting the cumulative separations reduces the constraints to plain
    monotonicity, which `pava` solves exactly.
    """
    order = np.argsort(desired, kind="stable")
    d = np.asarray(desired, dtype=float)[order]
    h = np.asarray(sizes, dtype=float)[order]
    margins = np.concatenate(([0.0], np.cumsum((h[:-1] + h[1:]) / 2 + gap)))
    placed = pava(d - margins) + margins
    out = np.empty_like(placed)
    out[order] = placed
    return out
