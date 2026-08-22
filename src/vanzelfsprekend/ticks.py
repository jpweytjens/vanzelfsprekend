"""Tick-mark direction: in, out, or gone."""

import matplotlib as mpl
from matplotlib.axes import Axes
from matplotlib.axis import Axis

from vanzelfsprekend.hook import ensure_state


def tick_direction(ax: Axes, direction: str = "out") -> Axes:
    """Point the tick marks `direction`: `'in'`, `'out'`, or `'none'`.

    `'none'` keeps the tick labels and removes the marks (zero length).
    The prior direction and lengths are snapshotted on the first call so
    `restore` can undo the change; later calls toggle freely without
    overwriting the snapshot.

    Returns
    -------
    matplotlib.axes.Axes
        The same axes, for chaining.
    """
    if direction not in ("in", "out", "none"):
        raise ValueError(f"direction must be 'in', 'out' or 'none', got {direction!r}")
    state = ensure_state(ax)
    if "ticks" not in state:
        state["ticks"] = {
            "snapshot": {
                "x": _tick_geometry(ax.xaxis),
                "y": _tick_geometry(ax.yaxis),
            }
        }
    snap = state["ticks"]["snapshot"]
    if direction == "none":
        ax.tick_params(which="both", length=0)
    else:
        for key in ("x", "y"):
            prior = snap[key]
            ax.tick_params(
                axis=key,
                which="major",
                direction=direction,
                length=prior["major_length"],
            )
            ax.tick_params(
                axis=key,
                which="minor",
                direction=direction,
                length=prior["minor_length"],
            )
    return ax


def _tick_geometry(axis: Axis) -> dict:
    key = axis.axis_name
    major = axis.get_tick_params(which="major")
    minor = axis.get_tick_params(which="minor")
    return {
        "direction": major.get("direction", mpl.rcParams[f"{key}tick.direction"]),
        "major_length": major.get("length", mpl.rcParams[f"{key}tick.major.size"]),
        "minor_length": minor.get("length", mpl.rcParams[f"{key}tick.minor.size"]),
    }
