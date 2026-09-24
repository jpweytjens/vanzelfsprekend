"""Tick locator built on mizani's extended Wilkinson algorithm."""

import datetime
from collections.abc import Callable, Mapping, Sequence
from typing import ClassVar, Literal

import matplotlib as mpl
import numpy as np
from dateutil.relativedelta import relativedelta
from matplotlib.axis import Axis
from matplotlib.dates import date2num, num2date
from matplotlib.font_manager import FontProperties
from matplotlib.ticker import AutoLocator, FixedLocator, Locator, LogLocator
from matplotlib.transforms import Bbox
from mizani.breaks import (
    breaks_date,
    breaks_date_width,
    breaks_extended,
    breaks_log,
)
from numpy.typing import ArrayLike

from vanzelfsprekend.ticks import _rc

SPACING = (7.0, 4.0)
"""Default gap between ticks along x and y, in tick-label heights.

A y label is one label height long along its axis; an x label is
three to five, so x asks for the wider gap. At 10 pt labels the pair
is 70 pt and 40 pt, about 2.5 cm and 1.4 cm.
"""
_UNBOUND_N = 5
_DEFAULT_Q = (1, 5, 2, 2.5, 4, 3)
_DEFAULT_WEIGHTS = {
    "simplicity": 0.25,
    "coverage": 0.2,
    "density": 0.5,
    "legibility": 0.05,
}
Placement = Literal["inside", "flexible", "loose"]
"""How the outermost ticks sit against the interval (mizani's `placement`).

Mirrors mizani's `BreaksExtendedPlacement`, which exists only for type
checkers; ty checks the two agree at every `breaks_extended` call.
"""
PlacementPair = tuple[Placement, Placement]
"""A `(low, high)` pair of placements, one per end."""


def parse_spacing(spacing: float | tuple[float, float] | None) -> dict[str, float]:
    """Resolve `spacing` into per-axis gaps, keyed `'x'` and `'y'`.

    `None` is the public default and takes `SPACING`, the single
    authority for the aimed-for tick spacing.
    """
    if spacing is None:
        spacing = SPACING
    if isinstance(spacing, (int, float)):
        return {"x": spacing, "y": spacing}
    pair = tuple(spacing)
    if len(pair) != 2 or not all(isinstance(s, (int, float)) for s in pair):
        raise ValueError(
            f"spacing must be a number or a tuple of two numbers, got {spacing!r}"
        )
    return {"x": pair[0], "y": pair[1]}


def parse_n(
    n: int | tuple[int | None, int | None] | None,
) -> dict[str, int | None]:
    """Resolve `n` into per-axis tick counts, keyed `'x'` and `'y'`.

    `None`, whole or as either tuple entry, leaves that axis to
    `spacing`, as `offset` reads `None` per end.
    """
    if n is None or isinstance(n, int):
        return {"x": n, "y": n}
    pair = tuple(n)
    if len(pair) != 2 or not all(v is None or isinstance(v, int) for v in pair):
        raise ValueError(
            f"n must be an integer or a tuple of two integers or None, got {n!r}"
        )
    return {"x": pair[0], "y": pair[1]}


def _label_height(axis: Axis) -> float:
    """Read the axis's major tick-label font size in points."""
    name = axis.axis_name  # ty: ignore[unresolved-attribute]
    size = axis.get_tick_params(which="major").get(
        "labelsize", _rc(f"{name}tick.labelsize")
    )
    return FontProperties(size=size).get_size_in_points()


class BreaksLocator(Locator):
    """What the three mizani-backed locators share: the target count.

    Talbot's density term wants the number of labels to follow the
    physical length of the axis; mizani takes a count. This base
    resolves the count at tick time: `n` when given, otherwise the
    axis's length in tick-label heights divided by `spacing`, so a
    poster's large labels thin the ticks and a small panel gets few.

    Parameters
    ----------
    spacing : float, optional
        The gap to aim for between ticks, in tick-label heights.
        `None` takes `SPACING` for the axis the locator lands on.
    n : int, optional
        The number of ticks to aim for, overriding `spacing`. `None`
        derives it from the axis's length and `spacing` at tick time.
    """

    PLACEMENTS: ClassVar[tuple[Placement, ...]]
    """The placements this locator can give; each subclass sets it."""

    def __init__(self, spacing: float | None, n: int | None) -> None:
        self._n = n
        self._spacing = spacing

    def target(self, axis: Axis | None = None) -> int:
        """Return the number of ticks to aim for on `axis`.

        `n` when it was given. Otherwise the axis's length in
        tick-label heights divided by `spacing`, rounded, at least two.
        `axis` defaults to the axis the locator is bound to; a group
        passes a sibling's to size the ticks for its narrowest panel.
        Without an axis (`tick_values` called by hand) there is no
        length, and the target is five.
        """
        if self._n is not None:
            return self._n
        if axis is None:
            axis = self.axis  # ty: ignore[invalid-assignment]
        if axis is None:
            return _UNBOUND_N
        name = axis.axis_name  # ty: ignore[unresolved-attribute]
        spacing = parse_spacing(self._spacing)[name]
        axes = axis.axes
        ends = Bbox.unit().transformed(axes.transAxes - axes.figure.dpi_scale_trans)
        length = (ends.width if name == "x" else ends.height) * 72
        return max(2, round(length / (spacing * _label_height(axis))))


