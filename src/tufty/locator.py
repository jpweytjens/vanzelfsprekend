"""Tick locator built on mizani's extended Wilkinson algorithm."""

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

    Parameters
    ----------
    n : int
        Desired number of ticks.
    """

    def __init__(self, n: int = 5):
        self._breaks = breaks_extended(n=n, only_inside=True)

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
        ticks = self._breaks((vmin, vmax))
        if ticks.size == 0:
            return AutoLocator().tick_values(vmin, vmax)
        return ticks
