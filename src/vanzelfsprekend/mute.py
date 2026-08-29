"""Grey the axis furniture so the data carries the ink."""

from matplotlib.axes import Axes
from matplotlib.axis import Axis

from vanzelfsprekend.hook import ensure_state
from vanzelfsprekend.palettes import LINE_INK, TEXT_INK

LINE_WIDTH = 0.7


def mute(
    ax: Axes,
    text_ink: str = TEXT_INK,
    line_ink: str = LINE_INK,
    line_width: float = LINE_WIDTH,
) -> Axes:
    """Grey the axis furniture in two tiers: readable text, receding lines.

    Spines and tick marks take `line_ink` at `line_width` points; tick
    labels and axis labels take the darker `text_ink`, since text is
    read while lines are only looked at. Gridlines are turned off —
    they are furniture, not data — and data artists are untouched.
    The prior colours, widths and grid visibility are snapshotted on
    the first call so `restore` can undo the change; later calls update
    the inks without overwriting the snapshot.

    Returns
    -------
    matplotlib.axes.Axes
        The same axes, for chaining.
    """
    state = ensure_state(ax)
    if "mute" not in state:
        state["mute"] = {
            "snapshot": {
                "spines": {
                    name: {
                        "color": spine.get_edgecolor(),
                        "width": spine.get_linewidth(),
                    }
                    for name, spine in ax.spines.items()
                },
                "x": _axis_ink(ax.xaxis),
                "y": _axis_ink(ax.yaxis),
                "grid": {
                    key: {
                        "major": _grid_on(axis, "major"),
                        "minor": _grid_on(axis, "minor"),
                    }
                    for key, axis in (("x", ax.xaxis), ("y", ax.yaxis))
                },
            }
        }
    for spine in ax.spines.values():
        spine.set_edgecolor(line_ink)
        spine.set_linewidth(line_width)
    ax.tick_params(which="both", color=line_ink, width=line_width, labelcolor=text_ink)
    ax.xaxis.label.set_color(text_ink)
    ax.yaxis.label.set_color(text_ink)
    ax.grid(False, which="both")  # gridlines are furniture; the data carries the ink
    return ax


def _grid_on(axis: Axis, which: str) -> bool:
    kw = axis._major_tick_kw if which == "major" else axis._minor_tick_kw  # ty: ignore[unresolved-attribute]
    return bool(kw.get("gridOn", False))


def _axis_ink(axis: Axis) -> dict:
    ticks = axis.get_major_ticks()
    return {
        "tick": ticks[0].tick1line.get_color() if ticks else None,
        "tick_width": ticks[0].tick1line.get_markeredgewidth() if ticks else None,
        "ticklabel": ticks[0].label1.get_color() if ticks else None,
        "label": axis.label.get_color(),
    }