class TalbotLocator(BreaksLocator):
    """Place ticks on nice numbers inside the data range.

    Delegates to `mizani.breaks.breaks_extended` (Talbot's extended
    Wilkinson algorithm) with each end held by `placement`; by default
    every tick lies within the interval it is given. When used on an
    axis, ticks are computed from the data interval, not the view
    interval, which is what lets a range frame hug the data.

    `placement` sets how the outermost ticks sit against the interval,
    the three labelings of Talbot, Lin and Hanrahan (2010): `'inside'`
    keeps them within it, `'loose'` puts them at or beyond it, and
    `'flexible'` lets the search choose either side. Every placement
    fills the interval: no further tick at the same step would fit
    inside it. A pair `(low, high)` sets each end on its own.

    Parameters
    ----------
    spacing : float, optional
        The gap to aim for between ticks, in tick-label heights. See
        `BreaksLocator`.
    n : int, optional
        The number of ticks to aim for, overriding `spacing`. See
        `BreaksLocator`.
    placement : {'inside', 'flexible', 'loose'} or tuple of two of them
        How the outermost ticks sit against the interval. Default
        `'inside'`.
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
        "density", "legibility"}`. The simplicity, coverage and density
        weights must be positive (mizani's rule, checked at
        construction).
    unit : float
        Place ticks on nice numbers measured in units of `unit`: the
        search runs on `(vmin / unit, vmax / unit)` and the result is
        multiplied back. With `unit=np.pi` the plain decimal nice numbers
        (0.5, 0.25) become `np.pi / 2`, `np.pi / 4`, ticks that follow the
        axis width the way the default ticks do, where a fixed
        `MultipleLocator(np.pi / 2)` would not. Must be finite and
        strictly positive; the default `1.0` is an exact identity that
        leaves the default tick path unchanged. A tick is *placed*, not
        labelled "pi/2" -- write the fraction with a `FuncFormatter`.
    """

    PLACEMENTS: ClassVar[tuple[Placement, ...]] = ("inside", "flexible", "loose")

    def __init__(
        self,
        spacing: float | None = None,
        n: int | None = None,
        placement: Placement | PlacementPair = "inside",
        nice_numbers: Sequence[float] | None = None,
        weights: dict[str, float] | None = None,
        unit: float = 1.0,
    ) -> None:
        super().__init__(spacing, n)
        if not np.isfinite(unit) or unit <= 0:
            raise ValueError(f"unit must be finite and strictly positive, got {unit!r}")
        valid_keys = set(_DEFAULT_WEIGHTS)
        if weights is not None:
            bad_keys = set(weights) - valid_keys
            if bad_keys:
                raise ValueError(
                    f"invalid weights key(s) {sorted(bad_keys)}; valid keys are "
                    f"{sorted(valid_keys)}"
                )
        merged_weights = {**_DEFAULT_WEIGHTS, **(weights or {})}
        self._q = tuple(nice_numbers) if nice_numbers is not None else _DEFAULT_Q
        self._w = (
            merged_weights["simplicity"],
            merged_weights["coverage"],
            merged_weights["density"],
            merged_weights["legibility"],
        )
        self._placement = _placement_ends(placement, self.PLACEMENTS, "TalbotLocator")
        # mizani checks the weights and placement when a search is built, and
        # searches are built per draw; build one now so a bad value fails at
        # the call, not at the first draw.
        self._breaks(_UNBOUND_N, self._placement)
        self._unit = float(unit)

    def _breaks(self, n: int, placement: PlacementPair) -> Callable:
        return breaks_extended(n=n, Q=self._q, w=self._w, placement=placement)

    def _ticks(self, vmin: float, vmax: float, n: int) -> np.ndarray:
        """Search in unit space with each end held by its placement."""
        u = self._unit
        return self._breaks(n, self._placement)((vmin / u, vmax / u)) * u

    def __call__(self) -> np.ndarray:  # ty: ignore[invalid-method-override]
        """Return tick locations computed from the axis's visible data."""
        dmin, dmax = visible_interval(self.axis)  # ty: ignore[invalid-argument-type]
        if not np.isfinite([dmin, dmax]).all():
            view = self.axis.get_view_interval()  # ty: ignore[unresolved-attribute]
            return np.asarray(AutoLocator().tick_values(*view))
        return self.tick_values(dmin, dmax)

    def tick_values(  # ty: ignore[invalid-method-override]
        self, vmin: float, vmax: float, n: int | None = None
    ) -> np.ndarray:
        """Return tick locations inside `[vmin, vmax]`.

        Parameters
        ----------
        vmin, vmax : float
            Interval bounds. Swapped if given in reverse order;
            degenerate values fall back to `AutoLocator`.
        n : int, optional
            The number of ticks to aim for; `None` resolves it with
            `target` from the bound axis.

        Returns
        -------
        ndarray
            Tick locations.
        """
        if vmin > vmax:
            vmin, vmax = vmax, vmin
        if not np.isfinite([vmin, vmax]).all() or vmin == vmax:
            return np.asarray(AutoLocator().tick_values(*self.nonsingular(vmin, vmax)))
        if n is None:
            n = self.target()
        try:
            ticks = self._ticks(vmin, vmax, n)
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
        frame regardless of margin padding; with one loose end, only
        that end takes the tick and the other keeps the proposed
        limit. Otherwise `vmin`, `vmax`
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
        interval = None
        if self.axis is not None:
            dmin, dmax = self.axis.get_data_interval()
            interval = (float(dmin), float(dmax))
        return self.view_limits_over(vmin, vmax, interval)

    def view_limits_over(
        self,
        vmin: float,
        vmax: float,
        interval: tuple[float, float] | None,
        n: int | None = None,
    ) -> tuple[float, float]:
        """Return view limits for `vmin`..`vmax`, covering `interval` when loose.

        The body of `view_limits` with the data interval passed in instead
        of read from `self.axis`, so a group of axes can be covered as one:
        `interval` is the data span the loose view must enclose, or `None`
        when no data is known.

        Parameters
        ----------
        vmin, vmax : float
            The proposed view limits.
        interval : tuple of float or None
            The data interval a loose locator covers edge to edge.
        n : int, optional
            The number of ticks to aim for; `None` resolves it with
            `target` from the bound axis.

        Returns
        -------
        tuple of float
            Lower and upper view limits.
        """
        if vmin > vmax:
            vmin, vmax = vmax, vmin
        if n is None:
            n = self.target()

        if self._placement != ("inside", "inside") and interval is not None:
            dmin, dmax = interval
            if np.isfinite([dmin, dmax]).all() and dmin != dmax:
                try:
                    ticks = self._ticks(dmin, dmax, n)
                    if ticks.size >= 2:
                        return _placed_limits(
                            ticks, vmin, vmax, (dmin, dmax), self._placement
                        )
                except (OverflowError, ValueError, FloatingPointError):
                    pass
                return super().view_limits(vmin, vmax)

        if mpl.rcParams["axes.autolimit_mode"] != "round_numbers":
            return super().view_limits(vmin, vmax)
        if not np.isfinite([vmin, vmax]).all() or vmin == vmax:
            return super().view_limits(vmin, vmax)
        try:
            u = self._unit
            ticks = self._breaks(n, ("loose", "loose"))((vmin / u, vmax / u))
            if ticks.size >= 2:
                return float(ticks[0]) * u, float(ticks[-1]) * u
        except (OverflowError, ValueError, FloatingPointError):
            pass
        return super().view_limits(vmin, vmax)


