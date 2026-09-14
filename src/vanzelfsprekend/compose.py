"""The `apply` door, the group-aware `range_frame`, and teardown.

`register` puts the `ax.vzs` accessor on `Axes`; `unregister` takes it off.
"""

from collections.abc import Callable, Sequence
from typing import Any, Literal

from matplotlib.artist import Artist
from matplotlib.axes import Axes
from matplotlib.text import Annotation, Text
from matplotlib.typing import ColorType

from vanzelfsprekend import placement
from vanzelfsprekend.direct import Side, label
from vanzelfsprekend.frame import FrameMode, skip_if_not_rectilinear
from vanzelfsprekend.group import frame_unit, share_groups
from vanzelfsprekend.hook import clear_state, disconnect, ensure_state, get_state
from vanzelfsprekend.labels import xlabel, ylabel
from vanzelfsprekend.lines import line_labels
from vanzelfsprekend.locator import SPACING
from vanzelfsprekend.multiples import _teardown_grid
from vanzelfsprekend.mute import LINE_WIDTH, mute
from vanzelfsprekend.palettes import LINE_INK, TEXT_INK
from vanzelfsprekend.secondary import secondary_frame
from vanzelfsprekend.ticks import _rc, tick_direction


def _frame(
    ax: Axes,
    *,
    frame: FrameMode | tuple[FrameMode, FrameMode],
    spacing: float | tuple[float, float],
    n: int | None,
    offset: float | tuple[float | None, float | None] | None,
    nice_numbers: Sequence[float] | None,
    weights: dict[str, float] | None,
) -> None:
    """Frame `ax` and the panels that share its scales as one unit.

    A unit already framed is framed again with the new settings; a new
    one is read from matplotlib's share groupers. Both public callers
    sit one frame above this one, so the depths below count out to their
    caller from each warn site: four frames for the warnings
    `share_groups` raises, five for those `install_frame` raises one
    call deeper.
    """
    state = get_state(ax)
    recorded = state["group"]["groups"] if state and "group" in state else None
    frame_unit(
        share_groups(ax, stacklevel=4) if recorded is None else recorded,
        frame=frame,
        spacing=spacing,
        n=n,
        offset=offset,
        nice_numbers=nice_numbers,
        weights=weights,
        stacklevel=5,
    )


