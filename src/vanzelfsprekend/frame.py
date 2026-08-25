"""The range frame: trimmed spines and data-range ticks."""

import warnings
from collections.abc import Sequence
from typing import Any, cast

import matplotlib.dates as mdates
import numpy as np
from matplotlib.axes import Axes
from matplotlib.axis import Axis
from matplotlib.ticker import NullLocator

from vanzelfsprekend.hook import add_applier, ensure_state, get_state, run_appliers
from vanzelfsprekend.locator import DateBreaksLocator, LogBreaksLocator, TalbotLocator


def range_frame(
    ax: Axes,
    frame: str = "nice",
    n: int = 5,
    offset: float | None = None,
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
    frame : {'nice', 'data', 'loose'}
        `'nice'` ends the spines at the outermost ticks, `'data'` at
        the exact data minimum and maximum. `'loose'` ends the spines
        at nice numbers bounding the data (frame may extend up to one
        tick step beyond the data).
    n : int
        Desired number of ticks per axis.
    offset : float, optional
        Outward displacement of the left and bottom spines, in points.
        `None` resolves to 8 for `frame='loose'` and 0 otherwise.
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
    if frame not in ("nice", "data", "loose"):
        raise ValueError(f"frame must be 'nice', 'data' or 'loose', got {frame!r}")
    if offset is None:
        offset = 8 if frame == "loose" else 0

    state = ensure_state(ax)
    frame_state: dict[str, Any] | None = state.get("frame")
    if frame_state is None:
        frame_state = {
            "active": set(),
            "snapshot": {
                "locators": {
                    "x": ax.xaxis.get_major_locator(),
                    "y": ax.yaxis.get_major_locator(),
                },
                "minor_locators": {
                    "x": ax.xaxis.get_minor_locator(),
                    "y": ax.yaxis.get_minor_locator(),
                },
                "formatters": {},
                "top_visible": ax.spines["top"].get_visible(),
                "right_visible": ax.spines["right"].get_visible(),
                "left_position": ax.spines["left"].get_position(),
                "bottom_position": ax.spines["bottom"].get_position(),
            },
        }
        state["frame"] = frame_state
    frame_state["mode"] = frame

    active = set()
    for name, axis in (("x", ax.xaxis), ("y", ax.yaxis)):
        scale = axis.get_scale()
        if scale not in ("linear", "log"):
            warnings.warn(
                f"vanzelfsprekend: {name}-axis has scale {scale!r}; "
                "only linear and log axes are supported, leaving it untouched",
                stacklevel=2,
            )
            continue
        converter = axis.get_converter()
        if converter is not None and not _is_date_converter(converter):
            warnings.warn(
                f"vanzelfsprekend: {name}-axis has a units converter; "
                "only plain and date axes are supported, leaving it untouched",
                stacklevel=2,
            )
            continue
        if converter is not None:
            locator = DateBreaksLocator(n=n, loose=frame == "loose")
            axis.set_major_locator(locator)
            formatters = cast(dict[str, Any], frame_state["snapshot"]["formatters"])
            if name not in formatters:
                formatters[name] = axis.get_major_formatter()
            axis.set_major_formatter(mdates.ConciseDateFormatter(locator))
        elif scale == "log":
            axis.set_major_locator(
                LogBreaksLocator(
                    n=n,
                    loose=frame == "loose",
                    base=axis.get_transform().base,  # ty: ignore[unresolved-attribute]
                )
            )
            axis.set_minor_locator(NullLocator())
        else:
            axis.set_major_locator(
                TalbotLocator(
                    n=n,
                    loose=frame == "loose",
                    nice_numbers=nice_numbers,
                    weights=weights,
                )
            )
        active.add(name)
    frame_state["active"] = active

    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    ax.spines["left"].set_position(("outward", offset))
    ax.spines["bottom"].set_position(("outward", offset))

    add_applier(ax, "frame", _apply_frame)
    run_appliers(ax)
    return ax


def _is_date_converter(converter: object) -> bool:
    date_converters: tuple[type, ...] = (
        mdates.DateConverter,
        mdates.ConciseDateConverter,
    )
    switchable = getattr(mdates, "_SwitchableDateConverter", None)
    if switchable is not None:
        date_converters += (switchable,)
    return isinstance(converter, date_converters)


def _apply_frame(ax: Axes) -> bool:
    state = get_state(ax)
    if state is None or "frame" not in state:
        return False
    frame_state = state["frame"]
    changed = False
    for name, axis, spine_name in (
        ("x", ax.xaxis, "bottom"),
        ("y", ax.yaxis, "left"),
    ):
        if name not in frame_state["active"]:
            continue
        span = _frame_span(axis, frame_state["mode"])
        if span is None:
            continue
        spine = ax.spines[spine_name]
        if spine.get_bounds() != span:
            spine.set_bounds(*span)
            changed = True
    return changed


def _frame_span(axis: Axis, frame: str) -> tuple[float, float] | None:
    dmin, dmax = axis.get_data_interval()
    if not np.isfinite([dmin, dmax]).all() or dmin == dmax:
        return None
    if frame == "data":
        return (dmin, dmax)
    ticks = axis.get_majorticklocs()
    if frame == "nice":
        ticks = [t for t in ticks if dmin <= t <= dmax]
    if len(ticks) == 0:
        return None
    return (min(ticks), max(ticks))