class LogBreaksLocator(BreaksLocator):
    """Place ticks on integer powers inside the data range of a log axis.

    Delegates to `mizani.breaks.breaks_log`, which returns breaks at
    integer powers of `base` (with a sub-decade fallback for narrow
    ranges) that may overflow the interval; the overflow is filtered
    away so every tick lies within the interval. When used on an axis,
    ticks are computed from the data interval, not the view interval,
    which is what lets a range frame hug the data.

    With `placement='loose'`, keeps the covering breaks and extends the
    grid outward by whole multiplicative steps so the outermost ticks
    bound the interval. A pair `(low, high)` frees each end on its own.

    Parameters
    ----------
    spacing : float, optional
        The gap to aim for between ticks, in tick-label heights. See
        `BreaksLocator`.
    n : int, optional
        The number of ticks to aim for, overriding `spacing`. See
        `BreaksLocator`.
    placement : {'inside', 'loose'} or tuple of two of them
        `'loose'` extends the tick grid outward by whole multiplicative
        steps so the outermost ticks bound the data interval; `'inside'`
        cuts them back inside it. A pair `(low, high)` sets each end on
        its own. `'flexible'` is linear-only and raises. Default
        `'inside'`.
    base : float
        Base of the logarithm, matching the axis scale's base.
    """

    PLACEMENTS: ClassVar[tuple[Placement, ...]] = ("inside", "loose")

    def __init__(
        self,
        spacing: float | None = None,
        n: int | None = None,
        placement: Placement | PlacementPair = "inside",
        base: float = 10,
    ) -> None:
        super().__init__(spacing, n)
        self._placement = _placement_ends(
            placement, self.PLACEMENTS, type(self).__name__
        )
        self._base = base

    def _breaks(self, n: int) -> Callable:
        return breaks_log(n=n, base=self._base)

    def _ticks(self, vmin: float, vmax: float, n: int) -> np.ndarray:
        """Covering breaks, extended at a loose end and cut back at the others."""
        ticks = np.asarray(self._breaks(n)((vmin, vmax)), dtype=float)
        ticks = ticks[ticks > 0]
        loose = (self._placement[0] == "loose", self._placement[1] == "loose")
        ticks = _extend_to_cover_log(ticks, vmin, vmax, loose)
        keep = np.ones(ticks.size, dtype=bool)
        if not loose[0]:
            keep &= ticks >= vmin * (1 - 1e-9)
        if not loose[1]:
            keep &= ticks <= vmax * (1 + 1e-9)
        return ticks[keep]

    def nonsingular(  # ty: ignore[invalid-method-override]
        self, vmin: float, vmax: float
    ) -> tuple[float, float]:
        """Expand a degenerate interval multiplicatively, as a log scale needs."""
        return _sanitize_log_interval(vmin, vmax, self._base)

    def __call__(self) -> np.ndarray:  # ty: ignore[invalid-method-override]
        """Return tick locations computed from the axis's visible data."""
        dmin, dmax = self.axis.get_data_interval()  # ty: ignore[unresolved-attribute]
        if dmin <= 0:
            dmin = self.axis.get_minpos()  # ty: ignore[unresolved-attribute]
        dmin, dmax = visible_interval(self.axis, (dmin, dmax))  # ty: ignore[invalid-argument-type]
        if not np.isfinite([dmin, dmax]).all():
            view = self.axis.get_view_interval()  # ty: ignore[unresolved-attribute]
            return _log_fallback(view[0], view[1], self._base)
        return self.tick_values(dmin, dmax)

    def tick_values(  # ty: ignore[invalid-method-override]
        self, vmin: float, vmax: float, n: int | None = None
    ) -> np.ndarray:
        """Return tick locations inside `[vmin, vmax]`.

        Parameters
        ----------
        vmin, vmax : float
            Interval bounds. Swapped if given in reverse order;
            degenerate or nonpositive values fall back to decade ticks
            from `LogLocator` on a sanitized interval.
        n : int, optional
            The number of ticks to aim for; `None` resolves it with
            `target` from the bound axis.

        Returns
        -------
        ndarray
            Tick locations.
        """
        if vmin > vmax:
            vmin, vmax = vmax, vmin
        if not np.isfinite([vmin, vmax]).all() or vmin <= 0 or vmin == vmax:
            return _log_fallback(vmin, vmax, self._base)
        if n is None:
            n = self.target()
        try:
            ticks = self._ticks(vmin, vmax, n)
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
        interval = None
        if self.axis is not None:
            dmin, dmax = self.axis.get_data_interval()
            if dmin <= 0:
                dmin = self.axis.get_minpos()
            interval = (float(dmin), float(dmax))
        return self.view_limits_over(vmin, vmax, interval)

    def view_limits_over(
        self,
        vmin: float,
        vmax: float,
        interval: tuple[float, float] | None,
        n: int | None = None,
    ) -> tuple[float, float]:
        """Return view limits for `vmin`..`vmax`, covering `interval` when loose.

        The body of `view_limits` with the data interval passed in instead
        of read from `self.axis`, so a group of axes can be covered as one:
        `interval` is the data span the loose view must enclose, or `None`
        when no data is known.

        Parameters
        ----------
        vmin, vmax : float
            The proposed view limits.
        interval : tuple of float or None
            The data interval a loose locator covers edge to edge.
        n : int, optional
            The number of ticks to aim for; `None` resolves it with
            `target` from the bound axis.

        Returns
        -------
        tuple of float
            Lower and upper view limits.
        """
        if vmin > vmax:
            vmin, vmax = vmax, vmin
        if n is None:
            n = self.target()
        breaks = self._breaks(n)

        if self._placement != ("inside", "inside") and interval is not None:
            dmin, dmax = interval
            if np.isfinite([dmin, dmax]).all() and 0 < dmin < dmax:
                try:
                    ticks = self._ticks(dmin, dmax, n)
                    if ticks.size >= 2:
                        return _placed_limits(
                            ticks, vmin, vmax, (dmin, dmax), self._placement
                        )
                except (OverflowError, ValueError, FloatingPointError):
                    pass
            return super().view_limits(vmin, vmax)

        if mpl.rcParams["axes.autolimit_mode"] != "round_numbers":
            return super().view_limits(vmin, vmax)
        if not np.isfinite([vmin, vmax]).all() or vmin <= 0 or vmin == vmax:
            return super().view_limits(vmin, vmax)
        try:
            ticks = np.asarray(breaks((vmin, vmax)), dtype=float)
            if ticks.size >= 2:
                ticks = _extend_to_cover_log(ticks, vmin, vmax)
                return float(ticks[0]), float(ticks[-1])
        except (OverflowError, ValueError, FloatingPointError):
            pass
        return super().view_limits(vmin, vmax)


