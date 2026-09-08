"""The range frame: trimmed spines and data-range ticks."""

import warnings
from collections.abc import Callable, Sequence
from typing import NamedTuple

import matplotlib.dates as mdates
import numpy as np
from matplotlib.axes import Axes
from matplotlib.axis import Axis
from matplotlib.ticker import NullLocator

from vanzelfsprekend.hook import add_applier, ensure_state, get_state, run_appliers
from vanzelfsprekend.locator import (
    SPACING,
    DateBreaksLocator,
    LogBreaksLocator,
    TalbotLocator,
    visible_interval,
)

FrameMode = str | tuple[str, str]
"""One axis's frame mode: a mode for both ends, or a `(low, high)` pair."""

MODES = ("nice", "data", "loose")


def range_frame(
    ax: Axes,
    frame: FrameMode | tuple[FrameMode, FrameMode] = "nice",
    spacing: float | tuple[float, float] = SPACING,
    n: int | None = None,
    offset: float | tuple[float | None, float | None] | None = None,
    nice_numbers: Sequence[float] | None = None,
    weights: dict[str, float] | None = None,
) -> Axes:
    """Turn `ax` into a range frame.

    Installs `TalbotLocator` (linear axes), `LogBreaksLocator` (log
    axes), or `DateBreaksLocator` plus a `ConciseDateFormatter` (date
    axes) on both axes, hiding minor ticks on log axes, hides the top
    and right spines, and keeps the left and bottom spine bounds glued
    to the data on every draw. Safe to call repeatedly; later calls
    update the settings instead of stacking hooks.

    Parameters
    ----------
    ax : matplotlib.axes.Axes
        The axes to modify, in place.
    frame : {'nice', 'data', 'loose'} or tuple of two of them
        `'nice'` ends the spines at the outermost ticks, `'data'` at
        the exact data minimum and maximum. `'loose'` ends the spines
        at nice numbers bounding the data (frame may extend up to one
        tick step beyond the data). A tuple `(x_mode, y_mode)` sets
        the bottom and left spine independently, and either entry may
        itself be a pair `(low, high)` setting that spine's two ends
        on their own: `(("loose", "data"), "nice")` runs the bottom
        spine from the tick below the data to the last observation.
        All three read the data cut back to the view, so a view pinned
        inside the data with `set_xlim` crops the frame to the data on
        screen, and a view wider than the data changes nothing.
    spacing : float or tuple of two floats
        The gap to aim for between ticks, in tick-label heights, so the
        number of ticks follows the axis's length and the labels' size:
        a small panel gets few, a poster's large labels thin them out.
        A tuple `(x_spacing, y_spacing)` sets the axes independently;
        the default `(7, 4)` is 70 pt and 40 pt at 10 pt labels, about
        2.5 cm and 1.4 cm, since an x label is three to five heights
        wide along its axis and a y label one. Halving the spacing
        doubles the ticks.
    n : int, optional
        The number of ticks to aim for per axis, overriding `spacing`.
    offset : float or tuple of (float or None), optional
        Outward displacement of the left and bottom spines, in points.
        A single number moves both spines; a tuple `(x_offset,
        y_offset)` moves the bottom and left spine independently, like
        `frame`. `None` (the whole argument, or either tuple element)
        resolves to 8 for a spine with a `'loose'` end and 0 otherwise.
    nice_numbers : sequence of float, optional
        Advanced pass-through to `TalbotLocator`; see there for details.
        Applies to linear axes only; ignored on log and date axes.
    weights : dict, optional
        Advanced pass-through to `TalbotLocator`; see there for details.
        Applies to linear axes only; ignored on log and date axes.

    Returns
    -------
    matplotlib.axes.Axes
        The same axes, for chaining.
    """
    mode, offsets = parse_frame_args(frame, offset)
    spacings = parse_spacing(spacing)
    snapshot_frame(ax)
    kinds: dict[str, AxisKind | None] = {
        "x": axis_kind(ax.xaxis),
        "y": axis_kind(ax.yaxis),
    }
    install_frame(
        ax,
        mode,
        offsets,
        n=n,
        spacing=spacings,
        nice_numbers=nice_numbers,
        weights=weights,
        kinds=kinds,
        stacklevel=3,
    )
    run_appliers(ax)
    return ax


