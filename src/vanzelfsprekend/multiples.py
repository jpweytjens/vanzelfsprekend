"""Small multiples: one treatment for a grid of axes on a shared scale."""

from collections.abc import Sequence

import numpy as np
from matplotlib.axes import Axes
from matplotlib.ticker import Locator


def _data_union(axes: Sequence[Axes], name: str) -> tuple[float, float] | None:
    """Union of the members' data intervals along `name` (`'x'` or `'y'`).

    Log axes substitute `minpos` for a nonpositive minimum, mirroring
    the locators' own reading. Members with no finite data are skipped;
    returns `None` when none remain or the union is degenerate.
    """
    lo, hi = np.inf, -np.inf
    for ax in axes:
        axis = ax.xaxis if name == "x" else ax.yaxis
        dmin, dmax = axis.get_data_interval()
        if axis.get_scale() == "log" and dmin <= 0:
            dmin = axis.get_minpos()
        if not np.isfinite([dmin, dmax]).all():
            continue
        lo, hi = min(lo, dmin), max(hi, dmax)
    if not np.isfinite([lo, hi]).all() or lo == hi:
        return None
    return (lo, hi)


class _GroupLocator(Locator):
    """Delegate tick placement to `inner`, fed the group's data union.

    Installed on a panel's axis in place of the locator `apply` chose,
    so ticks are recomputed on every draw from the union of the group
    members' data instead of the one panel's. Everything else defers to
    `inner`, whose own axis binding is left in place so a formatter
    constructed around it (`ConciseDateFormatter`) keeps working.
    """

    def __init__(self, inner: Locator, members: Sequence[Axes], name: str) -> None:
        self._inner = inner
        self._members = members
        self._name = name

    def __call__(self) -> np.ndarray:  # ty: ignore[invalid-method-override]
        union = _data_union(self._members, self._name)
        if union is None:
            return np.asarray(self._inner())
        return np.asarray(self._inner.tick_values(*union))

    def tick_values(self, vmin: float, vmax: float) -> np.ndarray:  # ty: ignore
        return np.asarray(self._inner.tick_values(vmin, vmax))

    def nonsingular(  # ty: ignore[invalid-method-override]
        self, vmin: float, vmax: float
    ) -> tuple[float, float]:
        return self._inner.nonsingular(vmin, vmax)

    def view_limits(self, vmin: float, vmax: float) -> tuple[float, float]:
        return self._inner.view_limits(vmin, vmax)