# mizani's by_n floors each grid to the data's start unless the interval is
# a multiple of a parent unit. Two of its intervals fall on the wrong side
# of that rule: a 2-month grid floors to the data's month and a 2-hour grid
# to the data's hour, so both follow the start's parity and can skip 1
# January or midnight. Every other interval either floors to a parent
# (anchoring it) or visits every sub-unit. We keep mizani's choice
# everywhere except those two, replacing each with the anchoring interval of
# the same unit whose tick count is nearest the target.
_DRIFTING_STEPS = {
    # relativedelta (years, months, days, hours, mins, secs, us) -> anchoring
    (0, 2, 0, 0, 0, 0, 0): ("months", (1, 3, 4, 6)),
    (0, 0, 0, 2, 0, 0, 0): ("hours", (1, 3, 4, 6, 12)),
}
_UNIT_SECONDS = {"months": 30.44 * 86400.0, "hours": 3600.0}


def _anchoring_width(
    dates: Sequence[datetime.datetime],
    lo: datetime.datetime,
    hi: datetime.datetime,
    n: int,
) -> str | None:
    """Width to use in place of a grid that drifts with the data start.

    Returns ``None`` when mizani's grid does not drift, so the caller keeps
    it unchanged. When the grid is one of the two drifting steps, returns
    the ``"<multiple> <unit>"`` width of the same-unit interval whose tick
    count over ``lo``..``hi`` is closest to ``n``.
    """
    if len(dates) < 2:
        return None
    step = relativedelta(dates[1], dates[0])
    key = (
        step.years,
        step.months,
        step.days,
        step.hours,
        step.minutes,
        step.seconds,
        step.microseconds,
    )
    match = _DRIFTING_STEPS.get(key)
    if match is None:
        return None
    unit, multiples = match
    span = (hi - lo).total_seconds() / _UNIT_SECONDS[unit]
    best = min(multiples, key=lambda m: abs(span / m - n))
    return f"{best} {unit}"


