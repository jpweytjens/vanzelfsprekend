"""Deliberate direct labels: a named artist, an anchor on it, text slid clear of ink.

`label` reads an artist's `label=` for its text, anchors on that artist
at `x=` or `y=`, and slides the text along a helper line, as little as
needed, past every piece of ink in its strip. Several names with one
coordinate form a column on the same helper. One weighted stack
(`placement.stack`) does the placing: pinned ink is an element that
cannot move.
"""

from typing import Literal

import numpy as np
from matplotlib.artist import Artist
from matplotlib.axes import Axes
from matplotlib.collections import PathCollection
from matplotlib.lines import Line2D

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
    """Return `artist`'s points as an (n, 2) float array in data space, NaN kept."""
    if isinstance(artist, Line2D):
        return np.column_stack(
            [
                np.asarray(artist.get_xdata(orig=False), dtype=float),
                np.asarray(artist.get_ydata(orig=False), dtype=float),
            ]
        )
    if isinstance(artist, PathCollection):
        return np.asarray(artist.get_offsets(), dtype=float).reshape(-1, 2)
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
