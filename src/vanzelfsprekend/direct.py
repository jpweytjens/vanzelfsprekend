"""Deliberate direct labels: a named artist, an anchor on it, text slid clear of ink.

`label` reads an artist's `label=` for its text, anchors on that artist
at `x=` or `y=`, and slides the text along a helper line, as little as
needed, past every piece of ink in its strip. Several names with one
coordinate form a column on the same helper. One weighted stack
(`placement.stack`) does the placing: pinned ink is an element that
cannot move.
"""

import warnings
from collections.abc import Sequence
from dataclasses import dataclass
from typing import Any, Literal, NamedTuple, cast

import numpy as np
from matplotlib import rcParams
from matplotlib.artist import Artist
from matplotlib.axes import Axes
from matplotlib.collections import PathCollection
from matplotlib.lines import Line2D
from matplotlib.text import Annotation
from matplotlib.transforms import Bbox
from matplotlib.typing import ColorType

from vanzelfsprekend import placement
from vanzelfsprekend.hook import add_applier, ensure_state, get_state, run_appliers
from vanzelfsprekend.lines import _ink_rise, _resolve_colors

Side = Literal["right", "left", "above", "below"]
Helper = tuple[Literal["x", "y"], float]

SIDES: tuple[Side, ...] = ("right", "left", "above", "below")
"""Priority order for an unchosen side (Imhof's ranking and Doumont's practice)."""

SIDE_TOLERANCE = 3.0
"""Accept a side when nothing moved more than this many label heights.

Swept on 2026-09-07 over a resonance figure (anchors 16.6, 17.2, 17.5,
18.5 GHz on a Lorentzian peak) and a three-line column with a crossing
curve, at 0.5, 1, 1.5, 2, 3 and 4: below 3.0 the 17.2 GHz summit label
flipped left, above and left of the summit, although the right is where
Doumont places it; at 3.0 and 4.0 it moved right instead. The 17.5 GHz
label stayed right at every value, and the three-line labels stayed
right from 1.0 up, only going above at 0.5. The 16.6 GHz label, on the
rising left flank, stayed right at every value with no displacement at
all: the flank rises past the label's top, so the right strip is clear
and the selector has no reason to deviate; it sits inside the peak,
which is the anchor's doing, not the tolerance's. 3.0 is the smallest
value that puts both Doumont anchors, 17.2 and 17.5 GHz, on the right.
"""

_ALIGNMENT: dict[str, tuple[str, str]] = {
    "right": ("left", "baseline"),
    "left": ("right", "baseline"),
    "above": ("center", "bottom"),
    "below": ("center", "top"),
}
"""Horizontal and vertical alignment of the text for each side."""


def _perpendicular(helper: Helper) -> tuple[Side, Side]:
    """Return the two sides a column on `helper` can take."""
    return ("right", "left") if helper[0] == "x" else ("above", "below")


def _candidates(ax: Axes) -> list[Artist]:
    return [*ax.get_lines(), *ax.collections]


def _drawn(artist: Artist) -> bool:
    """Return whether `artist` is a line or scatter with at least one finite point."""
    if not isinstance(artist, Line2D | PathCollection):
        return False
    return bool(np.isfinite(_points(artist)).all(axis=1).any())


def _find(ax: Axes, name: str | Artist) -> Artist:
    """Return the artist whose `label=` is `name`, or `name` itself if it is an artist.

    When several artists share the name, the ones with something drawn
    win over empty proxies, so a producer that keeps its legend text on
    an empty line (seaborn) is handled by naming the drawn line with
    `set_label`; if more than one drawn artist remains, the caller must
    pass the artist.
    """
    if isinstance(name, Artist):
        return name
    matches = [artist for artist in _candidates(ax) if artist.get_label() == name]
    if len(matches) > 1:
        drawn = [artist for artist in matches if _drawn(artist)]
        if len(drawn) == 1:
            return drawn[0]
        if drawn:
            matches = drawn
    if len(matches) == 1:
        return matches[0]
    if not matches:
        present = sorted(
            str(artist.get_label())
            for artist in _candidates(ax)
            if not str(artist.get_label()).startswith("_")
        )
        raise ValueError(f"no artist labelled {name!r}; labels present: {present}")
    raise ValueError(
        f"{len(matches)} artists labelled {name!r}; pass the artist instead"
    )


