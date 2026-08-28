"""Tick-label separation: crowded labels drift apart, marks stay put.

Targets are recomputed each draw from the tick locations, so the
placement never feeds on its own displacement; the shift is an additive
`ScaledTranslation` on the label's transform, which matplotlib's tick
layout does not reset, so a converged axes reports no change.
"""

from typing import cast

import numpy as np
from matplotlib.axes import Axes
from matplotlib.axis import Axis
from matplotlib.text import Text
from matplotlib.transforms import ScaledTranslation, Transform

from vanzelfsprekend import placement
from vanzelfsprekend.hook import get_state

_BASE_ATTR = "_vanzelfsprekend_base"


def _base_transform(text: Text) -> Transform:
    """Return the transform `text` had before this applier ever touched it.

    Tick-label `Text` objects are pooled and cloned by matplotlib:
    `Axis.majorTicks` only ever grows, so a label that drops out when the
    tick count shrinks comes back carrying whatever transform it had
    last; and `Axis._copy_tick_props` clones an existing tick's label
    transform onto newly grown ones via `Artist.update_from`, so a label
    never seen before can still inherit a sibling's shifted transform.
    Either way `text.get_transform()` is not trustworthy as "original".
    Every shifted transform this applier installs is tagged with the
    base it was built from, so following that tag -- when present --
    recovers the true, unshifted original instead of compounding on it.
    """
    current = text.get_transform()
    return cast("Transform", getattr(current, _BASE_ATTR, current))


def _apply_tick_labels(ax: Axes) -> bool:
    """Displace colliding tick labels minimally along their axis."""
    state = get_state(ax)
    if state is None or "frame" not in state or "tick_labels" not in state:
        return False
    active = state["frame"]["active"]
    applied = state["tick_labels"]["applied"]
    changed = False
    for name, axis in (("x", ax.xaxis), ("y", ax.yaxis)):
        if name in active:
            changed = _separate(ax, axis, name, applied[name]) or changed
    return changed


def _separate(ax: Axes, axis: Axis, name: str, applied: dict) -> bool:
    locs = np.asarray(axis.get_majorticklocs(), dtype=float)
    if len(locs) < 2:
        return False
    # Each visible label set (left/bottom `label1`, right/top `label2`) is
    # its own row or column, so each is solved on its own against the same
    # tick positions.
    ticks = axis.get_major_ticks()
    sides = [
        [tick.label1 for tick in ticks if tick.label1.get_visible()],
        [tick.label2 for tick in ticks if tick.label2.get_visible()],
    ]
    for stale in set(applied) - {text for side in sides for text in side}:
        stale.set_transform(cast("Transform", applied[stale][0]))
        del applied[stale]
    changed = False
    for labels in sides:
        changed = _separate_side(ax, locs, labels, name, applied) or changed
    return changed


def _separate_side(
    ax: Axes, locs: np.ndarray, labels: list[Text], name: str, applied: dict
) -> bool:
    if len(labels) != len(locs):
        return False
    try:
        extents = [text.get_window_extent() for text in labels]
    except RuntimeError:
        return False
    dim = 0 if name == "x" else 1
    points = np.ones((len(locs), 2))
    points[:, dim] = locs
    desired = ax.transData.transform(points)[:, dim]
    sizes = np.array([e.width if name == "x" else e.height for e in extents])
    px_per_pt = ax.figure.dpi / 72.0
    offsets = placement.stack(desired, sizes, placement.GAP * px_per_pt) - desired
    changed = False
    for text, offset in zip(labels, offsets, strict=True):
        entry = applied.get(text)
        if entry is None:
            base = _base_transform(text)
            entry = applied[text] = [base, 0.0, base]
        # `entry[2]` is the transform this applier last installed (or the
        # base, if it never needed to shift the label). Anything else --
        # an inherited sibling shift at first sighting, or a transform
        # matplotlib rebuilt underneath us (e.g. `tick_params(pad=...)`
        # via `Tick._apply_params`) -- is an untracked shift that must be
        # reconciled regardless of whether the offset itself changed.
        wears_untracked_shift = text.get_transform() is not entry[2]
        if wears_untracked_shift:
            # Re-derive the base rather than trusting the one captured at
            # first sighting: `_base_transform` still follows the
            # `_BASE_ATTR` tag when the untracked transform is an
            # inherited sibling shift (pooled/cloned-tick protection),
            # but otherwise it *is* the untracked transform -- e.g. one
            # matplotlib legitimately rebuilt via `tick_params(pad=...)`
            # -- which must be adopted as the new base so a user's
            # explicit styling isn't silently discarded.
            entry[0] = _base_transform(text)
        if not wears_untracked_shift and abs(offset - entry[1]) < 0.05:
            continue
        inches = float(offset) / ax.figure.dpi
        shift = (inches, 0.0) if name == "x" else (0.0, inches)
        base = cast("Transform", entry[0])
        shifted = base + ScaledTranslation(*shift, ax.figure.dpi_scale_trans)
        setattr(shifted, _BASE_ATTR, base)
        text.set_transform(shifted)
        entry[1] = float(offset)
        entry[2] = shifted
        changed = True
    return changed