def range_frame(
    ax: Axes,
    frame: FrameMode | tuple[FrameMode, FrameMode] = "nice",
    spacing: float | tuple[float, float] = SPACING,
    n: int | None = None,
    offset: float | tuple[float | None, float | None] | None = None,
    nice_numbers: Sequence[float] | None = None,
    weights: dict[str, float] | None = None,
) -> Axes:
    """Turn `ax` into a range frame.

    Installs `TalbotLocator` (linear axes), `LogBreaksLocator` (log
    axes), or `DateBreaksLocator` plus a `ConciseDateFormatter` (date
    axes) on both axes, hiding minor ticks on log axes, hides the top
    and right spines, and keeps the left and bottom spine bounds glued
    to the data on every draw. Where tick labels crowd, they drift
    apart just enough to stay readable, keeping their order; the tick
    marks stay exactly at their values. The ink is left alone: the
    spines keep their colour and the axes its colour cycle, which is
    what `mute` changes. Safe to call repeatedly; later calls update
    the settings instead of stacking hooks.

    A locator you set on an axis before calling `range_frame` is kept,
    not overwritten, so ticks and frame compose in either order; the
    locator-shaping arguments below (`spacing`, `n`, `nice_numbers`,
    `weights`) then have nothing to configure and are ignored on that
    axis. Panels framed as a group (shared axes, `small_multiples`) are
    the exception: the shared scale is computed here, so a locator set
    on a grouped axis is replaced.

    Panels that share an axis (`sharex`, `sharey`, `ax.sharex(other)`)
    are framed together, whichever one you pass: each shared axis is
    ticked and framed from the union of the panels' data, so the panels
    stay comparable and every tick lands on a spine. `restore` undoes
    them together, and a later `range_frame` on any of them updates
    them all. A twin made with `twinx` or `twiny` is left out with a
    warning and keeps its box. `small_multiples` does the same for a
    grid, with the inner furniture hidden.

    Parameters
    ----------
    ax : matplotlib.axes.Axes
        The axes to modify, in place.
    frame : {'nice', 'data', 'loose'} or tuple of two of them
        `'nice'` ends the spines at the outermost ticks, `'data'` at
        the exact data minimum and maximum. `'loose'` ends the spines
        at nice numbers bounding the data (frame may extend up to one
        tick step beyond the data). A tuple `(x_mode, y_mode)` sets
        the bottom and left spine independently, and either entry may
        itself be a pair `(low, high)` setting that spine's two ends
        on their own: `(("loose", "data"), "nice")` runs the bottom
        spine from the tick below the data to the last observation.
        All three read the data cut back to the view, so a view pinned
        inside the data with `set_xlim` crops the frame to the data on
        screen, and a view wider than the data changes nothing.
    spacing : float or tuple of two floats
        The gap to aim for between ticks, in tick-label heights, so the
        number of ticks follows the axis's length and the labels' size:
        a small panel gets few, a poster's large labels thin them out.
        A tuple `(x_spacing, y_spacing)` sets the axes independently;
        the default `(7, 4)` is 70 pt and 40 pt at 10 pt labels, about
        2.5 cm and 1.4 cm, since an x label is three to five heights
        wide along its axis and a y label one. Halving the spacing
        doubles the ticks.
    n : int, optional
        The number of ticks to aim for per axis, overriding `spacing`.
    offset : float or tuple of (float or None), optional
        Outward displacement of the left and bottom spines, in points.
        A single number moves both spines; a tuple `(x_offset,
        y_offset)` moves the bottom and left spine independently, like
        `frame`. `None` (the whole argument, or either tuple element)
        resolves to 8 for a spine with a `'loose'` end and 0 otherwise.
    nice_numbers : sequence of float, optional
        Advanced pass-through to `TalbotLocator`; see there for details.
        Applies to linear axes only; ignored on log and date axes.
    weights : dict, optional
        Advanced pass-through to `TalbotLocator`; see there for details.
        Applies to linear axes only; ignored on log and date axes.

    Returns
    -------
    matplotlib.axes.Axes
        The same axes, for chaining.
    """
    if skip_if_not_rectilinear(ax, stacklevel=3):
        return ax
    _frame(
        ax,
        frame=frame,
        spacing=spacing,
        n=n,
        offset=offset,
        nice_numbers=nice_numbers,
        weights=weights,
    )
    return ax


def apply(
    ax: Axes,
    frame: FrameMode | tuple[FrameMode, FrameMode] = "nice",
    spacing: float | tuple[float, float] = SPACING,
    n: int | None = None,
    offset: float | tuple[float | None, float | None] | None = None,
    nice_numbers: Sequence[float] | None = None,
    weights: dict[str, float] | None = None,
) -> Axes:
    """Apply vanzelfsprekend to `ax`: `range_frame`, then `mute`.

    Takes `range_frame`'s arguments and forwards them. `restore` undoes
    both steps.

    The ink follows the frame: every panel framed as one unit with `ax`
    is muted too, not just `ax`.

    Returns
    -------
    matplotlib.axes.Axes
        The same axes, for chaining.
    """
    if skip_if_not_rectilinear(ax, stacklevel=3):
        return ax
    _frame(
        ax,
        frame=frame,
        spacing=spacing,
        n=n,
        offset=offset,
        nice_numbers=nice_numbers,
        weights=weights,
    )
    for member in ensure_state(ax)["group"]["unit"]:
        mute(member)
    return ax


