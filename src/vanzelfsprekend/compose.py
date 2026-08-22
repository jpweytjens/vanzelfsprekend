"""The apply composer, teardown, and axes-method registration."""

from collections.abc import Sequence

from matplotlib.axes import Axes

from vanzelfsprekend.frame import range_frame
from vanzelfsprekend.hook import clear_state, disconnect, get_state


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
    bundled. Takes the same arguments as `range_frame`.

    Returns
    -------
    matplotlib.axes.Axes
        The same axes, for chaining.
    """
    return range_frame(
        ax, frame=frame, n=n, offset=offset, nice_numbers=nice_numbers, weights=weights
    )


def restore(ax: Axes) -> None:
    """Remove vanzelfsprekend's treatment from `ax`, restoring its prior state.

    Disconnects the draw hook and restores exactly the properties vanzelfsprekend
    changed — the original locators, spine visibility and positions, and
    label alignment — from the snapshot taken at first application. A no-op
    on an axes vanzelfsprekend never touched.
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
