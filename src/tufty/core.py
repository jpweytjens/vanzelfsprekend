"""Range frames for matplotlib axes."""

import warnings

import numpy as np

from tufty.locator import TalbotLocator

_STATE_ATTR = "_tufty_state"


def tuftify(ax, frame="nice", n=5, offset=None):
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
        `None` resolves to 8 for `frame='loose'` (prevents the spines
        meeting at the corner, since the loose view equals the tick
        span) and 0 otherwise.

    Returns
    -------
    matplotlib.axes.Axes
        The same axes, for chaining.
    """
    if frame not in ("nice", "data", "loose"):
        raise ValueError(f"frame must be 'nice', 'data' or 'loose', got {frame!r}")
    if offset is None:
        offset = 8 if frame == "loose" else 0

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
        if axis.get_converter() is not None:
            warnings.warn(
                f"tufty: {name}-axis has a units converter; "
                "only plain linear axes are supported, leaving it untouched",
                stacklevel=2,
            )
            continue
        axis.set_major_locator(TalbotLocator(n=n, loose=frame == "loose"))
        active.add(name)
    state["active"] = active

    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    ax.spines["left"].set_position(("outward", offset))
    ax.spines["bottom"].set_position(("outward", offset))
    _apply(ax)
    return ax


def xlabel(ax, text, labelpad=None):
    """Set an x-label that sits below the right end of the bottom spine.

    Call after `tuftify`. Vertical clearance from the tick labels is
    matplotlib's own per-draw computation; tufty only aligns the label's
    right edge with the spine end.

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
    ax.set_xlabel(text, labelpad=labelpad)
    ax.xaxis.label.set_horizontalalignment("right")
    _apply(ax)
    return ax.xaxis.label


def ylabel(ax, text, flush=False, labelpad=None):
    """Set a horizontal y-label at the top of the left spine.

    Call after `tuftify`. Horizontal clearance from the tick labels is
    matplotlib's own per-draw computation; tufty only aligns the label
    vertically.

    Parameters
    ----------
    ax : matplotlib.axes.Axes
        A tuftified axes.
    text : str
        The label text.
    flush : bool
        If True, anchor the label at the topmost tick with
        `va='center_baseline'`, the alignment y tick labels use, so the
        label sits flush with the top tick label. If False, place it
        above the spine's top end.
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
    ax.set_ylabel(text, rotation=0, labelpad=labelpad)
    ax.yaxis.label.set_verticalalignment("center_baseline" if flush else "bottom")
    ax.yaxis.label.set_horizontalalignment("right")
    state = getattr(ax, _STATE_ATTR, None)
    if state is not None:
        state["ylabel_flush"] = flush
    _apply(ax)
    return ax.yaxis.label


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
    bounds: dict[str, tuple[float, float] | None] = {"bottom": None, "left": None}
    for name, axis, spine_name in (
        ("x", ax.xaxis, "bottom"),
        ("y", ax.yaxis, "left"),
    ):
        if name not in state["active"]:
            continue
        span = _frame_span(axis, state["frame"])
        bounds[spine_name] = span
        if span is None:
            continue
        spine = ax.spines[spine_name]
        if spine.get_bounds() != span:
            spine.set_bounds(*span)
            changed = True
    return _place_labels(ax, bounds) or changed


def _place_labels(ax, bounds):
    changed = False
    span = bounds["bottom"]
    if span is not None and ax.get_xlabel():
        vmin, vmax = ax.get_xlim()
        frac = (span[1] - vmin) / (vmax - vmin)
        pos = ax.xaxis.label.get_position()
        if pos[0] != frac:
            ax.xaxis.label.set_position((frac, pos[1]))
            changed = True
    span = bounds["left"]
    if span is not None and ax.get_ylabel():
        anchor = span[1]
        if getattr(ax, _STATE_ATTR).get("ylabel_flush"):
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


def register():
    """Add a `tuftify` method to `matplotlib.axes.Axes`.

    Opt-in monkeypatching: after calling this once, `ax.tuftify(...)`
    delegates to `tuftify(ax, ...)`. Calling it again is a no-op.
    """
    from matplotlib.axes import Axes

    if getattr(Axes, "tuftify", None) is not None:
        return

    def _tuftify_method(self, frame="nice", n=5, offset=None):
        return tuftify(self, frame=frame, n=n, offset=offset)

    Axes.tuftify = _tuftify_method
