"""End-of-spine axis labels for a range frame."""

import numpy as np
from matplotlib.axes import Axes
from matplotlib.axis import Axis
from matplotlib.text import Text

from vanzelfsprekend.frame import _frame_span
from vanzelfsprekend.hook import add_applier, ensure_state, get_state, run_appliers


def xlabel(ax: Axes, text: str, labelpad: float | None = None) -> Text:
    """Set an x-label that sits below the right end of the bottom spine.

    Call after `range_frame`.

    Parameters
    ----------
    ax : matplotlib.axes.Axes
        A range-framed axes.
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
    _labels_state(ax)
    ax.set_xlabel(text, labelpad=labelpad)
    ax.xaxis.label.set_horizontalalignment("right")
    add_applier(ax, "labels", _apply_labels)
    run_appliers(ax)
    return ax.xaxis.label


def ylabel(
    ax: Axes, text: str, place: str = "beside", labelpad: float | None = None
) -> Text:
    """Set a horizontal y-label at the top of the left spine.

    Call after `range_frame`. The two placements are Doumont's two
    recommended y-labels (*Trees, maps and theorems*): `'beside'` is his
    "good graph", `'above'` his "better graph".

    Parameters
    ----------
    ax : matplotlib.axes.Axes
        A range-framed axes.
    text : str
        The label text.
    place : {'beside', 'above'}
        Where the horizontal label sits relative to the top tick.
        `'beside'` (the default) anchors it level with the top tick label
        (`va='center_baseline'`), to its left. `'above'` stacks it above
        the top tick label, its left edge aligned with the top tick
        label's left edge.
    labelpad : float, optional
        Gap in points between the label and the tick-label column, whose
        edge is set by the *widest* tick label. `None` keeps matplotlib's
        default (rcParam `axes.labelpad`, 4.0). Ignored when
        `place='above'`, which anchors on the top tick label directly.

    Returns
    -------
    matplotlib.text.Text
        The label artist.

    Raises
    ------
    ValueError
        If `place` is not `'beside'` or `'above'`.
    """
    if place not in ("beside", "above"):
        raise ValueError(f"place must be 'beside' or 'above', got {place!r}")
    _labels_state(ax)["ylabel_place"] = place
    if place == "beside":
        # Undo a prior 'above', whose set_label_coords disabled matplotlib's
        # own perpendicular placement.
        ax.yaxis.set_label_position("left")
        ax.yaxis._autolabelpos = True  # ty: ignore[unresolved-attribute]
    ax.set_ylabel(text, rotation=0, labelpad=labelpad)
    beside = place == "beside"
    ax.yaxis.label.set_verticalalignment("center_baseline" if beside else "bottom")
    ax.yaxis.label.set_horizontalalignment("right" if beside else "left")
    add_applier(ax, "labels", _apply_labels)
    run_appliers(ax)
    return ax.yaxis.label


def _labels_state(ax: Axes) -> dict:
    state = ensure_state(ax)
    ls = state.get("labels")
    if ls is None:
        ls = {
            "ylabel_place": "beside",
            "snapshot": {
                "x": _label_props(ax.xaxis.label),
                "y": _label_props(ax.yaxis.label),
                "y_autolabelpos": ax.yaxis._autolabelpos,  # ty: ignore[unresolved-attribute]
                "y_label_transform": ax.yaxis.label.get_transform(),
                "y_label_position_side": ax.yaxis.get_label_position(),
            },
        }
        state["labels"] = ls
    return ls


def _label_props(label: Text) -> dict:
    return {
        "ha": label.get_horizontalalignment(),
        "va": label.get_verticalalignment(),
        "rotation": label.get_rotation(),
        "position": label.get_position(),
    }


def _apply_labels(ax: Axes) -> bool:
    state = get_state(ax)
    if state is None or "frame" not in state:
        return False
    frame_state = state["frame"]
    mode = frame_state["mode"]
    active = frame_state["active"]
    ls = state.get("labels", {})
    changed = False
    if "x" in active and ax.get_xlabel():
        span = _frame_span(ax.xaxis, mode["x"])
        if span is not None:
            vmin, vmax = ax.get_xlim()
            frac = _axes_fraction(ax.xaxis, span[1], vmin, vmax)
            pos = ax.xaxis.label.get_position()
            if pos[0] != frac:
                ax.xaxis.label.set_position((frac, pos[1]))
                changed = True
    if "y" in active and ax.get_ylabel():
        if ls.get("ylabel_place", "beside") == "above":
            changed = _place_ylabel_above(ax) or changed
        else:
            span = _frame_span(ax.yaxis, mode["y"])
            if span is not None:
                locs = ax.yaxis.get_majorticklocs()
                if len(locs):
                    anchor = max(locs)
                    offset_px = _top_label_offset(ax, int(np.argmax(locs)))
                else:
                    anchor, offset_px = span[1], 0.0
                vmin, vmax = ax.get_ylim()
                frac = _axes_fraction(ax.yaxis, anchor, vmin, vmax)
                frac += offset_px / ax.bbox.height
                pos = ax.yaxis.label.get_position()
                if pos[1] != frac:
                    ax.yaxis.label.set_position((pos[0], frac))
                    changed = True
    return changed


def _place_ylabel_above(ax: Axes) -> bool:
    """Stack the y-label above the top tick label, left edges aligned.

    Anchored on the topmost tick label's measured left/top edge, so it
    tracks the tick label's rendered width. Uses `set_label_coords` (which
    disables matplotlib's own perpendicular placement), because the draw
    hook runs after that placement — a plain `set_position` on the label's
    x would be overwritten every draw and never converge.
    """
    locs = ax.yaxis.get_majorticklocs()
    labels = ax.yaxis.get_ticklabels()
    if not len(locs) or not labels:
        return False
    top = int(np.argmax(locs))
    if top >= len(labels):
        return False
    try:
        bbox = labels[top].get_window_extent()
    except RuntimeError:
        return False
    left, upper = ax.transAxes.inverted().transform((bbox.x0, bbox.y1))
    gap = 3.0 * ax.figure.dpi / 72.0 / ax.bbox.height
    target = (float(left), float(upper) + gap)
    pos = ax.yaxis.label.get_position()
    autolabelpos = ax.yaxis._autolabelpos  # ty: ignore[unresolved-attribute]
    moved = abs(pos[0] - target[0]) > 1e-4 or abs(pos[1] - target[1]) > 1e-4
    if autolabelpos or moved:
        ax.yaxis.set_label_coords(*target)
        return True
    return False


def _top_label_offset(ax: Axes, top_index: int) -> float:
    """Return the topmost y tick label's separation offset in pixels."""
    tick_state = (get_state(ax) or {}).get("tick_labels")
    if tick_state is None:
        return 0.0
    labels = ax.yaxis.get_ticklabels()
    if top_index >= len(labels):
        return 0.0
    entry = tick_state["applied"]["y"].get(labels[top_index])
    return float(entry[1]) if entry is not None else 0.0


def _axes_fraction(axis: Axis, value: float, vmin: float, vmax: float) -> float:
    transform = axis.get_transform()
    # A log-scale axis has a 1-D scale transform (e.g. `LogTransform`); a
    # linear axis's is the 2-D `IdentityTransform`, for which this reduces
    # to the previous plain arithmetic.
    if transform.input_dims == 1:
        value, vmin, vmax = np.ravel(
            transform.transform(np.array([[value], [vmin], [vmax]]))
        )
    return (value - vmin) / (vmax - vmin)
