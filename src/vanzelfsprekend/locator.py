"""Tick locator built on mizani's extended Wilkinson algorithm."""

from collections.abc import Sequence

import matplotlib as mpl
import numpy as np
from matplotlib.ticker import AutoLocator, FixedLocator, Locator, LogLocator
from mizani.breaks import breaks_extended, breaks_log
from numpy.typing import ArrayLike

_DEFAULT_Q = (1, 5, 2, 2.5, 4, 3)
_DEFAULT_WEIGHTS = {
    "simplicity": 0.25,
    "coverage": 0.2,
    "density": 0.5,
    "legibility": 0.05,
}


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
    nice_numbers : sequence of float, optional
        Advanced tuning of the underlying Talbot extended-Wilkinson
        search: preferred step mantissas for the tick-step search
        (mizani's `Q`). Biases which step sizes the search considers;
        the chosen step may be a whole multiple of an entry, and ticks
        are multiples of the step, so tick values are not strictly
        limited to these mantissas. `None` uses mizani's default
        `(1, 5, 2, 2.5, 4, 3)`.
    weights : dict, optional
        Advanced tuning of the underlying Talbot extended-Wilkinson
        search: a partial mapping of weights for the four scoring
        criteria, merged over the defaults `{"simplicity": 0.25,
        "coverage": 0.2, "density": 0.5, "legibility": 0.05}` (mizani's
        `w`). Keys must be a subset of `{"simplicity", "coverage",
        "density", "legibility"}`.
    """

    def __init__(
        self,
        n: int = 5,
        loose: bool = False,
        nice_numbers: Sequence[float] | None = None,
        weights: dict[str, float] | None = None,
    ) -> None:
        valid_keys = set(_DEFAULT_WEIGHTS)
        if weights is not None:
            bad_keys = set(weights) - valid_keys
            if bad_keys:
                raise ValueError(
                    f"invalid weights key(s) {sorted(bad_keys)}; valid keys are "
                    f"{sorted(valid_keys)}"
                )
        merged_weights = {**_DEFAULT_WEIGHTS, **(weights or {})}
        q = tuple(nice_numbers) if nice_numbers is not None else _DEFAULT_Q
        w = (
            merged_weights["simplicity"],
            merged_weights["coverage"],
            merged_weights["density"],
            merged_weights["legibility"],
        )

        self._loose = loose
        self._breaks = breaks_extended(n=n, Q=q, only_inside=not loose, w=w)
        self._cover = (
            self._breaks if loose else breaks_extended(n=n, Q=q, only_inside=False, w=w)
        )

    def __call__(self) -> np.ndarray:  # ty: ignore[invalid-method-override]
        """Return tick locations computed from the axis data interval."""
        dmin, dmax = self.axis.get_data_interval()  # ty: ignore[unresolved-attribute]
        if not np.isfinite([dmin, dmax]).all():
            view = self.axis.get_view_interval()  # ty: ignore[unresolved-attribute]
            return np.asarray(AutoLocator().tick_values(*view))
        return self.tick_values(dmin, dmax)

    def tick_values(self, vmin: float, vmax: float) -> np.ndarray:  # ty: ignore
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
            return np.asarray(AutoLocator().tick_values(*self.nonsingular(vmin, vmax)))
        try:
            ticks = self._breaks((vmin, vmax))
            if self._loose and ticks.size >= 2:
                ticks = _extend_to_cover(ticks, vmin, vmax)
        except (OverflowError, ValueError, FloatingPointError):
            return np.asarray(AutoLocator().tick_values(vmin, vmax))
        if ticks.size == 0:
            return np.asarray(AutoLocator().tick_values(vmin, vmax))
        return ticks

    def view_limits(self, vmin: float, vmax: float) -> tuple[float, float]:
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


class LogBreaksLocator(Locator):
    """Place ticks on integer powers inside the data range of a log axis.

    Delegates to `mizani.breaks.breaks_log`, which returns breaks at
    integer powers of `base` (with a sub-decade fallback for narrow
    ranges) that may overflow the interval; the overflow is filtered
    away so every tick lies within the interval. When used on an axis,
    ticks are computed from the data interval, not the view interval,
    which is what lets a range frame hug the data.

    With `loose=True`, keeps the covering breaks and extends the grid
    outward by whole multiplicative steps so the outermost ticks bound
    the interval.

    Parameters
    ----------
    n : int
        Desired number of ticks.
    loose : bool
        If True, extend the tick grid outward by whole multiplicative
        steps so the outermost ticks bound the data interval. Default
        is False.
    base : float
        Base of the logarithm, matching the axis scale's base.
    """

    def __init__(self, n: int = 5, loose: bool = False, base: float = 10) -> None:
        self._loose = loose
        self._base = base
        self._breaks = breaks_log(n=n, base=base)

    def __call__(self) -> np.ndarray:  # ty: ignore[invalid-method-override]
        """Return tick locations computed from the axis data interval."""
        dmin, dmax = self.axis.get_data_interval()  # ty: ignore[unresolved-attribute]
        if dmin <= 0:
            dmin = self.axis.get_minpos()  # ty: ignore[unresolved-attribute]
        if not np.isfinite([dmin, dmax]).all():
            view = self.axis.get_view_interval()  # ty: ignore[unresolved-attribute]
            return _log_fallback(view[0], view[1], self._base)
        return self.tick_values(dmin, dmax)

    def tick_values(self, vmin: float, vmax: float) -> np.ndarray:  # ty: ignore
        """Return tick locations inside `[vmin, vmax]`.

        Parameters
        ----------
        vmin, vmax : float
            Interval bounds. Swapped if given in reverse order;
            degenerate or nonpositive values fall back to decade ticks
            from `LogLocator` on a sanitized interval.

        Returns
        -------
        ndarray
            Tick locations.
        """
        if vmin > vmax:
            vmin, vmax = vmax, vmin
        if not np.isfinite([vmin, vmax]).all() or vmin <= 0 or vmin == vmax:
            return _log_fallback(vmin, vmax, self._base)
        try:
            ticks = np.asarray(self._breaks((vmin, vmax)), dtype=float)
            if self._loose:
                ticks = _extend_to_cover_log(ticks, vmin, vmax)
            else:
                ticks = ticks[
                    (ticks >= vmin * (1 - 1e-9)) & (ticks <= vmax * (1 + 1e-9))
                ]
        except (OverflowError, ValueError, FloatingPointError):
            return _log_fallback(vmin, vmax, self._base)
        if ticks.size == 0:
            return _log_fallback(vmin, vmax, self._base)
        return ticks

    def view_limits(self, vmin: float, vmax: float) -> tuple[float, float]:
        """Return view limits for `vmin`..`vmax`.

        Mirrors `TalbotLocator.view_limits`: a loose locator attached
        to an axis derives the view from the data interval's covering
        breaks so the view comes out edge-to-edge with the loose range
        frame; otherwise the input passes through unless
        `matplotlib.rcParams["axes.autolimit_mode"]` is
        `'round_numbers'`, in which case it is widened to the covering
        breaks.

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
            if dmin <= 0:
                dmin = self.axis.get_minpos()
            if np.isfinite([dmin, dmax]).all() and 0 < dmin < dmax:
                try:
                    ticks = np.asarray(self._breaks((dmin, dmax)), dtype=float)
                    if ticks.size >= 2:
                        ticks = _extend_to_cover_log(ticks, dmin, dmax)
                        return float(ticks[0]), float(ticks[-1])
                except (OverflowError, ValueError, FloatingPointError):
                    pass
            return super().view_limits(vmin, vmax)

        if mpl.rcParams["axes.autolimit_mode"] != "round_numbers":
            return super().view_limits(vmin, vmax)
        if not np.isfinite([vmin, vmax]).all() or vmin <= 0 or vmin == vmax:
            return super().view_limits(vmin, vmax)
        try:
            ticks = np.asarray(self._breaks((vmin, vmax)), dtype=float)
            if ticks.size >= 2:
                ticks = _extend_to_cover_log(ticks, vmin, vmax)
                return float(ticks[0]), float(ticks[-1])
        except (OverflowError, ValueError, FloatingPointError):
            pass
        return super().view_limits(vmin, vmax)


class QuartileLocator(FixedLocator):
    """Place ticks at the five-number summary of `data`.

    Ticks sit at the minimum, first quartile, median, third quartile,
    and maximum of the data, turning a range frame into Tufte's
    quartile plot. Non-finite values are ignored. Tick labels follow
    the axis formatter; pass a format string such as
    `ax.xaxis.set_major_formatter("{x:.1f}")` to round them.

    Parameters
    ----------
    data : array-like
        The plotted values whose summary the ticks mark.

    Raises
    ------
    ValueError
        If `data` contains no finite values.
    """

    def __init__(self, data: ArrayLike) -> None:
        values = np.asarray(data, dtype=float).ravel()
        values = values[np.isfinite(values)]
        if values.size == 0:
            raise ValueError("data has no finite values")
        super().__init__(np.quantile(values, (0, 0.25, 0.5, 0.75, 1)))


def _extend_to_cover(ticks: np.ndarray, vmin: float, vmax: float) -> np.ndarray:
    if ticks.size < 2:
        return ticks
    step = ticks[1] - ticks[0]
    tol = 1e-9 * step
    down = int(np.ceil((ticks[0] - vmin - tol) / step)) if ticks[0] - vmin > tol else 0
    up = int(np.ceil((vmax - ticks[-1] - tol) / step)) if vmax - ticks[-1] > tol else 0
    if down == 0 and up == 0:
        return ticks
    return ticks[0] + step * np.arange(-down, ticks.size + up)


def _extend_to_cover_log(ticks: np.ndarray, vmin: float, vmax: float) -> np.ndarray:
    if ticks.size < 2:
        return ticks
    out = list(ticks)
    while out[0] > vmin * (1 + 1e-9):
        out.insert(0, out[0] * out[0] / out[1])
    while out[-1] < vmax * (1 - 1e-9):
        out.append(out[-1] * out[-1] / out[-2])
    return np.asarray(out)


def _log_fallback(vmin: float, vmax: float, base: float) -> np.ndarray:
    if vmin > vmax:
        vmin, vmax = vmax, vmin
    if not np.isfinite([vmin, vmax]).all() or vmax <= 0:
        vmin, vmax = 1.0, base
    elif vmin <= 0:
        vmin = vmax / base**2
    if vmin == vmax:
        vmin, vmax = vmin / base, vmax * base
    return np.asarray(LogLocator(base=base).tick_values(vmin, vmax))