def _points(artist: Artist) -> np.ndarray:
    """Return `artist`'s points as an (n, 2) float array in data space.

    Masked offsets become NaN.
    """
    if isinstance(artist, Line2D):
        return np.column_stack(
            [
                np.asarray(artist.get_xdata(orig=False), dtype=float),
                np.asarray(artist.get_ydata(orig=False), dtype=float),
            ]
        )
    if isinstance(artist, PathCollection):
        offsets = np.ma.asarray(artist.get_offsets(), dtype=float)
        return np.ma.filled(offsets, np.nan).reshape(-1, 2)
    raise ValueError(f"cannot label a {type(artist).__name__}; lines and scatters only")


def _anchor(ax: Axes, artist: Artist, helper: Helper | None) -> tuple[float, float]:
    """Return the data-space point on `artist` that `helper` picks.

    `("x", v)` is the crossing of a line with the vertical at `v`,
    interpolated in display space so log axes come out right, or a
    scatter's point nearest in x. `("y", v)` mirrors that; a curve that
    crosses the horizontal several times anchors at the first crossing
    in data order. `None` is allowed only for a one-point artist.
    """
    points = _points(artist)
    finite = points[np.isfinite(points).all(axis=1)]
    name = str(artist.get_label())
    if not len(finite):
        raise ValueError(
            f"{name!r} has no finite point to anchor on; if its text lives on a legend "
            "proxy, name the drawn artist with set_label first"
        )
    if helper is None:
        if len(finite) == 1:
            return (float(finite[0, 0]), float(finite[0, 1]))
        raise ValueError(
            f"{name!r} has {len(finite)} points; give x= or y= to pick the anchor"
        )
    which, value = helper
    axis = 0 if which == "x" else 1
    display = ax.transData.transform(points)
    probe = finite[0].copy()
    probe[axis] = value
    target = float(ax.transData.transform(probe)[axis])
    outside = f"{which}={value:g} is outside {name!r}"
    if isinstance(artist, Line2D):
        return _crossing(
            ax, display, axis, target, f"{outside}, or falls in a gap of it"
        )
    along = display[:, axis]
    if not (np.nanmin(along) <= target <= np.nanmax(along)):
        raise ValueError(outside)
    i = int(np.nanargmin(np.abs(along - target)))
    return (float(points[i, 0]), float(points[i, 1]))


def _crossing(
    ax: Axes, display: np.ndarray, axis: int, target: float, message: str
) -> tuple[float, float]:
    """Return the first point of `display` where coordinate `axis` equals `target`."""
    a, b = display[:-1], display[1:]
    lo = np.minimum(a[:, axis], b[:, axis])
    hi = np.maximum(a[:, axis], b[:, axis])
    straddles = np.flatnonzero((lo <= target) & (target <= hi))
    if not len(straddles):
        raise ValueError(message)
    i = straddles[0]
    span = b[i, axis] - a[i, axis]
    t = 0.0 if span == 0 else (target - a[i, axis]) / span
    x, y = ax.transData.inverted().transform(a[i] + t * (b[i] - a[i]))
    return (float(x), float(y))


class Ink(NamedTuple):
    """The axes' drawn ink in display pixels, as the geometry the pins are cut from."""

    segments: np.ndarray
    """(m, 2, 2) polyline segments of every visible line."""
    half_widths: np.ndarray
    """(m,) half the stroke width of each segment."""
    points: np.ndarray
    """(k, 2) scatter marker centres."""
    radii: np.ndarray
    """(k,) marker radii."""
    boxes: list[Bbox]
    """Window extents of texts and patches."""


_NO_INK = Ink(np.zeros((0, 2, 2)), np.zeros(0), np.zeros((0, 2)), np.zeros(0), [])
"""An empty `Ink`, for the fallback that draws over everything."""


