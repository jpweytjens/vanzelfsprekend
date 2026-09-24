"""End-of-spine axis labels for a range frame."""

from typing import Any, cast

import numpy as np
from matplotlib.axes import Axes
from matplotlib.axis import Axis
from matplotlib.text import Text
from matplotlib.transforms import ScaledTranslation, Transform

from vanzelfsprekend.frame import _frame_span, _is_date_converter
from vanzelfsprekend.hook import add_applier, ensure_state, get_state, run_appliers


def xlabel(
    ax: Axes,
    text: str,
    flush: bool = True,
    labelpad: float | None = None,
    where: str = "bottom",
    **kwargs: Any,
) -> Text:
    """Set an x-label that sits below the right end of the bottom spine.

    Call after `range_frame`. With `where='top'` the label goes on a
    `secondary_frame` along the top instead, placed by the same rule
    against that axis's own tick labels.

    Parameters
    ----------
    ax : matplotlib.axes.Axes
        A range-framed axes.
    text : str
        The label text.
    flush : bool
        Where the label's right edge sits. `True` (the default) pushes it
        out to the rightmost tick label's right edge, so the label and the
        tick-label row share a flush right margin. `False` anchors it at
        the spine end (the last tick in `'inside'` mode, the data max in
        `'data'`), lining up with the *centre* of that tick label. The
        nudge is strictly outward (clamped never to move left of the
        spine end), so it only takes effect where the last tick sits at
        the spine end (`'inside'`/`'flexible'`/`'loose'`); in `'data'` mode, where
        the spine already reaches past the last tick label, it is a no-op.
    labelpad : float, optional
        Gap in points between the label and the tick-label column, whose
        edge is set by the *widest* tick label (matplotlib's own per-draw
        computation). `None` keeps matplotlib's default (rcParam
        `axes.labelpad`, 4.0).
    where : {'bottom', 'top'}
        The spine the label belongs to: the host's own bottom spine (the
        default), or a secondary frame added with
        `secondary_frame(where='top')`.
    **kwargs
        `matplotlib.text.Text` properties forwarded to `set_xlabel`, for
        styling: `color`, `fontsize`, `fontweight`, and the like.
        vanzelfsprekend owns the label's alignment and position, so a
        `horizontalalignment` here is overridden.

    Returns
    -------
    matplotlib.text.Text
        The label artist.

    Raises
    ------
    ValueError
        If `where` is not `'bottom'` or `'top'`, or names a side with no
        secondary frame on it.
    """
    if where == "bottom":
        target, store = ax, _labels_state(ax)
    elif where == "top":
        store = _secondary_entry(ax, where)
        target = store["secax"]
    else:
        raise ValueError(f"where must be 'bottom' or 'top', got {where!r}")
    store["xlabel_flush"] = flush
    target.set_xlabel(text, labelpad=labelpad, **kwargs)
    target.xaxis.label.set_horizontalalignment("right")
    add_applier(ax, "labels", _apply_labels)
    run_appliers(ax)
    return target.xaxis.label


