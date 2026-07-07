"""Tick locator built on mizani's extended Wilkinson algorithm."""

import matplotlib as mpl
import numpy as np
from matplotlib.ticker import AutoLocator, Locator
from mizani.breaks import breaks_extended


class TalbotLocator(Locator):
    """Place ticks on nice numbers inside the data range.

    Delegates to `mizani.breaks.breaks_extended` (Talbot's extended
    Wilkinson algorithm) with `only_inside=True`, so every tick lies
    within the interval it is given. When used on an axis, ticks are
    computed from the data interval, not the view interval, which is
    what lets a range frame hug the data.

    With `loose=True`, computes nice numbers from the data range and
    extends the tick grid outward by whole steps so the outermost ticks
    bound the interval.

    Parameters
    ----------
    n : int
        Desired number of ticks.
    loose : bool
        If True, extend the tick grid outward by whole steps so the
        outermost ticks bound the data interval. Default is False.
    """

    def __init__(self, n: int = 5, loose: bool = False):
        self._loose = loose
        self._breaks = breaks_extended(n=n, only_inside=not loose)
        self._cover = self._breaks if loose else breaks_extended(n=n)

    def __call__(self):
        """Return tick locations computed from the axis data interval."""
        dmin, dmax = self.axis.get_data_interval()
        if not np.isfinite([dmin, dmax]).all():
            return AutoLocator().tick_values(*self.axis.get_view_interval())
        return self.tick_values(dmin, dmax)

    def tick_values(self, vmin, vmax):
        """Return tick locations inside `[vmin, vmax]`.

        Parameters
        ----------
        vmin, vmax : float
            Interval bounds. Swapped if given in reverse order;
            degenerate values fall back to `AutoLocator`.

        Returns
        -------
        ndarray
            Tick locations.
        """
        if vmin > vmax:
            vmin, vmax = vmax, vmin
        if not np.isfinite([vmin, vmax]).all() or vmin == vmax:
            return AutoLocator().tick_values(*self.nonsingular(vmin, vmax))
        try:
            ticks = self._breaks((vmin, vmax))
            if self._loose and ticks.size >= 2:
                ticks = _extend_to_cover(ticks, vmin, vmax)
        except (OverflowError, ValueError, FloatingPointError):
            return AutoLocator().tick_values(vmin, vmax)
        if ticks.size == 0:
            return AutoLocator().tick_values(vmin, vmax)
        return ticks

    def view_limits(self, vmin, vmax):
        """Return view limits for `vmin`..`vmax`.

        matplotlib calls this on every autoscale, not only when
        `axes.autolimit_mode` is `'round_numbers'`, so a loose locator
        and a plain one need different behavior to avoid inflating the
        view every draw.

        If this is a loose locator attached to an axis, the axis's data
        interval (not `vmin`/`vmax`) is used to compute the loose tick
        span, so the view comes out edge-to-edge with the loose range
        frame regardless of margin padding. Otherwise `vmin`, `vmax`
        are returned unchanged unless
        `matplotlib.rcParams["axes.autolimit_mode"]` is
        `'round_numbers'`, in which case they are rounded outward to
        nice numbers covering the input, matching `MaxNLocator`.

        Either covering guarantee (loose span or round-numbers
        rounding) holds only up to a `1e-9 * step` float tolerance,
        since mizani's breaks carry float dust (e.g. the first break of
        `(2.3, 2.31)` comes out as `2.3 + 4.4e-16`).

        Parameters
        ----------
        vmin, vmax : float
            The proposed view limits.

        Returns
        -------
        tuple of float
            Lower and upper view limits.
        """
        if vmin > vmax:
            vmin, vmax = vmax, vmin

        if self._loose and self.axis is not None:
            dmin, dmax = self.axis.get_data_interval()
            if np.isfinite([dmin, dmax]).all() and dmin != dmax:
                try:
                    ticks = self._cover((dmin, dmax))
                    if ticks.size >= 2:
                        ticks = _extend_to_cover(ticks, dmin, dmax)
                        return float(ticks[0]), float(ticks[-1])
                except (OverflowError, ValueError, FloatingPointError):
                    pass
                return super().view_limits(vmin, vmax)

        if mpl.rcParams["axes.autolimit_mode"] != "round_numbers":
            return super().view_limits(vmin, vmax)
        if not np.isfinite([vmin, vmax]).all() or vmin == vmax:
            return super().view_limits(vmin, vmax)
        try:
            ticks = self._cover((vmin, vmax))
            if ticks.size >= 2:
                ticks = _extend_to_cover(ticks, vmin, vmax)
                return float(ticks[0]), float(ticks[-1])
        except (OverflowError, ValueError, FloatingPointError):
            pass
        return super().view_limits(vmin, vmax)


def _extend_to_cover(ticks, vmin, vmax):
    if ticks.size < 2:
        return ticks
    step = ticks[1] - ticks[0]
    tol = 1e-9 * step
    down = int(np.ceil((ticks[0] - vmin - tol) / step)) if ticks[0] - vmin > tol else 0
    up = int(np.ceil((vmax - ticks[-1] - tol) / step)) if vmax - ticks[-1] > tol else 0
    if down == 0 and up == 0:
        return ticks
    return ticks[0] + step * np.arange(-down, ticks.size + up)
