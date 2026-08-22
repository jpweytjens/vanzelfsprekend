"""Grey the axis furniture so the data carries the ink."""

from matplotlib.axes import Axes
from matplotlib.axis import Axis

from vanzelfsprekend.hook import ensure_state
from vanzelfsprekend.palettes import AXIS_INK


def mute(ax: Axes, ink: str = AXIS_INK) -> Axes:
    """Colour the spines, ticks, tick labels and axis labels `ink`.

    Data artists are untouched. The prior colours are snapshotted on
    the first call so `restore` can undo the change; later calls update
    the ink without overwriting the snapshot.

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
                    name: spine.get_edgecolor() for name, spine in ax.spines.items()
                },
                "x": _axis_ink(ax.xaxis),
                "y": _axis_ink(ax.yaxis),
            }
        }
    for spine in ax.spines.values():
        spine.set_edgecolor(ink)
    ax.tick_params(which="both", colors=ink)
    ax.xaxis.label.set_color(ink)
    ax.yaxis.label.set_color(ink)
    return ax


def _axis_ink(axis: Axis) -> dict:
    ticks = axis.get_major_ticks()
    return {
        "tick": ticks[0].tick1line.get_color() if ticks else None,
        "ticklabel": ticks[0].label1.get_color() if ticks else None,
        "label": axis.label.get_color(),
    }