def ylabel(
    ax: Axes,
    text: str,
    place: str = "above",
    labelpad: float | None = None,
    where: str = "left",
    **kwargs: Any,
) -> Text:
    """Set a horizontal y-label at the top of the left spine.

    Call after `range_frame`. The two placements are Doumont's two
    recommended y-labels (*Trees, maps and theorems*): `'above'` is his
    "better graph", `'beside'` his "good graph". With `where='right'`
    the label goes on a `secondary_frame` along the right instead,
    placed by the same rules against that axis's own tick labels, and
    `'beside'` then sits to the right of them.

    Parameters
    ----------
    ax : matplotlib.axes.Axes
        A range-framed axes.
    text : str
        The label text.
    place : {'above', 'beside'}
        Where the horizontal label sits relative to the top tick.
        `'above'` (the default) stacks it above the top tick label, its
        left edge aligned with the top tick label's left edge, as a
        separate clip-free text artist (see Notes). `'beside'` anchors it
        level with the top tick label (`va='center_baseline'`), to its
        left, on matplotlib's own y-axis label; it costs the label's own
        width, so reach for it where the space above the frame is already
        taken, by a title or by the panel above.
    labelpad : float, optional
        Gap in points between the label and the tick labels. `None` keeps
        matplotlib's default (rcParam `axes.labelpad`, 4.0). Which tick
        label sets the reference edge follows the placement: `'beside'`
        measures from the *widest* one (matplotlib's own per-draw
        computation), `'above'` from the top one.
    where : {'left', 'right'}
        The spine the label belongs to: the host's own left spine (the
        default), or a secondary frame added with
        `secondary_frame(where='right')`.
    **kwargs
        `matplotlib.text.Text` properties for styling the label, such as
        `color`, `fontsize`, `fontweight`. For `'beside'` they go to
        `set_ylabel`; for `'above'` they style the managed above-label
        text. vanzelfsprekend owns the label's rotation, alignment and
        position, so a `rotation` here is overridden.

    Returns
    -------
    matplotlib.text.Text
        The label artist: matplotlib's own `ax.yaxis.label` for
        `'beside'`, or the managed above-label text for `'above'`.

    Raises
    ------
    ValueError
        If `place` is not `'above'` or `'beside'`, if `where` is not
        `'left'` or `'right'`, or if `where` names a side with no
        secondary frame on it.

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
    if place not in ("above", "beside"):
        raise ValueError(f"place must be 'above' or 'beside', got {place!r}")
    if where == "left":
        target, store = ax, _labels_state(ax)
    elif where == "right":
        store = _secondary_entry(ax, where)
        target = store["secax"]
    else:
        raise ValueError(f"where must be 'left' or 'right', got {where!r}")
    store["ylabel_place"] = place
    if place == "above":
        result = _set_ylabel_above(ax, target, text, store, labelpad, kwargs)
    else:
        above_text = store.get("ylabel_above_text")
        if above_text is not None:
            above_text.remove()
            store["ylabel_above_text"] = None
        target.yaxis.set_label_position(where)
        target.yaxis._autolabelpos = True  # ty: ignore[invalid-assignment]
        target.set_ylabel(text, labelpad=labelpad, **kwargs)
        target.yaxis.label.set_rotation(0)
        target.yaxis.label.set_verticalalignment("center_baseline")
        # the label reads outward from the tick labels: to the left of a
        # left axis's, to the right of a right axis's
        target.yaxis.label.set_horizontalalignment(
            "right" if where == "left" else "left"
        )
        result = target.yaxis.label
    add_applier(ax, "labels", _apply_labels)
    run_appliers(ax)
    return result


def _secondary_entry(ax: Axes, where: str) -> dict:
    """Return the `secondary_frame` state on the `where` spine, or raise."""
    state = get_state(ax) or {}
    for entry in state.get("secondary", []):
        if entry["spine"] == where:
            return entry
    raise ValueError(
        f"no secondary frame on the {where}; call "
        f"secondary_frame(ax, functions, where={where!r}) first"
    )


def _set_ylabel_above(
    ax: Axes,
    target: Axes,
    text: str,
    store: dict,
    labelpad: float | None,
    kwargs: dict,
) -> Text:
    """Create or update the managed above-label and empty the axis label.

    The above-label is a clip-free text child of the host `ax`, styled to
    match `target`'s axis label (the host's own, or a secondary frame's);
    the draw hook positions it over `target`'s top tick label. It lives
    on the host because a secondary axes is a hairline strip whose axes
    fractions cannot place anything. `labelpad` rides on
    `target.yaxis.labelpad`, matplotlib's own store for the gap, so
    `None` means the same thing here as it does under `'beside'`. `kwargs`
    are `Text` style properties applied to the above-label, overriding the
    axis-label defaults copied in on first creation.
    """
    above_text = store.get("ylabel_above_text")
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
        above_text.set_fontproperties(target.yaxis.label.get_fontproperties())
        above_text.set_color(target.yaxis.label.get_color())
        store["ylabel_above_text"] = above_text
    above_text.set_text(text)
    if kwargs:
        above_text.update(kwargs)
    # only the managed text renders while 'above' is active; the pad still
    # lives on the axis, where `_place_ylabel_above` reads it each draw
    target.set_ylabel("", labelpad=labelpad)
    return above_text


def _labels_state(ax: Axes) -> dict:
    state = ensure_state(ax)
    ls = state.get("labels")
    if ls is None:
        ls = {
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


def _drawn_spine_span(ax: Axes, spine: str) -> tuple[float, float] | None:
    """Return the span the applier drew the named spine over, or `None`.

    `_frame_span` reports where a loose end wants to sit, which
    `_fit_view` then crops to a pinned view before setting the
    spine's bounds. A label belongs at the spine's drawn end, so it
    reads the bounds rather than re-deriving the crop. A secondary's
    spine is trimmed to the same span by `secondary_frame`'s applier.
    """
    bounds = ax.spines[spine].get_bounds()
    return None if bounds is None else (float(bounds[0]), float(bounds[1]))


def _visible_end_tick(axis: Axis) -> int | None:
    """Index of the major tick at the axis's drawn end, or `None`.

    The drawn end is where the axis label sits: the top of a y axis, the
    right of an x axis. That is the largest tick value, or the smallest
    on an inverted axis, whose view interval runs backwards.

    matplotlib lays out a `Text` for every tick the locator returns but
    draws only those inside the view interval (`Axis._update_ticks`), so
    a loose end reaching past a pinned limit leaves a positioned tick
    label that never renders. Anchoring on the end tick of all would
    follow one of those off the axes; reading the view here crops the
    same way `_fit_view` crops the spine to a pinned view.
    """
    locs = axis.get_majorticklocs()
    vmin, vmax = sorted(float(v) for v in axis.get_view_interval())
    visible = [i for i, loc in enumerate(locs) if vmin <= loc <= vmax]
    if not visible:
        return None
    reach = min if axis.get_inverted() else max
    return reach(visible, key=lambda i: locs[i])


def _span_end(axis: Axis, span: tuple[float, float]) -> float:
    """Return the end of a low-to-high `span` that the axis draws last.

    `_frame_span` and the spine's bounds both run low to high whichever
    way the axis points, so an inverted axis draws `span[0]` at the end
    the label sits at.
    """
    return span[0] if axis.get_inverted() else span[1]


def _apply_labels(ax: Axes) -> bool:
    state = get_state(ax)
    if state is None or "frame" not in state:
        return False
    active = state["frame"]["active"]
    changed = False
    # The host's own labels, then each secondary frame's: a secondary
    # mirrors one host axis, so its label follows that axis's frame.
    targets = [(ax, "bottom", "left", state.get("labels", {}))] + [
        (entry["secax"], entry["spine"], entry["spine"], entry)
        for entry in state.get("secondary", [])
    ]
    for target, x_spine, y_spine, store in targets:
        if "x" in active and target.get_xlabel() and x_spine in ("bottom", "top"):
            flush = store.get("xlabel_flush", True)
            changed = _place_xlabel(target, x_spine, flush) or changed
        if "y" not in active or y_spine not in ("left", "right"):
            continue
        above_text = store.get("ylabel_above_text")
        if above_text is not None:
            changed = _place_ylabel_above(target, y_spine, above_text) or changed
        elif target.get_ylabel():
            changed = _place_ylabel_beside(target, y_spine) or changed
    return changed


def _place_xlabel(ax: Axes, spine: str, flush: bool) -> bool:
    """Anchor `ax`'s x-label at the drawn end of `spine`, or flush past it."""
    span = _drawn_spine_span(ax, spine)
    if span is None:
        return False
    vmin, vmax = ax.get_xlim()
    frac = _axes_fraction(ax.xaxis, _span_end(ax.xaxis, span), vmin, vmax)
    if flush:
        flush_frac = _xlabel_flush_frac(ax)
        if flush_frac is not None:
            frac = max(frac, flush_frac)
    pos = ax.xaxis.label.get_position()
    if pos[0] == frac:
        return False
    ax.xaxis.label.set_position((frac, pos[1]))
    return True


