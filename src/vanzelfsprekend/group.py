"""Scale groups: the panels whose data union feeds one axis's ticks and spine.

`distill` reads a group from matplotlib's share groupers; `small_multiples`
reads one from the gridspec and `compare`. Both hand their groups to this
module, which unions the members' data so the frame and the locators span
it. Nothing here is public.
"""

from collections.abc import Sequence

import numpy as np
from matplotlib.axes import Axes
from matplotlib.ticker import Locator

from vanzelfsprekend.locator import DateBreaksLocator, LogBreaksLocator, TalbotLocator

BreaksLocator = TalbotLocator | LogBreaksLocator | DateBreaksLocator


def data_union(members: Sequence[Axes], name: str) -> tuple[float, float] | None:
    """Union of the members' data intervals along `name` (`'x'` or `'y'`).

    Log axes substitute `minpos` for a nonpositive minimum, mirroring
    the locators' own reading. Members with no finite data are skipped;
    returns `None` when none remain or the union is degenerate.
    """
    lo, hi = np.inf, -np.inf
    for ax in members:
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


def view_union(members: Sequence[Axes], name: str) -> tuple[float, float] | None:
    """Union of the members' view intervals along `name` (`'x'` or `'y'`).

    Each member's interval is sorted first so an inverted axis doesn't
    poison the union. Returns `None` when the result would be empty or
    degenerate.
    """
    lo, hi = np.inf, -np.inf
    for ax in members:
        axis = ax.xaxis if name == "x" else ax.yaxis
        vmin, vmax = sorted(axis.get_view_interval())
        lo, hi = min(lo, vmin), max(hi, vmax)
    if not np.isfinite([lo, hi]).all() or lo == hi:
        return None
    return (lo, hi)


class GroupLocator(Locator):
    """Delegate tick placement to `inner`, fed the group's data union.

    Installed on a panel's axis in place of the locator the frame chose,
    so ticks are recomputed on every draw from the union of the group
    members' data instead of the one panel's. Everything else defers to
    `inner`, whose own axis binding is left in place so a formatter
    constructed around it (`ConciseDateFormatter`) keeps working. View
    limits are computed over the union as well, so a loose group
    autoscales to the union's covering breaks on the first draw.
    """

    def __init__(
        self, inner: BreaksLocator, members: Sequence[Axes], name: str
    ) -> None:
        self._inner = inner
        self._members = members
        self._name = name

    def __call__(self) -> np.ndarray:  # ty: ignore[invalid-method-override]
        """Compute tick positions from the union of the group's data."""
        union = data_union(self._members, self._name)
        if union is None:
            return np.asarray(self._inner())
        return np.asarray(self._inner.tick_values(*union))

    def tick_values(self, vmin: float, vmax: float) -> np.ndarray:  # ty: ignore
        """Delegate tick value computation to the inner locator."""
        return np.asarray(self._inner.tick_values(vmin, vmax))

    def nonsingular(  # ty: ignore[invalid-method-override]
        self, vmin: float, vmax: float
    ) -> tuple[float, float]:
        """Delegate singularity handling to the inner locator."""
        return self._inner.nonsingular(vmin, vmax)

    def view_limits(self, vmin: float, vmax: float) -> tuple[float, float]:
        """View limits with the loose span covering the group's data union."""
        return self._inner.view_limits_over(
            vmin, vmax, data_union(self._members, self._name)
        )
