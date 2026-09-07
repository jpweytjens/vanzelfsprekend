"""Deliberate direct labels: a named artist, an anchor on it, text slid clear of ink.

`label` reads an artist's `label=` for its text, anchors on that artist
at `x=` or `y=`, and slides the text along a helper line, as little as
needed, past every piece of ink in its strip. Several names with one
coordinate form a column on the same helper. One weighted stack
(`placement.stack`) does the placing: pinned ink is an element that
cannot move.
"""

from typing import Literal, NamedTuple

import numpy as np
from matplotlib import rcParams
from matplotlib.artist import Artist
from matplotlib.axes import Axes
from matplotlib.collections import PathCollection
from matplotlib.lines import Line2D
from matplotlib.transforms import Bbox

Side = Literal["right", "left", "above", "below"]
Helper = tuple[Literal["x", "y"], float]

SIDES: tuple[Side, ...] = ("right", "left", "above", "below")
"""Priority order for an unchosen side (Imhof's ranking and Doumont's practice)."""

SIDE_TOLERANCE = 1.0
"""Accept a side when nothing moved more than this many label heights (Task 9)."""

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
