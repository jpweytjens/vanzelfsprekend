"""End-of-line direct labels: label each line at one end instead of in a legend."""

import warnings
from functools import partial
from itertools import cycle
from typing import Literal, cast

import numpy as np
from matplotlib.axes import Axes
from matplotlib.colors import is_color_like
from matplotlib.lines import Line2D
from matplotlib.text import Annotation
from matplotlib.textpath import TextPath
from matplotlib.typing import ColorType

from vanzelfsprekend import placement
from vanzelfsprekend.hook import add_applier, ensure_state, get_state, run_appliers


def line_labels(
    ax: Axes,
    at: Literal["start", "end"] = "end",
    labelcolor: str | ColorType | list[ColorType] = "linecolor",
    pad: float = 4.0,
    gap: float = placement.GAP,
    labels: list[str | None] | None = None,
) -> list[Annotation]:
    """Label each line at one end, in place of a legend.

    Text comes from each line's `label=`; lines with matplotlib's
    auto-generated `_`-prefixed labels or without a finite point are
    skipped. Labels sit just outside their line's end, each label's ink
    centred on the line end (measured from the glyph outlines, so the
    font's em-box metrics cannot skew it), and are pushed
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
    labels : list of (str or None), optional
        Supply the text yourself instead of reading each line's
        `label=`. Needed for producers that keep the legend text on a
        separate artist from the drawn line (seaborn labels its data
        lines `_child0`, `_child1`, ... and carries the real text on
        empty proxy lines). The list has one entry per *anchorable*
        line (a line with a finite end point, in draw order), and a
        `None` or `""` entry skips that line. A length that does not
        match the anchorable lines raises `ValueError`. With the
        default `labels=None`, lines are read as above and an empty
        result warns, pointing here.

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
    if labels is None:
        anchored = [
            (line, label, anchor)
            for line in ax.get_lines()
            if (label := _labeled(line)) is not None
            and (anchor := _anchor(line, at)) is not None
        ]
        if not anchored:
            warnings.warn(
                "vanzelfsprekend: no labelled lines with a finite end point "
                "found; pass labels=... to supply them",
                stacklevel=2,
            )
    else:
        targets = [
            (line, anchor)
            for line in ax.get_lines()
            if (anchor := _anchor(line, at)) is not None
        ]
        if len(labels) != len(targets):
            raise ValueError(
                f"labels has {len(labels)} entries but there are "
                f"{len(targets)} lines to label"
            )
        anchored = [
            (line, label, anchor)
            for (line, anchor), label in zip(targets, labels, strict=True)
            if label not in (None, "")
        ]
    lines = [line for line, _, _ in anchored]
    sign = 1.0 if at == "end" else -1.0
    texts = [
        ax.annotate(
            label,
            xy=anchor,
            xytext=(sign * pad, 0.0),
            textcoords="offset points",
            ha="left" if at == "end" else "right",
            va="baseline",
            color=color,
            annotation_clip=False,
        )
        for (_, label, anchor), color in zip(
            anchored, _resolve_colors(labelcolor, lines), strict=True
        )
    ]
    for text in texts:
        text.set_position((sign * pad, -_ink_rise(text)))
    sides[at] = {"lines": lines, "texts": texts, "pad": pad, "gap": gap}
    add_applier(ax, f"line_labels.{at}", partial(_apply_line_labels, at=at))
    run_appliers(ax)
    return texts


def _labeled(line: Line2D) -> str | None:
    """Return `line`'s legend text, or None for auto-generated or non-string labels."""
    label = line.get_label()
    if not isinstance(label, str) or label.startswith("_"):
        return None
    return label


def _anchor(line: Line2D, at: str) -> tuple[float, float] | None:
    x = np.asarray(line.get_xdata(orig=False), dtype=float)
    y = np.asarray(line.get_ydata(orig=False), dtype=float)
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
        return [cast("ColorType", labelcolor)] * len(lines)
    if not isinstance(labelcolor, list | tuple) or not labelcolor:
        raise ValueError(f"labelcolor {labelcolor!r} is not a colour or colour list")
    return [
        cast("ColorType", c) for c, _ in zip(cycle(labelcolor), lines, strict=False)
    ]


def _ink_rise(text: Annotation) -> float:
    """Return the centre of `text`'s glyph ink above the baseline, in points.

    Placing the baseline this far below an anchor centres the drawn
    glyphs on it. Measured from the glyph outlines via `TextPath`,
    which sidesteps fonts whose em-box metrics misplace their ink
    (macOS Helvetica Neue shifts everything ~0.13 em down).
    """
    path = TextPath(
        (0.0, 0.0),
        text.get_text(),
        size=float(text.get_fontsize()),
        prop=text.get_fontproperties(),
    )
    bounds = path.get_extents()
    if not np.isfinite([bounds.y0, bounds.y1]).all():
        return 0.0
    return float(bounds.y0 + bounds.y1) / 2


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
    placed = placement.stack(desired, heights, side["gap"] * px_per_pt)
    sign = 1.0 if at == "end" else -1.0
    for text, dy in zip(side["texts"], (placed - desired) / px_per_pt, strict=True):
        position = (sign * side["pad"], dy - _ink_rise(text))
        if text.get_position() != position:
            text.set_position(position)
            changed = True
    return changed
