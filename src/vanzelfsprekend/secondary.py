"""A second unit on the same data: a mirrored, frame-styled secondary axis."""

from collections.abc import Callable

import numpy as np
from matplotlib.axes import Axes
from matplotlib.ticker import FixedLocator

from vanzelfsprekend.hook import add_applier, ensure_state, get_state
from vanzelfsprekend.locator import visible_interval
from vanzelfsprekend.mute import LINE_WIDTH
from vanzelfsprekend.palettes import LINE_INK, TEXT_INK

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
    through `functions`), its spine, ticks and labels take the frame ink,
    and it follows the host every draw and tears down with `restore(ax)`.

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
    """
    if where not in _WHERE:
        raise ValueError(f"where must be one of {sorted(_WHERE)}, got {where!r}")
    axis_name = _WHERE[where]
    forward, _inverse = functions
    make = ax.secondary_xaxis if axis_name == "x" else ax.secondary_yaxis
    # `where` is validated against `_WHERE` above; ty cannot narrow a dict
    # membership check to the `Literal` sides each maker wants.
    secax = make(where, functions=functions)  # ty: ignore[invalid-argument-type]

    # One-shot styling: colours do not drift, only positions do.
    spine = secax.spines[where]
    spine.set_edgecolor(LINE_INK)
    spine.set_linewidth(LINE_WIDTH)
    secax.tick_params(
        which="both", color=LINE_INK, width=LINE_WIDTH, labelcolor=TEXT_INK
    )
    # Match the frame's stand-off: a loose `range_frame` pushes the host's
    # axis spine outward by a few points, so mirror that offset onto the
    # secondary and the two feel the same. Points are resize-invariant, so
    # this is one-shot like the colours.
    host_spine = "bottom" if axis_name == "x" else "left"
    position = ax.spines[host_spine].get_position()
    if isinstance(position, tuple) and position[0] == "outward":
        spine.set_position(("outward", position[1]))

    state = ensure_state(ax)
    state.setdefault("secondary", []).append(
        {"secax": secax, "axis": axis_name, "forward": forward, "spine": where}
    )
    add_applier(ax, "secondary", _apply_secondary)
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
        changed = _mirror_one(ax, entry) or changed
    return changed


def _mirror_one(ax: Axes, entry: dict) -> bool:
    host_axis = ax.xaxis if entry["axis"] == "x" else ax.yaxis
    secax = entry["secax"]
    sec_axis = secax.xaxis if entry["axis"] == "x" else secax.yaxis
    forward = entry["forward"]
    changed = False

    desired = np.asarray(forward(host_axis.get_majorticklocs()), dtype=float)
    if not np.array_equal(sec_axis.get_majorticklocs(), desired):
        sec_axis.set_major_locator(FixedLocator(desired))
        changed = True

    dmin, dmax = visible_interval(host_axis)
    if np.isfinite([dmin, dmax]).all() and dmin != dmax:
        lo, hi = sorted((float(forward(dmin)), float(forward(dmax))))
        spine = secax.spines[entry["spine"]]
        if spine.get_bounds() != (lo, hi):
            spine.set_bounds(lo, hi)
            changed = True
    return changed