_NONE = (None, "None", "", " ")
"""matplotlib's spellings of an absent line style or marker."""


def _ink(ax: Axes, exclude: set[Artist]) -> Ink:
    """Harvest the visible ink on `ax`, leaving out the artists in `exclude`.

    A line contributes its stroke as segments, unless its line style is
    none, and its markers as points of half the marker size plus half the
    edge width. A scatter contributes its markers the same way, the
    diameter being the square root of `s`. Spines, ticks, tick labels,
    axis labels and the legend are not ink: a label may run over
    furniture, the same stance `line_labels` takes. Collections other
    than scatters are not harvested either.
    """
    px_per_pt = ax.figure.dpi / 72.0
    segments, half_widths, points, radii, boxes = [], [], [], [], []
    for line in ax.get_lines():
        if line in exclude or not line.get_visible():
            continue
        vertices = line.get_transform().transform(line.get_path().vertices)
        if line.get_linestyle() not in _NONE:
            seg = np.stack([vertices[:-1], vertices[1:]], axis=1)
            seg = seg[np.isfinite(seg).all(axis=(1, 2))]
            segments.append(seg)
            half_widths.append(np.full(len(seg), line.get_linewidth() * px_per_pt / 2))
        if line.get_marker() not in _NONE:
            marks = vertices[np.isfinite(vertices).all(axis=1)]
            radius_pt = (line.get_markersize() + line.get_markeredgewidth()) / 2
            points.append(marks)
            radii.append(np.full(len(marks), radius_pt * px_per_pt))
    for collection in ax.collections:
        if (
            collection in exclude
            or not collection.get_visible()
            or not isinstance(collection, PathCollection)
        ):
            continue
        raw_offsets = np.ma.filled(
            np.ma.asarray(collection.get_offsets(), dtype=float), np.nan
        )
        offsets = collection.get_offset_transform().transform(raw_offsets)
        sizes = np.asarray(collection.get_sizes(), dtype=float)
        if sizes.size == 0:
            sizes = np.array([rcParams["lines.markersize"] ** 2])
        edges = np.asarray(
            collection.get_linewidths(),  # ty: ignore[unresolved-attribute]
            dtype=float,
        )
        if edges.size == 0:
            edges = np.zeros(1)
        diameter_pt = np.sqrt(np.resize(sizes, len(offsets)))
        radius_pt = (diameter_pt + np.resize(edges, len(offsets))) / 2
        finite = np.isfinite(offsets).all(axis=1)
        points.append(offsets[finite])
        radii.append(radius_pt[finite] * px_per_pt)
    for text in ax.texts:
        if text in exclude or not text.get_visible() or not text.get_text():
            continue
        boxes.append(text.get_window_extent())
    for patch in ax.patches:
        if patch in exclude or not patch.get_visible():
            continue
        boxes.append(patch.get_window_extent())
    return Ink(
        np.concatenate(segments) if segments else np.zeros((0, 2, 2)),
        np.concatenate(half_widths) if half_widths else np.zeros(0),
        np.concatenate(points) if points else np.zeros((0, 2)),
        np.concatenate(radii) if radii else np.zeros(0),
        boxes,
    )


def _merge(intervals: list[tuple[float, float]], gap: float) -> np.ndarray:
    """Return `intervals` sorted and merged wherever two sit within `gap`."""
    if not intervals:
        return np.zeros((0, 2))
    ordered = sorted(intervals)
    merged = [list(ordered[0])]
    for lo, hi in ordered[1:]:
        if lo <= merged[-1][1] + gap:
            merged[-1][1] = max(merged[-1][1], hi)
        else:
            merged.append([lo, hi])
    return np.array(merged, dtype=float)


