"""End-of-spine axis labels for a range frame."""

from typing import cast

import numpy as np
from matplotlib.axes import Axes
from matplotlib.axis import Axis
from matplotlib.text import Text
from matplotlib.transforms import ScaledTranslation, Transform

from vanzelfsprekend.frame import _frame_span, _is_date_converter
from vanzelfsprekend.hook import add_applier, ensure_state, get_state, run_appliers


def xlabel(
    ax: Axes, text: str, flush: bool = False, labelpad: float | None = None
) -> Text:
    """Set an x-label that sits below the right end of the bottom spine.

    Call after `range_frame`.

    Parameters
    ----------
    ax : matplotlib.axes.Axes
        A range-framed axes.
    text : str
        The label text.
    flush : bool
        Where the label's right edge sits. `False` (the default) anchors
        it at the spine end (the last tick in `'nice'` mode, the data max
        in `'data'`), lining up with the *centre* of the rightmost tick
        label. `True` pushes it out to that tick label's right edge, so
        the label and the tick-label row share a flush right margin. The
        nudge is strictly outward (clamped never to move left of the
        spine end), so it only takes effect where the last tick sits at
        the spine end (`'nice'`/`'loose'` mode); in `'data'` mode, where
        the spine already reaches past the last tick label, it is a no-op.
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
    _labels_state(ax)["xlabel_flush"] = flush
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
        (`va='center_baseline'`), to its left, on matplotlib's own y-axis
        label. `'above'` stacks it above the top tick label, its left edge
        aligned with the top tick label's left edge, as a separate
        clip-free text artist (see Notes).
    labelpad : float, optional
        Gap in points between the label and the tick-label column, whose
        edge is set by the *widest* tick label. `None` keeps matplotlib's
        default (rcParam `axes.labelpad`, 4.0). Ignored when
        `place='above'`, which anchors on the top tick label directly.

    Returns
    -------
    matplotlib.text.Text
        The label artist: matplotlib's own `ax.yaxis.label` for
        `'beside'`, or the managed above-label text for `'above'`.

    Raises
    ------
    ValueError
        If `place` is not `'beside'` or `'above'`.

    Notes
    -----
    `'above'` draws the label as a standalone text child rather than
    relocating `ax.yaxis.label`, because `Axes.get_tightbbox` collapses an
    axis label's cross-height (it assumes the label sits centred on the
    axis) and would clip a label stacked above it. A plain child text is
    enclosed at full extent, so `savefig(bbox_inches="tight")` keeps the
    above-label whole with no `bbox_extra_artists`. The real axis label is
    emptied while `'above'` is active.
    """
    if place not in ("beside", "above"):
        raise ValueError(f"place must be 'beside' or 'above', got {place!r}")
    ls = _labels_state(ax)
    ls["ylabel_place"] = place
    if place == "above":
        result = _set_ylabel_above(ax, text, ls)
    else:
        above_text = ls.get("ylabel_above_text")
        if above_text is not None:
            above_text.remove()
            ls["ylabel_above_text"] = None
        ax.yaxis.set_label_position("left")
        ax.yaxis._autolabelpos = True  # ty: ignore[unresolved-attribute]
        ax.set_ylabel(text, rotation=0, labelpad=labelpad)
        ax.yaxis.label.set_verticalalignment("center_baseline")
        ax.yaxis.label.set_horizontalalignment("right")
        result = ax.yaxis.label
    add_applier(ax, "labels", _apply_labels)
    run_appliers(ax)
    return result


def _set_ylabel_above(ax: Axes, text: str, ls: dict) -> Text:
    """Create or update the managed above-label and empty the axis label.

    The above-label is a clip-free text child styled to match the axis
    label; the draw hook positions it over the top tick label.
    """
    above_text = ls.get("ylabel_above_text")
    if above_text is None:
        above_text = ax.text(
            0.0,
            0.0,
            "",
            transform=ax.transAxes,
            horizontalalignment="left",
            verticalalignment="bottom",
            clip_on=False,
        )
        above_text.set_fontproperties(ax.yaxis.label.get_fontproperties())
        above_text.set_color(ax.yaxis.label.get_color())
        ls["ylabel_above_text"] = above_text
    above_text.set_text(text)
    ax.set_ylabel("")  # only the managed text renders while 'above' is active
    return above_text