def restore(ax: Axes) -> None:
    """Remove vanzelfsprekend from `ax` and every axes framed with it.

    Panels that were framed together, because they share an axis or
    were passed to `small_multiples`, are restored together: the shared
    scale cannot survive losing a member. Disconnects each draw hook and
    restores exactly the properties vanzelfsprekend changed (the original
    locators, spine visibility, positions and bounds, label alignment,
    furniture colours, view limits and the colour cycle) from the
    snapshots taken at first application. A no-op on an axes
    vanzelfsprekend never touched.
    """
    state = get_state(ax)
    if state is None:
        return
    unit = state.get("group", {}).get("unit", (ax,))
    autoscale = {}
    for member in unit:
        member_state = get_state(member)
        if member_state is None:
            continue
        group_state = member_state.get("group")
        if group_state is not None:
            autoscale[member] = {
                name: group_state["snapshot"]["autoscale"][name]
                for name in group_state["members"]
            }
        _restore_member(member)
    # Second pass: a shared `set_xlim`/`set_ylim` disables autoscale on
    # every sibling, so the flags only land once every limit has settled.
    for member, flags in autoscale.items():
        for name, on in flags.items():
            (member.set_autoscalex_on if name == "x" else member.set_autoscaley_on)(on)


def _restore_member(ax: Axes) -> None:
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
            if key in frame_state["formatted"]:
                axis.set_major_formatter(snap["formatters"][key])
        ax.spines["top"].set_visible(snap["top_visible"])
        ax.spines["right"].set_visible(snap["right_visible"])
        ax.spines["left"].set_position(snap["left_position"])
        ax.spines["bottom"].set_position(snap["bottom_position"])
        for side in ("bottom", "left"):
            # `Spine.set_bounds(None, None)` keeps the old bounds rather
            # than unsetting them, so a pristine `None` needs the attribute.
            ax.spines[side]._bounds = None  # ty: ignore[unresolved-attribute]

    group_state = state.get("group")
    if group_state is not None:
        for name in group_state["members"]:
            limits = group_state["snapshot"]["limits"][name]
            (ax.set_xlim if name == "x" else ax.set_ylim)(limits)

    multiples_state = state.get("multiples")
    if multiples_state is not None:
        _teardown_grid(multiples_state["grid"])

    labels_state = state.get("labels")
    if labels_state is not None:
        # Drop the managed above-label text, if `ylabel(place="above")` made one.
        above_text = labels_state.get("ylabel_above_text")
        if above_text is not None:
            above_text.remove()
            labels_state["ylabel_above_text"] = None
        snap = labels_state["snapshot"]
        for axis, key in ((ax.xaxis, "x"), (ax.yaxis, "y")):
            props = snap[key]
            axis.label.set_text(props["text"])
            axis.label.set_horizontalalignment(props["ha"])
            axis.label.set_verticalalignment(props["va"])
            axis.label.set_rotation(props["rotation"])
            axis.label.set_position(props["position"])
        # Restore matplotlib's own perpendicular y-label placement.
        ax.yaxis.set_label_position(snap.get("y_label_position_side", "left"))
        ax.yaxis.label.set_transform(snap["y_label_transform"])
        ax.yaxis._autolabelpos = snap.get("y_autolabelpos", True)  # ty: ignore[unresolved-attribute]

    mute_state = state.get("mute")
    if mute_state is not None:
        snap = mute_state["snapshot"]
        for name, prior in snap["spines"].items():
            ax.spines[name].set_edgecolor(prior["color"])
            ax.spines[name].set_linewidth(prior["width"])
        grid = snap.get("grid")
        if grid is not None:
            for key, axis in (("x", ax.xaxis), ("y", ax.yaxis)):
                axis.grid(grid[key]["major"], which="major")
                axis.grid(grid[key]["minor"], which="minor")
        ticks = snap.get("ticks")
        if ticks is not None:
            ax.tick_params(axis="x", which="major", bottom=ticks["x"])
            ax.tick_params(axis="y", which="major", left=ticks["y"])
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

    direct_state = state.get("direct")
    if direct_state is not None:
        for group in direct_state:
            for text in group["texts"]:
                text.remove()

    date_offset_state = state.get("date_offset")
    if date_offset_state is not None:
        off = ax.xaxis.get_offset_text()
        off.set_transform(date_offset_state["transform"])
        off.set_x(date_offset_state["x"])

    legend_state = state.get("legend")
    if legend_state is not None:
        legend_state["artist"].set_visible(legend_state["visible"])

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

    secondary_state = state.get("secondary")
    if secondary_state is not None:
        for entry in secondary_state:
            entry["secax"].remove()

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
        frame: FrameMode | tuple[FrameMode, FrameMode] = "nice",
        spacing: float | tuple[float, float] = SPACING,
        n: int | None = None,
        offset: float | tuple[float | None, float | None] | None = None,
        nice_numbers: Sequence[float] | None = None,
        weights: dict[str, float] | None = None,
    ) -> Axes:
        """Apply vanzelfsprekend to the axes; see `vanzelfsprekend.apply`."""
        return apply(
            self._ax,
            frame=frame,
            spacing=spacing,
            n=n,
            offset=offset,
            nice_numbers=nice_numbers,
            weights=weights,
        )

    def restore(self) -> None:
        """Put the axes back; see `vanzelfsprekend.restore`."""
        return restore(self._ax)

    def range_frame(
        self,
        frame: FrameMode | tuple[FrameMode, FrameMode] = "nice",
        spacing: float | tuple[float, float] = SPACING,
        n: int | None = None,
        offset: float | tuple[float | None, float | None] | None = None,
        nice_numbers: Sequence[float] | None = None,
        weights: dict[str, float] | None = None,
    ) -> Axes:
        """Turn the axes into a range frame; see `vanzelfsprekend.range_frame`."""
        return range_frame(
            self._ax,
            frame=frame,
            spacing=spacing,
            n=n,
            offset=offset,
            nice_numbers=nice_numbers,
            weights=weights,
        )

    def set_xlabel(
        self, text: str, flush: bool = True, labelpad: float | None = None
    ) -> Text:
        """End-of-spine x-label; see `vanzelfsprekend.xlabel`."""
        return xlabel(self._ax, text, flush=flush, labelpad=labelpad)

    def set_ylabel(
        self, text: str, place: str = "above", labelpad: float | None = None
    ) -> Text:
        """End-of-spine y-label; see `vanzelfsprekend.ylabel`."""
        return ylabel(self._ax, text, place=place, labelpad=labelpad)

    def line_labels(
        self,
        at: Literal["start", "end"] = "end",
        labelcolor: str | ColorType | list[ColorType] = "linecolor",
        pad: float = 4.0,
        gap: float = placement.GAP,
        labels: list[str | None] | None = None,
    ) -> list[Annotation]:
        """Direct labels at the lines' ends; see `vanzelfsprekend.line_labels`."""
        return line_labels(
            self._ax, at=at, labelcolor=labelcolor, pad=pad, gap=gap, labels=labels
        )

    def label(
        self,
        name: str | Artist | Sequence[str | Artist],
        *,
        x: Any | None = None,
        y: Any | None = None,
        side: Side | None = None,
        labelcolor: str | ColorType | list[ColorType] = "linecolor",
        pad: float = 4.0,
        gap: float = placement.GAP,
    ) -> list[Annotation]:
        """Put a label beside a named artist; see `vanzelfsprekend.label`."""
        return label(
            self._ax, name, x=x, y=y, side=side, labelcolor=labelcolor, pad=pad, gap=gap
        )

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

    def secondary_frame(
        self,
        functions: tuple[Callable, Callable],
        where: str = "top",
    ) -> Axes:
        """Add a mirrored second-unit axis; see `vanzelfsprekend.secondary_frame`."""
        return secondary_frame(self._ax, functions, where=where)

    def tick_direction(self, direction: str = "out") -> Axes:
        """Point the tick marks; see `vanzelfsprekend.tick_direction`."""
        return tick_direction(self._ax, direction=direction)


def register() -> None:
    """Add the `vzs` accessor to `matplotlib.axes.Axes`.

    Importing `vanzelfsprekend` calls this once, so `ax.vzs.apply(...)`,
    `ax.vzs.set_xlabel(...)` and the other entry points work straight
    away, each delegating to the module function bound to that axes.
    Calling it again is a no-op; call it to restore the accessor after an
    `unregister()`.
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