def _place_ylabel_beside(ax: Axes, spine: str) -> bool:
    """Level `ax`'s y-label with the top tick, or the drawn end of `spine`."""
    span = _drawn_spine_span(ax, spine)
    if span is None:
        return False
    locs = ax.yaxis.get_majorticklocs()
    top = _visible_end_tick(ax.yaxis)
    vmin, vmax = ax.get_ylim()
    # A 'data' end runs the spine past the end tick, to the data.
    # The label belongs at whichever the frame ends on; comparing
    # in axes fractions reads the same either way the axis points,
    # and the tick label's own offset applies only when it wins.
    frac = _axes_fraction(ax.yaxis, _span_end(ax.yaxis, span), vmin, vmax)
    if top is not None:
        tick_frac = _axes_fraction(ax.yaxis, float(locs[top]), vmin, vmax)
        if tick_frac >= frac:
            frac = tick_frac + _top_label_offset(ax, top) / ax.bbox.height
    pos = ax.yaxis.label.get_position()
    if pos[1] == frac:
        return False
    ax.yaxis.label.set_position((pos[0], frac))
    return True


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


def _place_ylabel_above(ax: Axes, spine: str, above_text: Text) -> bool:
    """Stack the managed above-label over the top tick label, left aligned.

    Anchored on the topmost drawn tick label's measured left/top edge,
    so it tracks the tick label's rendered width, and lifted clear of it
    by `ax.yaxis.labelpad`. A `'data'` end runs the spine past that tick,
    so the lift clears whichever of the two reaches higher. The above-label
    is a plain text child in its own axes' `transAxes` (the host's, even
    for a secondary frame's label), so a `set_position` sticks; nothing
    else moves it each draw.
    """
    labels = ax.yaxis.get_ticklabels()
    top = _visible_end_tick(ax.yaxis)
    if top is None or top >= len(labels):
        return False
    try:
        bbox = labels[top].get_window_extent()
    except RuntimeError:
        return False
    left, upper = above_text.get_transform().inverted().transform((bbox.x0, bbox.y1))
    span = _drawn_spine_span(ax, spine)
    if span is not None:
        vmin, vmax = ax.get_ylim()
        end = _axes_fraction(ax.yaxis, _span_end(ax.yaxis, span), vmin, vmax)
        upper = max(upper, end)
    gap = ax.yaxis.labelpad * ax.figure.dpi / 72.0 / ax.bbox.height
    target = (float(left), float(upper) + gap)
    pos = above_text.get_position()
    if abs(pos[0] - target[0]) > 1e-4 or abs(pos[1] - target[1]) > 1e-4:
        above_text.set_position(target)
        return True
    return False


def _xlabel_flush_frac(ax: Axes) -> float | None:
    """Axes-fraction x of the rightmost drawn tick label's right edge, or None.

    Returns None when the view shows no tick label to anchor to, so the
    caller falls back to the spine-end anchor.
    """
    labels = ax.xaxis.get_ticklabels()
    right = _visible_end_tick(ax.xaxis)
    if right is None or right >= len(labels):
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