class DateBreaksLocator(BreaksLocator):
    """Place ticks on calendar-nice dates inside the data range of a date axis.

    Delegates to `mizani.breaks.breaks_date`, which returns breaks at
    calendar-nice positions (year, month, day, hour, ... starts) that
    may overflow the interval; the overflow is filtered away so every
    tick lies within the interval. When used on an axis, ticks are
    computed from the data interval, not the view interval, which is
    what lets a range frame hug the data.

    Tick positions are floats in matplotlib date units; the interval is
    converted to datetimes at the boundary with `matplotlib.dates`, so
    any matplotlib epoch setting is respected.

    With `placement='loose'`, keeps the covering breaks so the outermost
    ticks bound the interval. A pair `(low, high)` frees each end on its
    own.

    Parameters
    ----------
    spacing : float, optional
        The gap to aim for between ticks, in tick-label heights. See
        `BreaksLocator`.
    n : int, optional
        The number of ticks to aim for, overriding `spacing`. See
        `BreaksLocator`.
    placement : {'inside', 'loose'} or tuple of two of them
        `'loose'` keeps the covering breaks so the outermost ticks bound
        the data interval; `'inside'` cuts them back inside it. A pair
        `(low, high)` sets each end on its own. `'flexible'` is
        linear-only and raises. Default `'inside'`.
    """

    PLACEMENTS: ClassVar[tuple[Placement, ...]] = ("inside", "loose")

    def __init__(
        self,
        spacing: float | None = None,
        n: int | None = None,
        placement: Placement | PlacementPair = "inside",
    ) -> None:
        super().__init__(spacing, n)
        self._placement = _placement_ends(
            placement, self.PLACEMENTS, type(self).__name__
        )

    def _ticks(self, vmin: float, vmax: float, n: int) -> np.ndarray:
        """Covering breaks, cut back inside the interval at each end not loose."""
        ticks = self._covering_breaks(vmin, vmax, n)
        tol = 1e-9 * (vmax - vmin)
        keep = np.ones(ticks.size, dtype=bool)
        if self._placement[0] != "loose":
            keep &= ticks >= vmin - tol
        if self._placement[1] != "loose":
            keep &= ticks <= vmax + tol
        return ticks[keep]

    def __call__(self) -> np.ndarray:  # ty: ignore[invalid-method-override]
        """Return tick locations computed from the axis's visible data."""
        dmin, dmax = visible_interval(self.axis)  # ty: ignore[invalid-argument-type]
        if not np.isfinite([dmin, dmax]).all():
            view = self.axis.get_view_interval()  # ty: ignore[unresolved-attribute]
            return _date_fallback(view[0], view[1])
        return self.tick_values(dmin, dmax)

    def tick_values(  # ty: ignore[invalid-method-override]
        self, vmin: float, vmax: float, n: int | None = None
    ) -> np.ndarray:
        """Return tick locations inside `[vmin, vmax]`.

        Parameters
        ----------
        vmin, vmax : float
            Interval bounds in matplotlib date units. Swapped if given
            in reverse order; degenerate or out-of-calendar values fall
            back to `AutoDateLocator` on a sanitized interval.
        n : int, optional
            The number of ticks to aim for; `None` resolves it with
            `target` from the bound axis.

        Returns
        -------
        ndarray
            Tick locations.
        """
        if vmin > vmax:
            vmin, vmax = vmax, vmin
        if not np.isfinite([vmin, vmax]).all() or vmin == vmax:
            return _date_fallback(vmin, vmax)
        if n is None:
            n = self.target()
        try:
            ticks = self._ticks(vmin, vmax, n)
        except (OverflowError, ValueError, FloatingPointError):
            return _date_fallback(vmin, vmax)
        if ticks.size == 0:
            return _date_fallback(vmin, vmax)
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
            The proposed view limits, in matplotlib date units.

        Returns
        -------
        tuple of float
            Lower and upper view limits.
        """
        interval = None
        if self.axis is not None:
            dmin, dmax = self.axis.get_data_interval()
            interval = (float(dmin), float(dmax))
        return self.view_limits_over(vmin, vmax, interval)

    def view_limits_over(
        self,
        vmin: float,
        vmax: float,
        interval: tuple[float, float] | None,
        n: int | None = None,
    ) -> tuple[float, float]:
        """Return view limits for `vmin`..`vmax`, covering `interval` when loose.

        The body of `view_limits` with the data interval passed in instead
        of read from `self.axis`, so a group of axes can be covered as one:
        `interval` is the data span the loose view must enclose, or `None`
        when no data is known.

        Parameters
        ----------
        vmin, vmax : float
            The proposed view limits, in matplotlib date units.
        interval : tuple of float or None
            The data interval a loose locator covers edge to edge, in
            matplotlib date units.
        n : int, optional
            The number of ticks to aim for; `None` resolves it with
            `target` from the bound axis.

        Returns
        -------
        tuple of float
            Lower and upper view limits.
        """
        if vmin > vmax:
            vmin, vmax = vmax, vmin
        if n is None:
            n = self.target()

        if self._placement != ("inside", "inside") and interval is not None:
            dmin, dmax = interval
            if np.isfinite([dmin, dmax]).all() and dmin != dmax:
                try:
                    ticks = self._ticks(dmin, dmax, n)
                    if ticks.size >= 2:
                        return _placed_limits(
                            ticks, vmin, vmax, (dmin, dmax), self._placement
                        )
                except (OverflowError, ValueError, FloatingPointError):
                    pass
            return super().view_limits(vmin, vmax)

        if mpl.rcParams["axes.autolimit_mode"] != "round_numbers":
            return super().view_limits(vmin, vmax)
        if not np.isfinite([vmin, vmax]).all() or vmin == vmax:
            return super().view_limits(vmin, vmax)
        try:
            ticks = self._covering_breaks(vmin, vmax, n)
            if ticks.size >= 2:
                return float(ticks[0]), float(ticks[-1])
        except (OverflowError, ValueError, FloatingPointError):
            pass
        return super().view_limits(vmin, vmax)

    def _covering_breaks(self, vmin: float, vmax: float, n: int) -> np.ndarray:
        lo, hi = num2date(vmin), num2date(vmax)
        dates = breaks_date(n=n)((lo, hi))
        width = _anchoring_width(dates, lo, hi, n)
        if width is not None:
            dates = breaks_date_width(width)((lo, hi))
        return np.asarray(date2num(dates), dtype=float)


class FeatureLocator(FixedLocator):
    """Place ticks at features of the paired `(x, y)` data.

    Each feature is a callable `(x, y) -> float | ndarray` returning a
    position (or positions) on the axis this locator is attached to.
    Because a feature such as a peak is a different coordinate on each
    axis (`x[argmax(y)]` on the x-axis, `y[argmax(y)]` on the y-axis),
    the feature is written for the axis it labels; the locator does not
    project. This is what a single-axis reduction cannot express, so it
    lives here rather than in `SummaryLocator`: the classic Doumont
    resonance plot labels the peak with
    `FeatureLocator(x, y, [lambda x, y: x[np.argmax(y)]])`.

    The arrays are captured at construction. The features' results are
    flattened, non-finite positions dropped, and coincident positions
    collapsed to a single tick, since a tick cannot show multiplicity.
    Inputs are not cleaned: a feature over arbitrary `(x, y)` has no
    universal non-finite policy, so the feature owns it (use
    `np.nanargmax`, or filter the pair first). Tick labels follow the
    axis formatter; pass a format string such as
    `ax.xaxis.set_major_formatter("{x:.1f}")` to round them.

    Parameters
    ----------
    x, y : array-like
        The plotted coordinates the features read.
    features : sequence of callable or number
        Callables `(x, y) -> float | ndarray` giving tick positions on
        the labelled axis. A plain number (or array) is taken as a fixed
        position, so a constant baseline can sit beside a computed
        feature, as in `[0, lambda x, y: y.max()]`.

    Raises
    ------
    ValueError
        If the features yield no finite position.
    """

    def __init__(
        self,
        x: ArrayLike,
        y: ArrayLike,
        features: Sequence[Callable[..., ArrayLike] | ArrayLike]
        | Mapping[str, Callable[..., float] | float],
    ) -> None:
        xs = np.asarray(x, dtype=float).ravel()
        ys = np.asarray(y, dtype=float).ravel()
        positions, names = _named_positions(features, xs, ys)
        super().__init__(positions)
        self._feature_names = names

    @property
    def feature_names(self) -> dict[float, tuple[str, ...]]:
        """Map from each named feature's position to its name(s); empty if nameless."""
        return dict(self._feature_names)