def _pins(ink: Ink, strip: tuple[float, float], axis: int, gap: float) -> np.ndarray:
    """Return the (k, 2) intervals along `axis` that ink occupies inside `strip`.

    `strip` bounds the perpendicular coordinate (x for a label sliding in
    y). A segment contributes the extent of its clipped part, widened by
    its half width; a marker its diameter; a box its side. Intervals
    within `gap` of each other merge, so a pair of pins never asks the
    stack to separate them.
    """
    perp = 1 - axis
    lo, hi = strip
    intervals: list[tuple[float, float]] = []
    if len(ink.segments):
        p0, p1 = ink.segments[:, 0, perp], ink.segments[:, 1, perp]
        s0, s1 = ink.segments[:, 0, axis], ink.segments[:, 1, axis]
        w = ink.half_widths
        dp = p1 - p0
        with np.errstate(divide="ignore", invalid="ignore"):
            ta = (lo - w - p0) / dp
            tb = (hi + w - p0) / dp
        t0 = np.clip(np.minimum(ta, tb), 0.0, 1.0)
        t1 = np.clip(np.maximum(ta, tb), 0.0, 1.0)
        parallel = dp == 0
        hits = np.where(parallel, (p0 >= lo - w) & (p0 <= hi + w), t1 > t0)
        t0 = np.where(parallel, 0.0, t0)
        t1 = np.where(parallel, 1.0, t1)
        a = s0 + t0 * (s1 - s0)
        b = s0 + t1 * (s1 - s0)
        low = np.minimum(a, b) - w
        high = np.maximum(a, b) + w
        intervals += list(zip(low[hits].tolist(), high[hits].tolist(), strict=True))
    if len(ink.points):
        inside = (ink.points[:, perp] + ink.radii >= lo) & (
            ink.points[:, perp] - ink.radii <= hi
        )
        s, r = ink.points[inside, axis], ink.radii[inside]
        intervals += list(zip((s - r).tolist(), (s + r).tolist(), strict=True))
    for box in ink.boxes:
        b_lo, b_hi = (box.x0, box.x1) if perp == 0 else (box.y0, box.y1)
        if b_hi >= lo and b_lo <= hi:
            intervals.append((box.y0, box.y1) if axis == 1 else (box.x0, box.x1))
    return _merge(intervals, gap)


