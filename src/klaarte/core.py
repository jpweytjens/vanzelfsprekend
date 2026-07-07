"""Range frames for matplotlib axes."""

import warnings

import numpy as np

from klaarte.hook import add_applier, ensure_state, get_state, run_appliers
from klaarte.locator import TalbotLocator


def tuftify(ax, frame="nice", n=5, offset=None, nice_numbers=None, weights=None):
    """Turn `ax` into a Tufte-style range frame.

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


def xlabel(ax, text, labelpad=None):
    """Set an x-label that sits below the right end of the bottom spine.

    Parameters
    ----------
    ax : matplotlib.axes.Axes
        A tuftified axes.
    text : str
        The label text.
    labelpad : float, optional
        Gap in points between the label and the tick-label column, whose
        edge is set by the *widest* tick label (matplotlib's own per-draw
        computation). `None` keeps matplotlib's default (rcParam
        `axes.labelpad`, 4.0).

    Returns
    -------
    matplotlib.text.Text
        The label artist.
    """
    ensure_state(ax)
    ax.set_xlabel(text, labelpad=labelpad)
    ax.xaxis.label.set_horizontalalignment("right")
    _labels_state(ax)
    add_applier(ax, "labels", _apply_labels)
    run_appliers(ax)
    return ax.xaxis.label


def ylabel(ax, text, flush=False, labelpad=None):
    """Set a horizontal y-label at the top of the left spine.

    Parameters
    ----------
    ax : matplotlib.axes.Axes
        A tuftified axes.
    text : str
        The label text.
    flush : bool
        If True, anchor the label at the topmost tick with
        `va='center_baseline'`, so it sits flush with the top tick label.
        If False, place it above the spine's top end.
    labelpad : float, optional
        Gap in points between the label and the tick-label column, whose
        edge is set by the *widest* tick label. `None` keeps matplotlib's
        default (rcParam `axes.labelpad`, 4.0).

    Returns
    -------
    matplotlib.text.Text
        The label artist.
    """
    ensure_state(ax)
    ax.set_ylabel(text, rotation=0, labelpad=labelpad)
    ax.yaxis.label.set_verticalalignment("center_baseline" if flush else "bottom")
    ax.yaxis.label.set_horizontalalignment("right")
    _labels_state(ax)["ylabel_flush"] = flush
    add_applier(ax, "labels", _apply_labels)
    run_appliers(ax)
    return ax.yaxis.label


def register():
    """Add a `tuftify` method to `matplotlib.axes.Axes`.

    Opt-in monkeypatching: after calling this once, `ax.tuftify(...)`
    delegates to `tuftify(ax, ...)`. Calling it again is a no-op.
    """
    from matplotlib.axes import Axes

    if getattr(Axes, "tuftify", None) is not None:
        return

    def _tuftify_method(self, frame="nice", n=5, offset=None, nice_numbers=None, weights=None):
        return tuftify(
            self, frame=frame, n=n, offset=offset, nice_numbers=nice_numbers, weights=weights
        )

    Axes.tuftify = _tuftify_method


def _labels_state(ax):
    state = ensure_state(ax)
    ls = state.get("labels")
    if ls is None:
        ls = {"ylabel_flush": False}
        state["labels"] = ls
    return ls


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


def _apply_labels(ax):
    state = get_state(ax)
    if state is None or "frame" not in state:
        return False
    frame_state = state["frame"]
    mode = frame_state["mode"]
    active = frame_state["active"]
    ls = state.get("labels", {})
    changed = False
    if "x" in active and ax.get_xlabel():
        span = _frame_span(ax.xaxis, mode)
        if span is not None:
            vmin, vmax = ax.get_xlim()
            frac = (span[1] - vmin) / (vmax - vmin)
            pos = ax.xaxis.label.get_position()
            if pos[0] != frac:
                ax.xaxis.label.set_position((frac, pos[1]))
                changed = True
    if "y" in active and ax.get_ylabel():
        span = _frame_span(ax.yaxis, mode)
        if span is not None:
            anchor = span[1]
            if ls.get("ylabel_flush"):
                locs = ax.yaxis.get_majorticklocs()
                if len(locs):
                    anchor = max(locs)
            vmin, vmax = ax.get_ylim()
            frac = (anchor - vmin) / (vmax - vmin)
            pos = ax.yaxis.label.get_position()
            if pos[1] != frac:
                ax.yaxis.label.set_position((pos[0], frac))
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