def _labels_state(ax: Axes) -> dict:
    state = ensure_state(ax)
    ls = state.get("labels")
    if ls is None:
        ls = {
            "ylabel_place": "beside",
            "xlabel_flush": False,
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
        "text": label.get_text(),
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
            if ls.get("xlabel_flush", False):
                flush_frac = _xlabel_flush_frac(ax)
                if flush_frac is not None:
                    frac = max(frac, flush_frac)
            pos = ax.xaxis.label.get_position()
            if pos[0] != frac:
                ax.xaxis.label.set_position((frac, pos[1]))
                changed = True
    if "y" in active and ls.get("ylabel_place", "beside") == "above":
        above_text = ls.get("ylabel_above_text")
        if above_text is not None:
            changed = _place_ylabel_above(ax, above_text) or changed
    elif "y" in active and ax.get_ylabel():
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


def _apply_date_offset(ax: Axes) -> bool:
    """Anchor a date axis's offset text ("2016") to the spine end.

    `ConciseDateFormatter` parks the shared-year offset in the axes'
    bottom-right corner; move it to the right end of the bottom spine,
    the anchor `xlabel` uses, and lift it clear of an `xlabel` when both
    are present. matplotlib re-pins the offset's y every draw, so the
    lift rides on a transform translation it leaves alone. Snapshots the
    offset's original transform and x once so `restore` can undo it.
    """
    state = get_state(ax)
    if state is None or "frame" not in state:
        return False
    frame_state = state["frame"]
    if "x" not in frame_state["active"] or not _is_date_converter(
        ax.xaxis.get_converter()
    ):
        return False
    off = ax.xaxis.get_offset_text()
    snap = state.setdefault(
        "date_offset",
        {
            "transform": off.get_transform(),
            "x": off.get_position()[0],
            "stacked": False,
        },
    )
    changed = False
    span = _frame_span(ax.xaxis, frame_state["mode"]["x"])
    if span is not None:
        vmin, vmax = ax.get_xlim()
        frac = _axes_fraction(ax.xaxis, span[1], vmin, vmax)
        if off.get_position()[0] != frac:
            off.set_x(frac)
            changed = True
    if off.get_horizontalalignment() != "right":
        off.set_horizontalalignment("right")
        changed = True
    base = cast(Transform, snap["transform"])
    stacked = bool(ax.get_xlabel())
    if stacked != snap["stacked"]:
        if stacked:
            rise = float(off.get_fontsize()) + 2.0
            shift = ScaledTranslation(0.0, rise / 72.0, ax.figure.dpi_scale_trans)
            off.set_transform(base + shift)
        else:
            off.set_transform(base)
        snap["stacked"] = stacked
        changed = True
    return changed


def _place_ylabel_above(ax: Axes, above_text: Text) -> bool:
    """Stack the managed above-label over the top tick label, left aligned.

    Anchored on the topmost tick label's measured left/top edge, so it
    tracks the tick label's rendered width. The above-label is a plain
    `transAxes` text child, so a `set_position` sticks; nothing else
    moves it each draw.
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
    pos = above_text.get_position()
    if abs(pos[0] - target[0]) > 1e-4 or abs(pos[1] - target[1]) > 1e-4:
        above_text.set_position(target)
        return True
    return False


def _xlabel_flush_frac(ax: Axes) -> float | None:
    """Axes-fraction x of the rightmost tick label's right edge, or None.

    Returns None when there is no rightmost tick label to anchor to, so
    the caller falls back to the spine-end anchor.
    """
    locs = ax.xaxis.get_majorticklocs()
    labels = ax.xaxis.get_ticklabels()
    if not len(locs) or not labels:
        return None
    right = int(np.argmax(locs))
    if right >= len(labels):
        return None
    try:
        bbox = labels[right].get_window_extent()
    except RuntimeError:
        return None
    return float(ax.transAxes.inverted().transform((bbox.x1, 0))[0])


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
