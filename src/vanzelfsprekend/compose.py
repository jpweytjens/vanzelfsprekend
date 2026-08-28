"""The apply composer, teardown, and the `ax.vzs` accessor registration."""

from collections.abc import Sequence
from typing import Literal

import matplotlib as mpl
from matplotlib.axes import Axes
from matplotlib.text import Annotation, Text
from matplotlib.typing import ColorType

from vanzelfsprekend import palettes, placement
from vanzelfsprekend.frame import range_frame
from vanzelfsprekend.hook import (
    add_applier,
    clear_state,
    disconnect,
    ensure_state,
    get_state,
)
from vanzelfsprekend.labels import xlabel, ylabel
from vanzelfsprekend.lines import line_labels
from vanzelfsprekend.mute import LINE_WIDTH, mute
from vanzelfsprekend.palettes import LINE_INK, TEXT_INK
from vanzelfsprekend.ticklabels import _apply_tick_labels
from vanzelfsprekend.ticks import _rc, tick_direction


def apply(
    ax: Axes,
    frame: str | tuple[str, str] = "nice",
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
    recovered. Where tick labels crowd, they drift apart just enough to
    stay readable, keeping their order; the tick marks stay exactly at
    their values.

    Returns
    -------
    matplotlib.axes.Axes
        The same axes, for chaining.
    """
    range_frame(
        ax, frame=frame, n=n, offset=offset, nice_numbers=nice_numbers, weights=weights
    )
    mute(ax)
    state = ensure_state(ax)
    if "cycle" not in state:
        state["cycle"] = {"snapshot": mpl.rcParams["axes.prop_cycle"]}
    ax.set_prop_cycle(color=palettes.CYCLE)
    state.setdefault("tick_labels", {"applied": {"x": {}, "y": {}}})
    add_applier(ax, "tick_labels", _apply_tick_labels)
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
        ax.xaxis.set_minor_locator(snap["minor_locators"]["x"])
        ax.yaxis.set_minor_locator(snap["minor_locators"]["y"])
        for axis, key in ((ax.xaxis, "x"), (ax.yaxis, "y")):
            if key in snap["formatters"]:
                axis.set_major_formatter(snap["formatters"][key])
        ax.spines["top"].set_visible(snap["top_visible"])
        ax.spines["right"].set_visible(snap["right_visible"])
        ax.spines["left"].set_position(snap["left_position"])
        ax.spines["bottom"].set_position(snap["bottom_position"])
        ax.spines["left"].set_bounds(None, None)
        ax.spines["bottom"].set_bounds(None, None)

    multiples_state = state.get("multiples")
    if multiples_state is not None:
        # Imported here: multiples imports `apply` from this module, so a
        # module-level import would be a cycle. Order matters — the frame
        # block above must write its locators into the fresh unshared
        # ticker before the original shared one is re-attached.
        from vanzelfsprekend.multiples import _reattach_tickers, _teardown_grid

        _teardown_grid(multiples_state["grid"])
        _reattach_tickers(ax, multiples_state["snapshot"])

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
                rc_color = _rc(f"{key}tick.color")
                rc_labelcolor = _rc(f"{key}tick.labelcolor")
                if rc_labelcolor == "inherit":
                    rc_labelcolor = rc_color
                ax.tick_params(
                    axis=key,
                    which="both",
                    color=rc_color,
                    width=_rc(f"{key}tick.major.width"),
                    labelcolor=rc_labelcolor,
                )
            axis.label.set_color(prior["label"])

    tick_state = state.get("tick_labels")
    if tick_state is not None:
        for per_axis in tick_state["applied"].values():
            for text, (original, *_rest) in per_axis.items():
                text.set_transform(original)

    line_labels_state = state.get("line_labels")
    if line_labels_state is not None:
        for side in line_labels_state.values():
            for text in side["texts"]:
                text.remove()

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


class _Accessor:
    """The entry points bound to one axes, reached as `ax.vzs` after `register`.

    Method names mimic matplotlib's where a matching contract exists
    (`set_xlabel`, `set_ylabel`); everything else keeps its module name.
    Each method delegates to the module function with this accessor's axes
    as the first argument.
    """

    def __init__(self, ax: Axes) -> None:
        self._ax = ax

    def apply(
        self,
        frame: str | tuple[str, str] = "nice",
        n: int = 5,
        offset: float | None = None,
        nice_numbers: Sequence[float] | None = None,
        weights: dict[str, float] | None = None,
    ) -> Axes:
        """Apply vanzelfsprekend's default treatment; see `vanzelfsprekend.apply`."""
        return apply(
            self._ax,
            frame=frame,
            n=n,
            offset=offset,
            nice_numbers=nice_numbers,
            weights=weights,
        )

    def restore(self) -> None:
        """Remove the treatment; see `vanzelfsprekend.restore`."""
        return restore(self._ax)

    def range_frame(
        self,
        frame: str | tuple[str, str] = "nice",
        n: int = 5,
        offset: float | None = None,
        nice_numbers: Sequence[float] | None = None,
        weights: dict[str, float] | None = None,
    ) -> Axes:
        """Draw the range frame with every knob; see `vanzelfsprekend.range_frame`."""
        return range_frame(
            self._ax,
            frame=frame,
            n=n,
            offset=offset,
            nice_numbers=nice_numbers,
            weights=weights,
        )

    def set_xlabel(self, text: str, labelpad: float | None = None) -> Text:
        """End-of-spine x-label; see `vanzelfsprekend.xlabel`."""
        return xlabel(self._ax, text, labelpad=labelpad)

    def set_ylabel(
        self, text: str, flush: bool = False, labelpad: float | None = None
    ) -> Text:
        """End-of-spine y-label; see `vanzelfsprekend.ylabel`."""
        return ylabel(self._ax, text, flush=flush, labelpad=labelpad)

    def line_labels(
        self,
        at: Literal["start", "end"] = "end",
        labelcolor: str | ColorType | list[ColorType] = "linecolor",
        pad: float = 4.0,
        gap: float = placement.GAP,
    ) -> list[Annotation]:
        """Direct labels at the lines' ends; see `vanzelfsprekend.line_labels`."""
        return line_labels(self._ax, at=at, labelcolor=labelcolor, pad=pad, gap=gap)

    def mute(
        self,
        text_ink: str = TEXT_INK,
        line_ink: str = LINE_INK,
        line_width: float = LINE_WIDTH,
    ) -> Axes:
        """Grey the axis furniture; see `vanzelfsprekend.mute`."""
        return mute(
            self._ax, text_ink=text_ink, line_ink=line_ink, line_width=line_width
        )

    def tick_direction(self, direction: str = "out") -> Axes:
        """Point the tick marks; see `vanzelfsprekend.tick_direction`."""
        return tick_direction(self._ax, direction=direction)


def register() -> None:
    """Add the `vzs` accessor to `matplotlib.axes.Axes`.

    Opt-in monkeypatching of a single attribute: after calling this once,
    `ax.vzs.apply(...)`, `ax.vzs.set_xlabel(...)` and the other entry
    points delegate to the module functions bound to that axes. Calling
    it again is a no-op.
    """
    if getattr(Axes, "vzs", None) is not None:
        return

    Axes.vzs = property(_Accessor)  # ty: ignore[unresolved-attribute]


def unregister() -> None:
    """Remove the `vzs` accessor if present.

    Re-entrant: a no-op when it was never registered.
    """
    if getattr(Axes, "vzs", None) is not None:
        delattr(Axes, "vzs")