def label(
    ax: Axes,
    name: str | Artist | Sequence[str | Artist],
    *,
    x: Any | None = None,
    y: Any | None = None,
    side: Side | None = None,
    labelcolor: str | ColorType | list[ColorType] = "linecolor",
    pad: float = 4.0,
    gap: float = placement.GAP,
) -> list[Annotation]:
    """Put a label beside the artist called `name`, or a column of them.

    The text is the artist's `label=`, the same string a legend would
    show, and the anchor is where `x=` or `y=` meets the artist: a line's
    crossing, a scatter's nearest point. From there the text slides along
    a helper line through the anchor, as little as needed, to clear every
    mark and text in its way. It goes right of the anchor by default and
    left, above or below when the right is blocked; `side=` chooses.
    Lines, scatters, texts and patches count as ink; fills and other
    collections do not. A one-point artist needs no anchor. Several
    names with one coordinate form a column on the same helper, stacked
    in order; a column takes only the sides perpendicular to its helper.

    An existing legend is hidden, since the labels replace it, and
    `restore` brings it back. Calling again with the same artists rebuilds
    that group. Labels are re-solved on every draw.

    Parameters
    ----------
    ax : matplotlib.axes.Axes
        The axes holding the artist.
    name : str, artist, or sequence of them
        The artist's `label=`; or the artist itself, when two drawn
        artists share a label. A sequence is a column. A producer that
        keeps the legend text on an empty proxy (seaborn names its data
        lines `_child0`, `_child1`, ...) is handled by naming the drawn
        line first, `line.set_label("A")`: a drawn artist wins the name
        over an empty proxy.
    x, y : float, optional
        The spine coordinate of the anchor; give one, not both. Required
        for a multi-point artist and for a column. In the axis's own
        units, so a date works on a date axis.
    side : {'right', 'left', 'above', 'below'}, optional
        Where the text goes. `None` tries the sides in that order and
        takes the first that fits.
    labelcolor : color, list of color, or 'linecolor'
        As in `line_labels`: the artist's own colour, one colour, or a
        list cycled over the names.
    pad : float
        Points between the anchor (or the column's helper) and the near
        edge of the text.
    gap : float
        Minimum clearance in points between the text and anything else.

    Returns
    -------
    list of matplotlib.text.Annotation
        The label artists, in `name` order.
    """
    column = not isinstance(name, str | Artist)
    names = list(cast("Sequence[str | Artist]", name)) if column else [name]
    if x is not None and y is not None:
        raise ValueError("give x= or y=, not both")
    helper: Helper | None
    if x is not None:
        helper = ("x", float(ax.convert_xunits(x)))
    elif y is not None:
        helper = ("y", float(ax.convert_yunits(y)))
    else:
        helper = None
    if column and helper is None:
        raise ValueError("a column of labels needs x= or y=")
    if side is not None and side not in SIDES:
        raise ValueError(f"side must be one of {SIDES}, got {side!r}")
    if (
        column
        and helper is not None
        and side is not None
        and side not in _perpendicular(helper)
    ):
        allowed = " or ".join(_perpendicular(helper))
        raise ValueError(
            f"a column on {helper[0]}= can only go {allowed}, got {side!r}"
        )
    if not names:
        raise ValueError("no names given")
    artists = [_find(ax, n) for n in names]
    anchors = [_anchor(ax, artist, helper) for artist in artists]
    state = ensure_state(ax)
    legend = ax.get_legend()
    if legend is not None:
        state.setdefault("legend", {"artist": legend, "visible": legend.get_visible()})
        legend.set_visible(False)
    groups: list[dict] = state.setdefault("direct", [])
    for prior in [group for group in groups if group["artists"] == artists]:
        for text in prior["texts"]:
            text.remove()
        groups.remove(prior)
    texts = [
        ax.annotate(
            str(artist.get_label()),
            xy=anchor,
            xytext=(pad, 0.0),
            textcoords="offset points",
            ha="left",
            va="baseline",
            color=color,
            annotation_clip=False,
        )
        for artist, anchor, color in zip(
            artists, anchors, _resolve_colors(labelcolor, artists), strict=True
        )
    ]
    groups.append(
        {
            "artists": artists,
            "texts": texts,
            "helper": helper,
            "side": side,
            "pad": pad,
            "gap": gap,
            "warned": False,
        }
    )
    add_applier(ax, "direct", _apply_direct)
    run_appliers(ax)
    return list(texts)


@dataclass
class _Attempt:
    side: Side
    base_px: float | None
    """The strip's base on the perpendicular axis.

    The column helper, or None for the anchor itself.
    """
    sizes: np.ndarray
    centres: np.ndarray
    offsets: np.ndarray
    placed: np.ndarray
    displacement: float
    over: bool


def _measure(texts: list[Annotation], side: Side) -> tuple[np.ndarray, np.ndarray]:
    """Align `texts` for `side`.

    Return their (n, 2) box sizes and box centres in pixels.
    """
    ha, va = _ALIGNMENT[side]
    sizes, centres = [], []
    for text in texts:
        text.set_ha(ha)  # ty: ignore[unresolved-attribute]
        text.set_va(va)  # ty: ignore[unresolved-attribute]
        box = text.get_window_extent()
        sizes.append((box.width, box.height))
        centres.append(((box.x0 + box.x1) / 2, (box.y0 + box.y1) / 2))
    return np.array(sizes), np.array(centres)


