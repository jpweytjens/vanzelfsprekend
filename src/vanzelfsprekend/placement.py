"""Exact 1-D no-overlap placement, shared by line labels and tick labels.

`stack` returns the positions closest (least squares) to the desired
ones that keep their order and clear each other; `pava` is its solver.
Sizes and positions are in the same unit, one dimension: heights for a
vertical stack of line labels, widths for a row of x tick labels.
"""

import numpy as np

GAP = 2.0
"""Default minimum clearance between placed boxes, in points."""

PIN_WEIGHT = 1e9
"""Weight of a pinned box: chosen so pins move only when a strip is over capacity."""

PIN_TOLERANCE = 0.5
"""A pin that moved more than this many pixels marks its strip over capacity.

Chosen: under one device pixel.
"""


def pava(y: np.ndarray, weights: np.ndarray | None = None) -> np.ndarray:
    """Return best non-decreasing weighted least-squares fit to `y`.

    Pool adjacent violators algorithm.

    With `weights=None` every value weighs one, the classic fit. A pooled
    block takes the weighted mean of its members, so a very heavy value
    pulls the block onto itself.
    """
    w = np.ones(len(y)) if weights is None else np.asarray(weights, dtype=float)
    means: list[float] = []
    counts: list[int] = []
    totals: list[float] = []
    for value, weight in zip(y, w, strict=True):
        mean, count, total = float(value), 1, float(weight)
        while means and means[-1] > mean:
            mean = (mean * total + means[-1] * totals[-1]) / (total + totals[-1])
            total += totals[-1]
            count += counts[-1]
            means.pop()
            counts.pop()
            totals.pop()
        means.append(mean)
        counts.append(count)
        totals.append(total)
    return np.repeat(means, counts)


def stack(
    desired: np.ndarray,
    sizes: np.ndarray,
    gap: float,
    weights: np.ndarray | None = None,
    key: np.ndarray | None = None,
) -> np.ndarray:
    """Return positions closest to `desired` that keep order and clear each other.

    Minimizes the total weighted squared displacement subject to adjacent
    positions (in sorted order) being at least half of each size plus `gap`
    apart. Subtracting the cumulative separations reduces the constraints to
    plain monotonicity, which `pava` solves exactly.

    `weights` scales each box's displacement cost; a box weighted
    `PIN_WEIGHT` is effectively pinned and the others move around it.
    `key` fixes the order the boxes are stacked in; it defaults to
    `desired`, and a caller passes its own to break ties on purpose.
    """
    order = np.argsort(desired if key is None else key, kind="stable")
    d = np.asarray(desired, dtype=float)[order]
    h = np.asarray(sizes, dtype=float)[order]
    w = None if weights is None else np.asarray(weights, dtype=float)[order]
    margins = np.concatenate(([0.0], np.cumsum((h[:-1] + h[1:]) / 2 + gap)))
    placed = pava(d - margins, w) + margins
    out = np.empty_like(placed)
    out[order] = placed
    return out