def parse_frame_args(
    frame: FrameMode | tuple[FrameMode, FrameMode],
    offset: float | tuple[float | None, float | None] | None,
) -> tuple[dict[str, tuple[str, str]], dict[str, float]]:
    """Resolve `frame` and `offset` into per-axis end modes and spine offsets.

    Every axis comes out as a `(low, high)` pair of modes, whatever
    the spelling given.
    """
    invalid = ValueError(
        "frame must be 'nice', 'data' or 'loose', a tuple of two of them, or "
        "a tuple whose entries are each a mode or a (low, high) pair of "
        f"modes, got {frame!r}"
    )

    def ends(axis_mode: FrameMode) -> tuple[str, str]:
        pair = (
            (axis_mode, axis_mode) if isinstance(axis_mode, str) else tuple(axis_mode)
        )
        if len(pair) != 2 or any(m not in MODES for m in pair):
            raise invalid
        return pair

    modes = (frame, frame) if isinstance(frame, str) else tuple(frame)
    if len(modes) != 2:
        raise invalid
    mode = {"x": ends(modes[0]), "y": ends(modes[1])}
    if offset is None or isinstance(offset, (int, float)):
        per_offset = {"x": offset, "y": offset}
    else:
        pair = tuple(offset)
        if len(pair) != 2:
            raise ValueError(
                "offset must be a number, or a tuple of two (each a number or "
                f"None), got {offset!r}"
            )
        per_offset = {"x": pair[0], "y": pair[1]}
    offsets: dict[str, float] = {}
    for name in ("x", "y"):
        value = per_offset[name]
        offsets[name] = (8 if "loose" in mode[name] else 0) if value is None else value
    return mode, offsets


def parse_spacing(spacing: float | tuple[float, float]) -> dict[str, float]:
    """Resolve `spacing` into per-axis gaps, keyed `'x'` and `'y'`."""
    if isinstance(spacing, (int, float)):
        return {"x": spacing, "y": spacing}
    pair = tuple(spacing)
    if len(pair) != 2 or not all(isinstance(s, (int, float)) for s in pair):
        raise ValueError(
            f"spacing must be a number or a tuple of two numbers, got {spacing!r}"
        )
    return {"x": pair[0], "y": pair[1]}


def snapshot_frame(ax: Axes) -> None:
    """Record what the frame will change on `ax`, once.

    Taken before any locator is replaced. On axes that share a `Ticker`
    the snapshot of every sibling must exist before any sibling installs,
    or a later sibling records the first one's locator as its original;
    `group.treat` orders the calls that way.
    """
    state = ensure_state(ax)
    if "frame" in state:
        return
    state["frame"] = {
        "active": set(),
        "formatted": set(),
        "snapshot": {
            "locators": {
                "x": ax.xaxis.get_major_locator(),
                "y": ax.yaxis.get_major_locator(),
            },
            "minor_locators": {
                "x": ax.xaxis.get_minor_locator(),
                "y": ax.yaxis.get_minor_locator(),
            },
            "formatters": {
                "x": ax.xaxis.get_major_formatter(),
                "y": ax.yaxis.get_major_formatter(),
            },
            "top_visible": ax.spines["top"].get_visible(),
            "right_visible": ax.spines["right"].get_visible(),
            "left_position": ax.spines["left"].get_position(),
            "bottom_position": ax.spines["bottom"].get_position(),
        },
    }