def _solve_side(
    side: Side,
    anchors: np.ndarray,
    sizes: np.ndarray,
    centres: np.ndarray,
    offsets: np.ndarray,
    rest: np.ndarray,
    base_px: float | None,
    pad_px: float,
    gap_px: float,
    ink: Ink,
) -> tuple[np.ndarray, float, bool]:
    """Stack the labels along the helper on `side`.

    Return positions, displacement, and over-capacity. Positions are box
    centres along the sliding axis, in pixels. The displacement is the
    largest label move plus the largest pin move. `base_px` is where the
    strip starts on the perpendicular axis: a column's helper, or `None`
    for each label's own anchor.
    """
    axis = 1 if side in ("right", "left") else 0
    perp = 1 - axis
    sign = 1.0 if side in ("right", "above") else -1.0
    shift = centres[:, axis] - anchors[:, axis] - offsets[:, axis]
    desired = anchors[:, axis] + rest + shift
    base = anchors[:, perp] if base_px is None else np.full(len(anchors), base_px)
    near = base + sign * pad_px
    far = near + sign * sizes[:, perp].max()
    strip = (float(min(near.min(), far.min())), float(max(near.max(), far.max())))
    pins = _pins(ink, strip, axis, gap_px)
    centre = pins.mean(axis=1)
    width = pins[:, 1] - pins[:, 0]
    # The tie rule reads the anchor, not the box-centre target: the target
    # sits a fraction of a pixel off the anchor (ink centring, descender
    # space) and would miss a thin pin the anchor is on. Preferring after
    # the pin matches where a baseline-aligned label sits; tried first, and
    # only if that traps a label between its own pin and the next one does
    # the other direction get a look, since it may open onto a bigger gap.
    # The retry is attempt-wide: every label that sits on a pin is re-tied
    # below it together, not one label at a time.
    along = anchors[:, axis]
    n = len(desired)

    def solve(prefer_after: bool) -> tuple[np.ndarray, float, bool]:
        key = desired.copy()
        for lo, hi, mid in zip(pins[:, 0], pins[:, 1], centre, strict=True):
            inside = (along >= lo) & (along <= hi)
            if prefer_after:
                key[inside] = np.maximum(key[inside], mid + 1e-9)
            else:
                key[inside] = np.minimum(key[inside], mid - 1e-9)
        placed = placement.stack(
            np.concatenate([desired, centre]),
            np.concatenate([sizes[:, axis], width]),
            gap_px,
            weights=np.concatenate(
                [np.ones(n), np.full(len(centre), placement.PIN_WEIGHT)]
            ),
            key=np.concatenate([key, centre]),
        )
        label_move = float(np.abs(placed[:n] - desired).max())
        pin_move = float(np.abs(placed[n:] - centre).max()) if len(centre) else 0.0
        return placed[:n], label_move + pin_move, pin_move > placement.PIN_TOLERANCE

    placed, displacement, over = solve(prefer_after=True)
    if over:
        alt_placed, alt_displacement, alt_over = solve(prefer_after=False)
        if not alt_over:
            return alt_placed, alt_displacement, alt_over
    return placed, displacement, over


def _offsets(attempt: _Attempt, anchors: np.ndarray, pad_px: float) -> np.ndarray:
    """Return the (n, 2) pixel offsets from each anchor that realise `attempt`."""
    axis = 1 if attempt.side in ("right", "left") else 0
    perp = 1 - axis
    sign = 1.0 if attempt.side in ("right", "above") else -1.0
    shift = attempt.centres[:, axis] - anchors[:, axis] - attempt.offsets[:, axis]
    out = np.empty_like(anchors)
    out[:, axis] = attempt.placed - anchors[:, axis] - shift
    base = anchors[:, perp] if attempt.base_px is None else attempt.base_px
    out[:, perp] = base + sign * pad_px - anchors[:, perp]
    return out


def _attempt(
    side: Side,
    group: dict,
    anchors: np.ndarray,
    helper_px: float | None,
    ink: Ink,
    px_per_pt: float,
) -> _Attempt:
    """Measure `group` for `side`, solve it against `ink`, and return the attempt."""
    texts = group["texts"]
    sizes, centres = _measure(texts, side)
    offsets = np.array([text.get_position() for text in texts]) * px_per_pt
    if side in ("right", "left"):
        rest = np.array([-_ink_rise(text) * px_per_pt for text in texts])
    else:
        rest = np.zeros(len(texts))
    # The helper is the strip's base only when it is perpendicular to the
    # sliding axis: always for a column, and for a single label only when
    # the side matches (x= with right/left, y= with above/below). Otherwise
    # the helper merely picked the anchor, and the strip starts at the
    # anchor itself.
    perp = 0 if side in ("right", "left") else 1
    helper_axis = (
        None if group["helper"] is None else (0 if group["helper"][0] == "x" else 1)
    )
    base_px = helper_px if helper_axis == perp else None
    placed, displacement, over = _solve_side(
        side,
        anchors,
        sizes,
        centres,
        offsets,
        rest,
        base_px,
        group["pad"] * px_per_pt,
        group["gap"] * px_per_pt,
        ink,
    )
    return _Attempt(side, base_px, sizes, centres, offsets, placed, displacement, over)


