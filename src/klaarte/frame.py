"""The range frame: trimmed spines and data-range ticks."""

import warnings

import numpy as np

from klaarte.hook import add_applier, ensure_state, get_state, run_appliers
from klaarte.locator import TalbotLocator


def range_frame(ax, frame="nice", n=5, offset=None, nice_numbers=None, weights=None):
    """Turn `ax` into a range frame.

    Installs `TalbotLocator` on both axes, hides the top and right
    spines, and keeps the left and bottom spine bounds glued to the
    data on every draw. Safe to call repeatedly; later calls update
    the settings instead of stacking hooks.

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
    weights : dict, optional
        Advanced pass-through to `TalbotLocator`; see there for details.

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
    frame_state = state.get("frame")
    if frame_state is None:
        frame_state = {"active": set()}
        state["frame"] = frame_state
    frame_state["mode"] = frame
    frame_state["offset"] = offset

    active = set()
    for name, axis in (("x", ax.xaxis), ("y", ax.yaxis)):
        if axis.get_scale() != "linear":
            warnings.warn(
                f"klaarte: {name}-axis has scale {axis.get_scale()!r}; "
                "only linear axes are supported, leaving it untouched",
                stacklevel=2,
            )
            continue
        if axis.get_converter() is not None:
            warnings.warn(
                f"klaarte: {name}-axis has a units converter; "
                "only plain linear axes are supported, leaving it untouched",
                stacklevel=2,
            )
            continue
        axis.set_major_locator(
            TalbotLocator(
                n=n, loose=frame == "loose", nice_numbers=nice_numbers, weights=weights
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


def _apply_frame(ax):
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


def _frame_span(axis, frame):
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