def _is_date_converter(converter: object) -> bool:
    date_converters: tuple[type, ...] = (
        mdates.DateConverter,
        mdates.ConciseDateConverter,
    )
    switchable = getattr(mdates, "_SwitchableDateConverter", None)
    if switchable is not None:
        date_converters += (switchable,)
    return isinstance(converter, date_converters)


class AxisKind(NamedTuple):
    """What a locator needs to know about an axis: scale, date-ness, support."""

    scale: str
    is_date: bool
    supported: bool


def axis_kind(axis: Axis) -> AxisKind:
    """Read the kind of one axis: its scale, whether it holds dates, and support."""
    scale = axis.get_scale()
    converter = axis.get_converter()
    is_date = converter is not None and _is_date_converter(converter)
    supported = scale in ("linear", "log") and (converter is None or is_date)
    return AxisKind(scale, is_date, supported)


def install_frame(
    ax: Axes,
    mode: dict[str, tuple[str, str]],
    offsets: dict[str, float],
    n: int | None,
    spacing: dict[str, float],
    nice_numbers: Sequence[float] | None,
    weights: dict[str, float] | None,
    kinds: dict[str, AxisKind | None],
    stacklevel: int,
) -> None:
    """Install the frame on `ax` given each axis's kind.

    Registers the frame applier but does not run it; `snapshot_frame`
    must have run on `ax` first.

    Parameters
    ----------
    ax : matplotlib.axes.Axes
        The axes to modify, in place.
    mode, offsets, spacing : dict
        Per-axis `(low, high)` frame modes, spine offset and tick
        spacing, keyed `'x'` and `'y'`, from `parse_frame_args` and
        `parse_spacing`.
    n, nice_numbers, weights
        Locator settings; see `range_frame`.
    kinds : dict
        Per-axis `AxisKind`, or `None` for an axis the caller decided
        to leave alone (a group that disagrees on kind; the caller has
        warned or raised). An unsupported kind warns here, as it always
        has, and is left alone too.
    stacklevel : int
        The depth of the caller the warnings must point at, counted
        from this function.
    """
    frame_state = get_state(ax)["frame"]  # ty: ignore[not-subscriptable]
    frame_state["mode"] = mode
    active = set()
    for name, axis in (("x", ax.xaxis), ("y", ax.yaxis)):
        kind = kinds[name]
        if kind is None:
            continue
        if kind.scale not in ("linear", "log"):
            warnings.warn(
                f"vanzelfsprekend: {name}-axis has scale {kind.scale!r}; "
                "only linear and log axes are supported, leaving it untouched",
                stacklevel=stacklevel,
            )
            continue
        if not kind.supported:
            warnings.warn(
                f"vanzelfsprekend: {name}-axis has a units converter; "
                "only plain and date axes are supported, leaving it untouched",
                stacklevel=stacklevel,
            )
            continue
        loose = (mode[name][0] == "loose", mode[name][1] == "loose")
        if kind.is_date:
            locator = DateBreaksLocator(n=n, spacing=spacing[name], loose=loose)
            axis.set_major_locator(locator)
            axis.set_major_formatter(mdates.ConciseDateFormatter(locator))
            frame_state["formatted"].add(name)
        elif kind.scale == "log":
            axis.set_major_locator(
                LogBreaksLocator(
                    n=n,
                    spacing=spacing[name],
                    loose=loose,
                    base=axis.get_transform().base,  # ty: ignore[unresolved-attribute]
                )
            )
            axis.set_minor_locator(NullLocator())
        else:
            axis.set_major_locator(
                TalbotLocator(
                    n=n,
                    spacing=spacing[name],
                    loose=loose,
                    nice_numbers=nice_numbers,
                    weights=weights,
                )
            )
        active.add(name)
    frame_state["active"] = active

    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    ax.spines["left"].set_position(("outward", offsets["y"]))
    ax.spines["bottom"].set_position(("outward", offsets["x"]))

    add_applier(ax, "frame", _apply_frame)