class SummaryLocator(FixedLocator):
    """Place ticks at summaries of one axis's own values.

    Each reducer is a callable `values -> float | ndarray` (mean,
    median, any percentile, a custom statistic). This is the
    single-axis special case of `FeatureLocator`: a reducer is a
    feature that ignores the other axis, so both funnel through the
    same flatten, drop-non-finite, and collapse-coincident pipeline.
    Unlike `FeatureLocator`, the input is cleaned first: non-finite
    values are dropped before the reducers run. Tick labels follow the
    axis formatter; pass a format string such as
    `ax.xaxis.set_major_formatter("{x:.1f}")` to round them.

    Parameters
    ----------
    values : array-like
        The plotted values whose summaries the ticks mark.
    reducers : sequence of callable or number
        Callables `values -> float | ndarray` giving tick positions. A
        plain number (or array) is taken as a fixed position.

    Raises
    ------
    ValueError
        If `values` contains no finite value.
    """

    def __init__(
        self,
        values: ArrayLike,
        reducers: Sequence[Callable[..., ArrayLike] | ArrayLike]
        | Mapping[str, Callable[..., float] | float],
    ) -> None:
        vals = np.asarray(values, dtype=float).ravel()
        vals = vals[np.isfinite(vals)]
        if vals.size == 0:
            raise ValueError("data has no finite values")
        positions, names = _named_positions(reducers, vals)
        super().__init__(positions)
        self._feature_names = names

    @property
    def feature_names(self) -> dict[float, tuple[str, ...]]:
        """Map from each named reducer's position to its name(s); empty if nameless."""
        return dict(self._feature_names)


