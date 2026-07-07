"""Range frames for matplotlib axes."""

import warnings

import numpy as np

from tufty.locator import TalbotLocator

_STATE_ATTR = "_tufty_state"


def tuftify(ax, frame="nice", n=5):
    """Turn `ax` into a Tufte-style range frame.

    Installs `TalbotLocator` on both axes, hides the top and right
    spines, and keeps the left and bottom spine bounds glued to the
    data on every draw. Safe to call repeatedly; later calls update
    the settings instead of stacking hooks.

    Parameters
    ----------
    ax : matplotlib.axes.Axes
        The axes to modify, in place.
    frame : {'nice', 'data'}
        `'nice'` ends the spines at the outermost ticks, `'data'` at
        the exact data minimum and maximum.
    n : int
        Desired number of ticks per axis.

    Returns
    -------
    matplotlib.axes.Axes
        The same axes, for chaining.
    """
    if frame not in ("nice", "data"):
        raise ValueError(f"frame must be 'nice' or 'data', got {frame!r}")

    state = getattr(ax, _STATE_ATTR, None)
    if state is None:
        state = {"cid": ax.figure.canvas.mpl_connect("draw_event", _make_on_draw(ax))}
        setattr(ax, _STATE_ATTR, state)
    state["frame"] = frame

    active = set()
    for name, axis in (("x", ax.xaxis), ("y", ax.yaxis)):
        if axis.get_scale() != "linear":
            warnings.warn(
                f"tufty: {name}-axis has scale {axis.get_scale()!r}; "
                "only linear axes are supported, leaving it untouched",
                stacklevel=2,
            )
            continue
        axis.set_major_locator(TalbotLocator(n=n))
        active.add(name)
    state["active"] = active

    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    _apply(ax)
    return ax


def _make_on_draw(ax):
    def _on_draw(event):
        if _apply(ax):
            event.canvas.draw_idle()

    return _on_draw


def _apply(ax):
    state = getattr(ax, _STATE_ATTR, None)
    if state is None:
        return False
    changed = False
    for name, axis, spine_name in (
        ("x", ax.xaxis, "bottom"),
        ("y", ax.yaxis, "left"),
    ):
        if name not in state["active"]:
            continue
        span = _frame_span(axis, state["frame"])
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
    ticks = [t for t in axis.get_majorticklocs() if dmin <= t <= dmax]
    if not ticks:
        return None
    return (min(ticks), max(ticks))