def _apply_frame(ax: Axes) -> bool:
    state = get_state(ax)
    if state is None or "frame" not in state:
        return False
    frame_state = state["frame"]
    changed = False
    overrides = frame_state.get("intervals", {})
    for name, axis, spine_name in (
        ("x", ax.xaxis, "bottom"),
        ("y", ax.yaxis, "left"),
    ):
        if name not in frame_state["active"]:
            continue
        override = overrides.get(name)
        ends = frame_state["mode"][name]
        span = _frame_span(
            axis, ends, interval=override() if override is not None else None
        )
        if span is not None and "loose" in ends:
            span, grew = _fit_loose_view(ax, name, span, ends)
            changed = changed or grew
        if span is None:
            continue
        spine = ax.spines[spine_name]
        if spine.get_bounds() != span:
            spine.set_bounds(*span)
            changed = True
    return changed


def _fit_loose_view(
    ax: Axes, name: str, span: tuple[float, float], ends: tuple[str, str]
) -> tuple[tuple[float, float] | None, bool]:
    """Reconcile a spine with a loose end with the view along `name`.

    A loose end sits at a tick bracketing the data, which a user's
    fixed locator can put outside the autoscaled view; spines are not
    clipped, so the spine would be drawn outside the axes. While the
    axis autoscales, the view grows to cover the spine, as the default
    locator's own view limits already do. A view the user pinned is a
    crop, so a loose end keeps only the ticks the view shows; an end
    that is not loose reads the visible data and is inside the view
    already.

    Returns the span to draw and whether the view was changed.
    """
    axis = ax.xaxis if name == "x" else ax.yaxis
    view = axis.get_view_interval()
    vmin, vmax = sorted(float(v) for v in view)
    autoscaled = ax.get_autoscalex_on() if name == "x" else ax.get_autoscaley_on()
    if autoscaled:
        lo, hi = min(span[0], vmin), max(span[1], vmax)
        if (lo, hi) == (vmin, vmax):
            return span, False
        limits = (hi, lo) if view[0] > view[1] else (lo, hi)
        (ax.set_xlim if name == "x" else ax.set_ylim)(*limits, auto=None)
        return span, True
    ticks = [t for t in axis.get_majorticklocs() if vmin <= t <= vmax]
    if not ticks:
        return None, False
    return (
        min(ticks) if ends[0] == "loose" else span[0],
        max(ticks) if ends[1] == "loose" else span[1],
    ), False


def _frame_span(
    axis: Axis, ends: tuple[str, str], interval: tuple[float, float] | None = None
) -> tuple[float, float] | None:
    """Where the spine ends, each end by its own mode, or `None` to leave it."""
    dmin, dmax = interval if interval is not None else visible_interval(axis)
    if not np.isfinite([dmin, dmax]).all() or dmin == dmax:
        return None
    ticks = list(axis.get_majorticklocs())
    if not ticks and ends != ("data", "data"):
        return None
    inside = [t for t in ticks if dmin <= t <= dmax]
    tol = 1e-9 * (dmax - dmin)

    def end(
        mode: str,
        datum: float,
        outer: Callable[[list[float]], float],
        nearest: Callable[[list[float]], float],
        beyond: list[float],
    ) -> float | None:
        if mode == "data":
            return datum
        if mode == "nice":
            return outer(inside) if inside else None
        if interval is None:
            return outer(ticks)
        # Loose over an injected interval: end at the drawn tick
        # bounding it, since ticks inside the interval cannot bracket
        # the data. Tolerance absorbs mizani's float dust.
        return nearest(beyond) if beyond else outer(ticks)

    lo = end(ends[0], dmin, min, max, [t for t in ticks if t <= dmin + tol])
    hi = end(ends[1], dmax, max, min, [t for t in ticks if t >= dmax - tol])
    if lo is None or hi is None:
        return None
    return (lo, hi)
