"""End-of-line direct labels: label each line at one end instead of in a legend."""

from functools import partial
from itertools import cycle
from typing import Literal

import numpy as np
from matplotlib.axes import Axes
from matplotlib.colors import is_color_like
from matplotlib.lines import Line2D
from matplotlib.text import Annotation
from matplotlib.typing import ColorType

from vanzelfsprekend.hook import add_applier, ensure_state, get_state, run_appliers


def line_labels(
    ax: Axes,
    at: Literal["start", "end"] = "end",
    labelcolor: str | ColorType | list[ColorType] = "linecolor",
    pad: float = 4.0,
    gap: float = 2.0,
) -> list[Annotation]:
    """Label each line at one end, in place of a legend.

    Text comes from each line's `label=`; lines with matplotlib's
    auto-generated `_`-prefixed labels or without a finite point are
    skipped. Labels sit just outside their line's end and are pushed
    apart vertically only as far as needed to clear each other, keeping
    the end-value order (an exact least-squares stack, re-solved on
    every draw). Calling again with the same `at` rebuilds that side
    from the current lines; the sides compose, so one call per side
    labels both ends.

    Parameters
    ----------
    ax : matplotlib.axes.Axes
        The axes whose lines to label.
    at : {'end', 'start'}
        Which end of each line to label. `'end'` anchors at the last
        finite point, text to its right; `'start'` at the first finite
        point, text to its left (slopegraph-style). On a `'nice'` or
        `'data'` frame, start labels can collide with the y tick
        labels; `frame='loose'` leaves a gutter for them.
    labelcolor : color, list of color, or 'linecolor'
        `'linecolor'` colours each label like its line, as in
        `legend(labelcolor=...)`. A single colour applies to every
        label; a list is cycled over the lines.
    pad : float
        Horizontal gap in points between a line's end and its label.
    gap : float
        Minimum vertical clearance in points between label boxes.

    Returns
    -------
    list of matplotlib.text.Annotation
        The label artists, in line order.
    """
    if at not in ("start", "end"):
        raise ValueError(f"at must be 'start' or 'end', got {at!r}")
    state = ensure_state(ax)
    sides = state.setdefault("line_labels", {})
    prior = sides.pop(at, None)
    if prior is not None:
        for text in prior["texts"]:
            text.remove()
    anchored = [
        (line, anchor)
        for line in ax.get_lines()
        if not line.get_label().startswith("_")
        and (anchor := _anchor(line, at)) is not None
    ]
    lines = [line for line, _ in anchored]
    sign = 1.0 if at == "end" else -1.0
    texts = [
        ax.annotate(
            line.get_label(),
            xy=anchor,
            xytext=(sign * pad, 0.0),
            textcoords="offset points",
            ha="left" if at == "end" else "right",
            va="center",
            color=color,
            annotation_clip=False,
        )
        for (line, anchor), color in zip(
            anchored, _resolve_colors(labelcolor, lines), strict=True
        )
    ]
    sides[at] = {"lines": lines, "texts": texts, "pad": pad, "gap": gap}
    add_applier(ax, f"line_labels.{at}", partial(_apply_line_labels, at=at))
    run_appliers(ax)
    return texts


def _anchor(line: Line2D, at: str) -> tuple[float, float] | None:
    x = np.asarray(line.get_xdata(), dtype=float)
    y = np.asarray(line.get_ydata(), dtype=float)
    finite = np.flatnonzero(np.isfinite(x) & np.isfinite(y))
    if not len(finite):
        return None
    i = finite[0] if at == "start" else finite[-1]
    return (float(x[i]), float(y[i]))


def _resolve_colors(
    labelcolor: str | ColorType | list[ColorType], lines: list[Line2D]
) -> list[ColorType]:
    if isinstance(labelcolor, str) and labelcolor == "linecolor":
        return [line.get_color() for line in lines]
    if is_color_like(labelcolor):
        return [labelcolor] * len(lines)
    colors = [c for c, _ in zip(cycle(labelcolor), lines, strict=False)]
    if len(colors) != len(lines):
        raise ValueError(f"labelcolor {labelcolor!r} is not a colour or colour list")
    return colors


def _apply_line_labels(ax: Axes, at: str) -> bool:
    state = get_state(ax)
    side = (state or {}).get("line_labels", {}).get(at)
    if side is None or not side["texts"]:
        return False
    try:
        heights = np.array([t.get_window_extent().height for t in side["texts"]])
    except RuntimeError:
        return False
    changed = False
    for line, text in zip(side["lines"], side["texts"], strict=True):
        anchor = _anchor(line, at)
        if anchor is not None and text.xy != anchor:
            text.xy = anchor
            changed = True
    desired = ax.transData.transform([t.xy for t in side["texts"]])[:, 1]
    px_per_pt = ax.figure.dpi / 72.0
    placed = _stack(desired, heights, side["gap"] * px_per_pt)
    sign = 1.0 if at == "end" else -1.0
    for text, dy in zip(side["texts"], (placed - desired) / px_per_pt, strict=True):
        position = (sign * side["pad"], dy)
        if text.get_position() != position:
            text.set_position(position)
            changed = True
    return changed


def _pava(y: np.ndarray) -> np.ndarray:
    """Return best non-decreasing least-squares fit to `y` (pool adjacent violators)."""
    means: list[float] = []
    counts: list[int] = []
    for value in y:
        mean, count = float(value), 1
        while means and means[-1] > mean:
            mean = (mean * count + means[-1] * counts[-1]) / (count + counts[-1])
            count += counts[-1]
            means.pop()
            counts.pop()
        means.append(mean)
        counts.append(count)
    return np.repeat(means, counts)


def _stack(desired: np.ndarray, heights: np.ndarray, gap: float) -> np.ndarray:
    """Return positions closest to `desired` that keep order and clear each other.

    Minimizes the total squared displacement subject to adjacent positions
    (in sorted order) being at least half of each height plus `gap` apart.
    Subtracting the cumulative separations reduces the constraints to plain
    monotonicity, which `_pava` solves exactly.
    """
    order = np.argsort(desired, kind="stable")
    d = np.asarray(desired, dtype=float)[order]
    h = np.asarray(heights, dtype=float)[order]
    margins = np.concatenate(([0.0], np.cumsum((h[:-1] + h[1:]) / 2 + gap)))
    placed = _pava(d - margins) + margins
    out = np.empty_like(placed)
    out[order] = placed
    return out