class QuartileLocator(SummaryLocator):
    """Place ticks at the five-number summary of `data`.

    The `SummaryLocator` preset whose reducers are the minimum, first
    quartile, median, third quartile, and maximum, turning a range
    frame into Tufte's quartile plot. Non-finite values are ignored.
    Coincident quantiles collapse to a single tick, since a tick cannot
    show multiplicity. Tick labels follow the axis formatter; pass a
    format string such as `ax.xaxis.set_major_formatter("{x:.1f}")` to
    round them.

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
        quantiles = {"min": 0.0, "Q1": 0.25, "median": 0.5, "Q3": 0.75, "max": 1.0}
        super().__init__(
            data,
            {name: (lambda v, p=p: np.quantile(v, p)) for name, p in quantiles.items()},
        )


class AugmentedLocator(Locator):
    """Place ticks at the union of a base locator's ticks and fixed extra ticks.

    The `base` locator is the live side: its ticks are read fresh each
    draw (a `TalbotLocator`/`LogBreaksLocator`/`DateBreaksLocator` reads
    the axis data interval), and it alone owns the view limits and
    singularity handling. `extra` is the fixed side, any `FixedLocator`
    (so `FeatureLocator`, `SummaryLocator`, `QuartileLocator` fit
    directly) or a bare sequence of positions, wrapped in a
    `FixedLocator`. The two tick sets are concatenated, non-finite
    positions dropped, and coincident positions collapsed to a single
    tick.

    Extra ticks are expected to lie within the view; an out-of-range
    extra tick is kept as given and behaves like any out-of-range tick.
    Ticks are not projected across axes: the base and extra are read on
    the axis this locator is attached to.

    Parameters
    ----------
    base : matplotlib.ticker.Locator
        The live locator whose ticks the extra ticks augment; owns the
        view limits and singularity handling.
    extra : matplotlib.ticker.Locator or sequence of float
        Fixed extra tick positions. A `FixedLocator` (or a `FeatureLocator`
        / `SummaryLocator` / `QuartileLocator`, which subclass it), or a
        sequence taken as fixed positions.
    """

    def __init__(self, base: Locator, extra: Locator | Sequence[float]) -> None:
        self._base = base
        self._extra = extra if isinstance(extra, Locator) else FixedLocator(list(extra))

    @property
    def extra(self) -> Locator:
        """The fixed side whose ticks augment the base."""
        return self._extra

    @property
    def feature_names(self) -> dict[float, tuple[str, ...]]:
        """The `extra` side's `position -> names` map, or empty if it has none."""
        return getattr(self._extra, "feature_names", {})

    def __call__(self) -> np.ndarray:  # ty: ignore[invalid-method-override]
        """Return the union of the base and extra tick positions."""
        return np.asarray(
            self.raise_if_exceeds(_union(self._base(), self._extra()).tolist())
        )

    def tick_values(  # ty: ignore[invalid-method-override]
        self, vmin: float, vmax: float
    ) -> np.ndarray:
        """Return the union of the base and extra ticks over `[vmin, vmax]`."""
        return _union(
            self._base.tick_values(vmin, vmax), self._extra.tick_values(vmin, vmax)
        )

    def set_axis(self, axis: Axis) -> None:  # ty: ignore[invalid-method-override]
        """Bind the axis, forwarding to base and extra so both can read it."""
        super().set_axis(axis)
        self._base.set_axis(axis)
        self._extra.set_axis(axis)

    def view_limits(self, vmin: float, vmax: float) -> tuple[float, float]:
        """View limits from the base alone; the extra never moves the view."""
        return self._base.view_limits(vmin, vmax)

    def nonsingular(  # ty: ignore[invalid-method-override]
        self, vmin: float, vmax: float
    ) -> tuple[float, float]:
        """Delegate degenerate-interval handling to the base."""
        return self._base.nonsingular(vmin, vmax)


def _union(*locs: ArrayLike) -> np.ndarray:
    """Concatenate tick arrays, drop non-finite, collapse coincident, sort."""
    parts = [np.asarray(a, dtype=float).ravel() for a in locs]
    values = np.concatenate(parts) if parts else np.empty(0)
    return np.unique(values[np.isfinite(values)])


def _tick_positions(
    reducers: Sequence[Callable[..., ArrayLike] | ArrayLike], *data: np.ndarray
) -> list[float]:
    parts = [
        np.asarray(
            # ty: ignore[call-top-callable]; callable() narrowing over the
            # Callable | ArrayLike union leaves a top callable ty won't call.
            reducer(*data) if callable(reducer) else reducer,
            dtype=float,
        ).ravel()
        for reducer in reducers
    ]
    values = np.concatenate(parts) if parts else np.empty(0)
    values = values[np.isfinite(values)]
    if values.size == 0:
        raise ValueError("reducers produced no finite tick positions")
    # tolist: FixedLocator's stub wants Sequence[float], which an ndarray
    # does not satisfy structurally.
    return np.unique(values).tolist()


def _named_positions(
    entries: Sequence[Callable[..., ArrayLike] | ArrayLike]
    | Mapping[str, Callable[..., float] | float],
    *data: np.ndarray,
) -> tuple[list[float], dict[float, tuple[str, ...]]]:
    """Positions plus a `position -> names` map from named or nameless entries.

    A `Mapping` names each entry (one name, one scalar position); a
    `Sequence` is nameless and may yield arrays. Positions follow the
    same flatten, drop-non-finite, collapse-coincident pipeline as
    `_tick_positions`; the map carries identity past the collapse, so
    coincident named positions collapse to a tuple of their names.
    """
    if isinstance(entries, Mapping):
        items: list[tuple[str | None, Callable[..., ArrayLike] | ArrayLike]] = [
            (name, entry) for name, entry in entries.items()
        ]
    else:
        items = [(None, entry) for entry in entries]

    pairs: list[tuple[float, str | None]] = []
    for name, entry in items:
        # ty: ignore[call-top-callable]; same top-callable narrowing as _tick_positions.
        arr = np.asarray(
            entry(*data) if callable(entry) else entry, dtype=float
        ).ravel()
        if name is not None and arr.size != 1:
            raise ValueError(
                f"named feature {name!r} must yield one position, got {arr.size}"
            )
        pairs.extend((float(value), name) for value in arr)

    finite = [(v, n) for v, n in pairs if np.isfinite(v)]
    if not finite:
        raise ValueError("reducers produced no finite tick positions")
    positions = np.unique([v for v, _ in finite]).tolist()
    names: dict[float, tuple[str, ...]] = {}
    for value, name in finite:
        if name is not None:
            names[value] = (*names.get(value, ()), name)
    return positions, names


def visible_interval(
    axis: Axis, interval: tuple[float, float] | None = None
) -> tuple[float, float]:
    """Return the axis's data interval cut back to its view.

    A view wider than the data leaves it unchanged, so an autoscaled
    axis reads its data as before. A view pinned inside the data crops
    it to the data on screen, which is what a `set_xlim` after
    `range_frame` means. A view lying entirely outside the data yields a
    non-finite pair, the same reading as no data at all. `interval`
    stands in for the data interval when the caller has already
    adjusted it, as a log axis does for a nonpositive minimum.
    """
    if interval is None:
        interval = axis.get_data_interval()
    dmin, dmax = (float(v) for v in interval)
    vmin, vmax = sorted(float(v) for v in axis.get_view_interval())
    lo, hi = max(dmin, vmin), min(dmax, vmax)
    if lo > hi:
        return (np.nan, np.nan)
    return (lo, hi)


