"""A second unit on the same data: a mirrored, frame-styled secondary axis."""

from collections.abc import Callable

import numpy as np
from matplotlib.axes import Axes
from matplotlib.axis import Axis
from matplotlib.colors import to_rgba
from matplotlib.ticker import FixedLocator, Formatter

from vanzelfsprekend.hook import add_applier, ensure_state, get_state
from vanzelfsprekend.locator import visible_interval
from vanzelfsprekend.ticks import _tick_geometry

_WHERE = {"top": "x", "bottom": "x", "left": "y", "right": "y"}


def secondary_frame(
    ax: Axes,
    functions: tuple[Callable, Callable],
    where: str = "top",
) -> Axes:
    """Add a second-unit axis that mirrors `ax`'s ticks, styled like the frame.

    The companion to `range_frame` for a second *unit* on the same data
    (radians and degrees, degrees C and F, a count and its log), never a
    second dataset. A secondary axis is created on the `where` side, its
    major ticks are kept sitting exactly under the host's (relabelled
    through `functions`), its spine and tick marks take the host's ink,
    width and tick direction, and it follows the host every draw, so a
    later `mute` or `tick_direction` on the host reaches it too. It tears
    down with `restore(ax)`.

    Parameters
    ----------
    ax : matplotlib.axes.Axes
        The host axes. Its major ticks drive the secondary's.
    functions : tuple of two callables
        `(forward, inverse)`, passed to matplotlib's
        `secondary_xaxis`/`secondary_yaxis` exactly as they take them:
        `forward` maps the host coordinate to the secondary unit,
        `inverse` back. The mirror places a secondary tick labelled
        `forward(p)` at each host tick position `p`.
    where : {'top', 'bottom', 'left', 'right'}
        The side, which also picks the axis: x for top/bottom, y for
        left/right.

    Returns
    -------
    matplotlib.axes.Axes
        The secondary axes, so a label can be set on it.

    Notes
    -----
    Sets no tick formatter: a mirrored degree axis is already whole
    numbers, and any other unit takes the default numeric formatter.
    An accent on the host is mirrored too: each secondary tick label
    takes the colour of the host label under it, and is blanked when
    `accent(only_features=True)` blanks the host's.
    """
    if where not in _WHERE:
        raise ValueError(f"where must be one of {sorted(_WHERE)}, got {where!r}")
    axis_name = _WHERE[where]
    forward, _inverse = functions
    make = ax.secondary_xaxis if axis_name == "x" else ax.secondary_yaxis
    # `where` is validated against `_WHERE` above; ty cannot narrow a dict
    # membership check to the `Literal` sides each maker wants.
    secax = make(where, functions=functions)  # ty: ignore[invalid-argument-type]

    # Match the frame's stand-off: a loose `range_frame` pushes the host's
    # axis spine outward by a few points, so mirror that offset onto the
    # secondary and the two feel the same. Points are resize-invariant, so
    # this is one-shot, unlike the ink and tick style the applier follows.
    host_spine = "bottom" if axis_name == "x" else "left"
    position = ax.spines[host_spine].get_position()
    if isinstance(position, tuple) and position[0] == "outward":
        secax.spines[where].set_position(("outward", position[1]))

    state = ensure_state(ax)
    entry = {"secax": secax, "axis": axis_name, "forward": forward, "spine": where}
    state.setdefault("secondary", []).append(entry)
    add_applier(ax, "secondary", _apply_secondary)
    _mirror_style(ax, entry)
    # A SecondaryAxis is used as an axes but is not an `Axes` subclass in
    # the stubs (both descend from the private base).
    return secax  # ty: ignore[invalid-return-type]


def _apply_secondary(ax: Axes) -> bool:
    """Re-mirror every secondary on `ax` from the host's current ticks."""
    state = get_state(ax)
    if state is None or "secondary" not in state:
        return False
    changed = False
    for entry in state["secondary"]:
        changed = _mirror_style(ax, entry) or changed
        changed = _mirror_one(ax, entry) or changed
    return changed


