"""The range frame: trimmed spines and data-range ticks."""

import warnings
from collections.abc import Callable, Sequence
from typing import NamedTuple, TypeVar

import matplotlib.dates as mdates
import numpy as np
from matplotlib.axes import Axes
from matplotlib.axis import Axis
from matplotlib.ticker import Locator, NullLocator

from vanzelfsprekend.hook import add_applier, ensure_state, get_state
from vanzelfsprekend.locator import (
    DateBreaksLocator,
    LogBreaksLocator,
    TalbotLocator,
    visible_interval,
)

FrameMode = str | tuple[str, str]
"""One axis's frame mode: a mode for both ends, or a `(low, high)` pair."""

MODES = ("nice", "data", "loose")


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
    `group.frame_unit` orders the calls that way.
    """
    state = ensure_state(ax)
    if "frame" in state:
        return
    state["frame"] = {
        "active": set(),
        "formatted": set(),
        "installed": {},
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
            "is_default": {
                "majloc": {
                    "x": ax.xaxis.isDefault_majloc,
                    "y": ax.yaxis.isDefault_majloc,
                },
                "minloc": {
                    "x": ax.xaxis.isDefault_minloc,
                    "y": ax.yaxis.isDefault_minloc,
                },
                "majfmt": {
                    "x": ax.xaxis.isDefault_majfmt,
                    "y": ax.yaxis.isDefault_majfmt,
                },
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


def skip_if_not_rectilinear(ax: Axes, stacklevel: int) -> bool:
    """Warn and return True if `ax` is a projection the frame cannot fit.

    The range frame assumes the four cartesian spines and an x-y data
    plane; only matplotlib's `'rectilinear'` projection has them. Polar,
    3D and the rest are declined here and left untouched, the same
    contract as an unsupported scale. `stacklevel` points the warning at
    the public caller.
    """
    if ax.name == "rectilinear":
        return False
    warnings.warn(
        f"vanzelfsprekend: axes uses the {ax.name!r} projection; only "
        "rectilinear (x-y) axes are supported, leaving it untouched",
        stacklevel=stacklevel,
    )
    return True


def build_major_locator(
    kind: AxisKind,
    loose: tuple[bool, bool],
    n: int | None,
    spacing: float,
    nice_numbers: Sequence[float] | None,
    weights: dict[str, float] | None,
    base: float | None,
) -> Locator:
    """Return the range-frame major locator for `kind`.

    A `DateBreaksLocator` for a date axis, a `LogBreaksLocator` (using
    `base`) for a log axis, a `TalbotLocator` otherwise. Does not touch
    the axis; the caller installs it.
    """
    if kind.is_date:
        return DateBreaksLocator(n=n, spacing=spacing, loose=loose)
    if kind.scale == "log":
        return LogBreaksLocator(n=n, spacing=spacing, loose=loose, base=base)  # ty: ignore[invalid-argument-type]
    return TalbotLocator(
        n=n, spacing=spacing, loose=loose, nice_numbers=nice_numbers, weights=weights
    )


_Slotted = TypeVar("_Slotted")


def _write_slot(
    installed: dict[str, object],
    key: str,
    is_default: bool,
    current: _Slotted,
    build: Callable[[], _Slotted],
    set_fn: Callable[[_Slotted], None],
) -> _Slotted | None:
    """Install `build()` into a tick slot iff we may; return it, else None.

    We may when the slot is matplotlib's untouched default (`is_default`)
    or still holds the object we installed before (`current is
    installed[key]`, a refresh). A slot the user set deliberately is
    preserved untouched.
    """
    if is_default or current is installed.get(key):
        obj = build()
        set_fn(obj)
        installed[key] = obj
        return obj
    return None


def install_frame(
    ax: Axes,
    mode: dict[str, tuple[str, str]],
    offsets: dict[str, float],
    n: int | None,
    spacing: dict[str, float],
    nice_numbers: Sequence[float] | None,
    weights: dict[str, float] | None,
    kinds: dict[str, AxisKind | None],
    grouped: set[str],
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
    grouped : set of str
        Axis names (`'x'`, `'y'`) that will be wrapped in a
        `GroupLocator` by the caller. A grouped axis is always
        (re)installed — the shared scale is computed there — so the
        no-clobber guard does not apply to it. Empty for a lone axes.
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
        base = axis.get_transform().base if kind.scale == "log" else None  # ty: ignore[unresolved-attribute]
        installed = frame_state["installed"]
        may_clobber = name in grouped
        loc = _write_slot(
            installed,
            f"majloc:{name}",
            axis.isDefault_majloc or may_clobber,
            axis.get_major_locator(),
            lambda kind=kind, loose=loose, name=name, base=base: build_major_locator(
                kind, loose, n, spacing[name], nice_numbers, weights, base
            ),
            axis.set_major_locator,
        )
        wrote_major = loc is not None
        if wrote_major and kind.is_date:
            fmt = _write_slot(
                installed,
                f"majfmt:{name}",
                axis.isDefault_majfmt or may_clobber,
                axis.get_major_formatter(),
                lambda loc=loc: mdates.ConciseDateFormatter(loc),
                axis.set_major_formatter,
            )
            if fmt is not None:
                frame_state["formatted"].add(name)
        if kind.scale == "log":
            _write_slot(
                installed,
                f"minloc:{name}",
                axis.isDefault_minloc or may_clobber,
                axis.get_minor_locator(),
                NullLocator,
                axis.set_minor_locator,
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