def _placement_ends(
    placement: Placement | PlacementPair, allowed: tuple[Placement, ...], owner: str
) -> PlacementPair:
    """Read `placement` as a `(low, high)` pair, each end one of `allowed`."""
    pair = (placement, placement) if isinstance(placement, str) else tuple(placement)
    if len(pair) != 2 or any(p not in allowed for p in pair):
        linear_only = "; flexible needs a linear axis" if "flexible" in pair else ""
        raise ValueError(
            f"{owner} takes placement {allowed} or a (low, high) pair of them, "
            f"got {placement!r}{linear_only}"
        )
    return pair


def _placed_limits(
    ticks: np.ndarray,
    vmin: float,
    vmax: float,
    interval: tuple[float, float],
    placement: PlacementPair,
) -> tuple[float, float]:
    """Return view limits reaching each outermost tick the placement lets past the data.

    A loose end always takes its outermost tick; a flexible end takes it
    only when it lies past the data, and otherwise keeps the proposed
    limit, as an inside end does. "Past" allows `1e-9 * step` of float
    dust: mizani returns `-0.30000000000000004` for a tick at `-0.3`,
    which a raw comparison would read as past the data, dropping the
    margin. `ticks` has at least two entries (the callers check).
    """
    dmin, dmax = interval
    low, high = float(ticks[0]), float(ticks[-1])
    tol = 1e-9 * float(ticks[1] - ticks[0])
    past_low = low < dmin - tol
    past_high = high > dmax + tol
    reach_low = placement[0] == "loose" or (placement[0] == "flexible" and past_low)
    reach_high = placement[1] == "loose" or (placement[1] == "flexible" and past_high)
    return (low if reach_low else vmin, high if reach_high else vmax)


def _extend_to_cover_log(
    ticks: np.ndarray,
    vmin: float,
    vmax: float,
    ends: tuple[bool, bool] = (True, True),
) -> np.ndarray:
    if ticks.size < 2:
        return ticks
    out = [float(t) for t in ticks]
    diffs = np.diff(out)
    ratios = np.asarray(out[1:]) / np.asarray(out[:-1])
    # `breaks_log` steps by a constant factor across decades but by a constant
    # amount inside one (1.1, 1.3, 1.5), so extend along whichever progression
    # the grid follows. Two ticks fit both, and on a log axis the geometric
    # reading is the right one, so only three or more can name it arithmetic.
    arithmetic = bool(
        len(out) >= 3
        and np.allclose(diffs, diffs[0], rtol=1e-9)
        and not np.allclose(ratios, ratios[0], rtol=1e-9)
    )
    step, ratio = float(diffs[0]), float(ratios[0])
    if not arithmetic and not (np.isfinite(ratio) and ratio > 1):
        return np.asarray(out)
    if ends[0]:
        while out[0] > vmin * (1 + 1e-9):
            below = out[0] - step if arithmetic else out[0] / ratio
            if not np.isfinite(below) or below <= 0 or below >= out[0]:
                break
            out.insert(0, below)
    if ends[1]:
        while out[-1] < vmax * (1 - 1e-9):
            above = out[-1] + step if arithmetic else out[-1] * ratio
            if not np.isfinite(above) or above <= out[-1]:
                break
            out.append(above)
    return np.asarray(out)


def _sanitize_log_interval(
    vmin: float, vmax: float, base: float
) -> tuple[float, float]:
    if vmin > vmax:
        vmin, vmax = vmax, vmin
    if not np.isfinite([vmin, vmax]).all() or vmax <= 0:
        vmin, vmax = 1.0, base
    elif vmin <= 0:
        vmin = vmax / base**2
    if vmin == vmax:
        with np.errstate(over="ignore"):
            expanded = vmin / base, vmax * base
        vmin, vmax = expanded if np.isfinite(expanded[1]) else (1.0, base)
    return vmin, vmax


def _sanitize_date_interval(vmin: float, vmax: float) -> tuple[float, float]:
    # mizani's break rounding can step outside years 1-9999, so clip
    # well inside the calendar rather than to its exact edges.
    lo = date2num(datetime.datetime(1000, 1, 1))
    hi = date2num(datetime.datetime(9000, 1, 1))
    if vmin > vmax:
        vmin, vmax = vmax, vmin
    if not np.isfinite([vmin, vmax]).all():
        vmin, vmax = 0.0, 1.0
    vmin = float(np.clip(vmin, lo, hi))
    vmax = float(np.clip(vmax, lo, hi))
    if vmin == vmax:
        vmin, vmax = vmin - 0.5, vmax + 0.5
    return vmin, vmax


def _date_fallback(vmin: float, vmax: float) -> np.ndarray:
    vmin, vmax = _sanitize_date_interval(vmin, vmax)
    try:
        dates = breaks_date(n=5)((num2date(vmin), num2date(vmax)))
        ticks = np.asarray(date2num(dates), dtype=float)
        if ticks.size:
            return ticks
    except (OverflowError, ValueError, FloatingPointError):
        pass
    return np.linspace(vmin, vmax, 5)


def _log_fallback(vmin: float, vmax: float, base: float) -> np.ndarray:
    vmin, vmax = _sanitize_log_interval(vmin, vmax, base)
    with np.errstate(over="ignore"):
        ticks = np.asarray(LogLocator(base=base).tick_values(vmin, vmax))
    return ticks[np.isfinite(ticks)]