def _mirror_style(ax: Axes, entry: dict) -> bool:
    """Give the secondary's spine and tick marks the host's ink and direction."""
    host_spine = ax.spines["bottom" if entry["axis"] == "x" else "left"]
    secax = entry["secax"]
    spine = secax.spines[entry["spine"]]
    changed = False
    if spine.get_edgecolor() != host_spine.get_edgecolor():
        spine.set_edgecolor(host_spine.get_edgecolor())
        changed = True
    if spine.get_linewidth() != host_spine.get_linewidth():
        spine.set_linewidth(host_spine.get_linewidth())
        changed = True

    host_axis = ax.xaxis if entry["axis"] == "x" else ax.yaxis
    ticks = host_axis.get_major_ticks()
    if not ticks:
        return changed
    mark = ticks[0].tick1line
    geometry = _tick_geometry(host_axis)
    style = {
        "direction": geometry["direction"],
        "length": geometry["major_length"],
        "color": to_rgba(mark.get_color()),
        "width": mark.get_markeredgewidth(),
    }
    if entry.get("style") != style:
        secax.tick_params(which="major", **style)
        entry["style"] = style
        changed = True
    return changed


def _mirror_one(ax: Axes, entry: dict) -> bool:
    host_axis = ax.xaxis if entry["axis"] == "x" else ax.yaxis
    secax = entry["secax"]
    sec_axis = secax.xaxis if entry["axis"] == "x" else secax.yaxis
    forward = entry["forward"]
    changed = False

    desired = np.asarray(forward(host_axis.get_majorticklocs()), dtype=float)
    if not np.array_equal(sec_axis.get_majorticklocs(), desired):
        sec_axis.set_major_locator(FixedLocator(list(desired)))
        changed = True

    dmin, dmax = visible_interval(host_axis)
    if np.isfinite([dmin, dmax]).all() and dmin != dmax:
        lo, hi = sorted((float(forward(dmin)), float(forward(dmax))))
        spine = secax.spines[entry["spine"]]
        if spine.get_bounds() != (lo, hi):
            spine.set_bounds(lo, hi)
            changed = True

    return _mirror_labels(host_axis, sec_axis, forward, entry) or changed


def _mirror_labels(
    host_axis: Axis, sec_axis: Axis, forward: Callable, entry: dict
) -> bool:
    """Copy each host tick label's colour and blankness onto the tick under it.

    The hook runs after a draw, so the host's labels already carry
    whatever `accent` gave them; mirroring the labels rather than the
    accent state also follows a later re-accent or its removal.
    """
    changed = False
    host_ticks = list(
        zip(host_axis.get_majorticklocs(), host_axis.get_major_ticks(), strict=False)
    )
    blank: list[float] = []
    for loc, tick in zip(
        sec_axis.get_majorticklocs(), sec_axis.get_major_ticks(), strict=False
    ):
        host = next(
            (t for p, t in host_ticks if np.isclose(float(forward(p)), loc)), None
        )
        if host is None:
            continue
        colour = host.label1.get_color()
        if to_rgba(tick.label1.get_color()) != to_rgba(colour):
            tick.label1.set_color(colour)
            changed = True
        if host.label1.get_text() == "":
            blank.append(loc)
    if blank or entry.get("blank"):
        formatter = sec_axis.get_major_formatter()
        if not isinstance(formatter, _Blanking):
            sec_axis.set_major_formatter(_Blanking(formatter, entry))
            changed = True
        if entry.get("blank") != blank:
            entry["blank"] = blank
            changed = True
    return changed


class _Blanking(Formatter):
    """Wrap the secondary's formatter, writing nothing at the host's blanked ticks."""

    def __init__(self, inner: Formatter, entry: dict) -> None:
        self._inner = inner
        self._entry = entry

    def set_locs(self, locs: list[float]) -> None:
        super().set_locs(locs)
        self._inner.set_locs(locs)

    def __call__(self, x: float, pos: int | None = None) -> str:
        if any(np.isclose(x, b) for b in self._entry.get("blank", [])):
            return ""
        return self._inner(x, pos)
