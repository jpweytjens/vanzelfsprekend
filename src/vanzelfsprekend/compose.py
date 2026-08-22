"""The apply composer, teardown, and axes-method registration."""

from collections.abc import Sequence

import matplotlib as mpl
from matplotlib.axes import Axes

from vanzelfsprekend import palettes
from vanzelfsprekend.frame import range_frame
from vanzelfsprekend.hook import clear_state, disconnect, get_state
from vanzelfsprekend.mute import mute


def apply(
    ax: Axes,
    frame: str = "nice",
    n: int = 5,
    offset: float | None = None,
    nice_numbers: Sequence[float] | None = None,
    weights: dict[str, float] | None = None,
) -> Axes:
    """Apply vanzelfsprekend's default treatment to `ax`.

    The top-level entry point. Today it applies `range_frame` with good
    defaults; it is the seam where later styling and mark helpers will be
    bundled. Takes the same arguments as `range_frame`. It also greys the
    axis furniture and installs the ink-first Tol colour cycle. A custom
    per-axes cycle set before `apply` is restored to the rc default, not
    recovered.

    Returns
    -------
    matplotlib.axes.Axes
        The same axes, for chaining.
    """
    range_frame(
        ax, frame=frame, n=n, offset=offset, nice_numbers=nice_numbers, weights=weights
    )
    mute(ax)
    state = get_state(ax)
    if "cycle" not in state:
        state["cycle"] = {"snapshot": mpl.rcParams["axes.prop_cycle"]}
    ax.set_prop_cycle(color=palettes.CYCLE)
    return ax


def restore(ax: Axes) -> None:
    """Remove vanzelfsprekend's treatment from `ax`, restoring its prior state.

    Disconnects the draw hook and restores exactly the properties vanzelfsprekend
    changed — the original locators, spine visibility and positions,
    label alignment, furniture colours, and the colour cycle — from the
    snapshot taken at first application. A no-op on an axes vanzelfsprekend
    never touched.
    """
    state = get_state(ax)
    if state is None:
        return
    disconnect(ax)

    frame_state = state.get("frame")
    if frame_state is not None:
        snap = frame_state["snapshot"]
        ax.xaxis.set_major_locator(snap["locators"]["x"])
        ax.yaxis.set_major_locator(snap["locators"]["y"])
        ax.spines["top"].set_visible(snap["top_visible"])
        ax.spines["right"].set_visible(snap["right_visible"])
        ax.spines["left"].set_position(snap["left_position"])
        ax.spines["bottom"].set_position(snap["bottom_position"])
        ax.spines["left"].set_bounds(None, None)
        ax.spines["bottom"].set_bounds(None, None)

    labels_state = state.get("labels")
    if labels_state is not None:
        for axis, key in ((ax.xaxis, "x"), (ax.yaxis, "y")):
            props = labels_state["snapshot"][key]
            axis.label.set_horizontalalignment(props["ha"])
            axis.label.set_verticalalignment(props["va"])
            axis.label.set_rotation(props["rotation"])
            axis.label.set_position(props["position"])

    mute_state = state.get("mute")
    if mute_state is not None:
        snap = mute_state["snapshot"]
        for name, prior in snap["spines"].items():
            ax.spines[name].set_edgecolor(prior["color"])
            ax.spines[name].set_linewidth(prior["width"])
        for axis, key in ((ax.xaxis, "x"), (ax.yaxis, "y")):
            prior = snap[key]
            if prior["tick"] is not None:
                ax.tick_params(
                    axis=key,
                    which="both",
                    color=prior["tick"],
                    width=prior["tick_width"],
                    labelcolor=prior["ticklabel"],
                )
            else:
                rc_color = mpl.rcParams[f"{key}tick.color"]
                rc_labelcolor = mpl.rcParams[f"{key}tick.labelcolor"]
                if rc_labelcolor == "inherit":
                    rc_labelcolor = rc_color
                ax.tick_params(
                    axis=key,
                    which="both",
                    color=rc_color,
                    width=mpl.rcParams[f"{key}tick.major.width"],
                    labelcolor=rc_labelcolor,
                )
            axis.label.set_color(prior["label"])

    ticks_state = state.get("ticks")
    if ticks_state is not None:
        for key in ("x", "y"):
            prior = ticks_state["snapshot"][key]
            ax.tick_params(
                axis=key,
                which="major",
                direction=prior["direction"],
                length=prior["major_length"],
            )
            ax.tick_params(
                axis=key,
                which="minor",
                direction=prior["direction"],
                length=prior["minor_length"],
            )

    cycle_state = state.get("cycle")
    if cycle_state is not None:
        ax.set_prop_cycle(cycle_state["snapshot"])

    clear_state(ax)
    ax.figure.canvas.draw_idle()


def register() -> None:
    """Add `apply` and `restore` methods to `matplotlib.axes.Axes`.

    Opt-in monkeypatching: after calling this once, `ax.apply(...)` and
    `ax.restore()` delegate to the functions. Calling it again is a no-op.
    """
    from matplotlib.axes import Axes

    if getattr(Axes, "apply", None) is not None:
        return

    def _apply_method(
        self: Axes,
        frame: str = "nice",
        n: int = 5,
        offset: float | None = None,
        nice_numbers: Sequence[float] | None = None,
        weights: dict[str, float] | None = None,
    ) -> Axes:
        return apply(
            self,
            frame=frame,
            n=n,
            offset=offset,
            nice_numbers=nice_numbers,
            weights=weights,
        )

    def _restore_method(self: Axes) -> None:
        return restore(self)

    Axes.apply = _apply_method
    Axes.restore = _restore_method


def unregister() -> None:
    """Remove the `apply` and `restore` methods if present.

    Re-entrant: a no-op when they were never registered.
    """
    from matplotlib.axes import Axes

    for name in ("apply", "restore"):
        if getattr(Axes, name, None) is not None:
            delattr(Axes, name)