def _place(
    group: dict,
    anchors: np.ndarray,
    helper_px: float | None,
    ink: Ink,
    px_per_pt: float,
) -> tuple[np.ndarray, tuple[str, str]]:
    """Return per-label offsets in points and the text alignment for `group`.

    Tries the sides in priority order and keeps the first whose
    displacement stays within `SIDE_TOLERANCE` label heights; failing
    that, the smallest displacement among the sides that are not over
    capacity; failing that, warns once and places on the least bad side
    with the ink ignored, so a label is drawn over ink rather than lost.
    """
    if group["side"] is not None:
        sides: tuple[Side, ...] = (group["side"],)
    elif len(group["texts"]) > 1:
        sides = _perpendicular(group["helper"])
    else:
        sides = SIDES
    attempts = [
        _attempt(side, group, anchors, helper_px, ink, px_per_pt) for side in sides
    ]
    tolerance = SIDE_TOLERANCE * max(a.sizes[:, 1].max() for a in attempts)
    feasible = [a for a in attempts if not a.over]
    chosen = next((a for a in feasible if a.displacement <= tolerance), None)
    if chosen is None and feasible:
        chosen = min(feasible, key=lambda a: a.displacement)
    if chosen is None:
        if not group["warned"]:
            names = [text.get_text() for text in group["texts"]]
            warnings.warn(
                f"vanzelfsprekend: labels {names} do not fit on any side; drawn over "
                "the ink, move the anchor or pass side=",
                stacklevel=2,
            )
            group["warned"] = True
        least_bad = min(attempts, key=lambda a: a.displacement).side
        chosen = _attempt(least_bad, group, anchors, helper_px, _NO_INK, px_per_pt)
    pad_px = group["pad"] * px_per_pt
    return _offsets(chosen, anchors, pad_px) / px_per_pt, _ALIGNMENT[chosen.side]


def _apply_direct(ax: Axes) -> bool:
    """Re-solve every label group on ax in call order; return whether anything moved."""
    state = get_state(ax)
    groups: list[dict] = (state or {}).get("direct") or []
    # The managed y-label of `ylabel(place="above")` is an `ax.text` child,
    # furniture, not ink; everything else in `ax.texts` counts.
    furniture = {(state or {}).get("labels", {}).get("ylabel_above_text")} - {None}
    px_per_pt = ax.figure.dpi / 72.0
    changed = False
    for i, group in enumerate(groups):
        try:
            anchors_data = [
                _anchor(ax, artist, group["helper"]) for artist in group["artists"]
            ]
        except ValueError:
            continue
        before = [(t.get_position(), t.get_ha(), t.get_va()) for t in group["texts"]]
        for text, anchor in zip(group["texts"], anchors_data, strict=True):
            if text.xy != anchor:
                text.xy = anchor
                changed = True
        anchors = ax.transData.transform(anchors_data)
        helper_px = None
        if group["helper"] is not None:
            axis = 0 if group["helper"][0] == "x" else 1
            probe = list(anchors_data[0])
            probe[axis] = group["helper"][1]
            helper_px = float(ax.transData.transform(probe)[axis])
        pending = {text for later in groups[i:] for text in later["texts"]}
        try:
            ink = _ink(ax, pending | furniture)
            offsets, (ha, va) = _place(group, anchors, helper_px, ink, px_per_pt)
        except RuntimeError:
            for text, previous in zip(group["texts"], before, strict=True):
                text.set_ha(previous[1])
                text.set_va(previous[2])
            return changed
        for text, offset, previous in zip(group["texts"], offsets, before, strict=True):
            position = (float(offset[0]), float(offset[1]))
            text.set_position(position)
            text.set_ha(ha)
            text.set_va(va)
            if (position, ha, va) != previous:
                changed = True
    return changed
