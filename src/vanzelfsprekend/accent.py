"""Pull chosen feature ticks forward: colour their labels; the antonym of `mute`."""

from collections.abc import Sequence

import numpy as np
from matplotlib.axes import Axes
from matplotlib.axis import Axis
from matplotlib.colors import to_rgba
from matplotlib.typing import ColorType

from vanzelfsprekend.hook import add_applier, ensure_state
from vanzelfsprekend.palettes import ACCENT_INK


def _feature_names(axis: Axis) -> dict[float, tuple[str, ...]]:
    """Read the installed major locator's `position -> names` map, or empty."""
    return getattr(axis.get_major_locator(), "feature_names", {})


def _accent_axes(ax: Axes, axis: str | None) -> list[Axis]:
    """Return the axes to act on: the named `"x"`/`"y"`, else every axis with names."""
    if axis == "x":
        return [ax.xaxis]
    if axis == "y":
        return [ax.yaxis]
    if axis is not None:
        raise ValueError(f"axis must be 'x', 'y' or None, got {axis!r}")
    named: list[Axis] = [a for a in (ax.xaxis, ax.yaxis) if _feature_names(a)]
    if not named:
        raise ValueError(
            "no named features on either axis; install an AugmentedLocator or a "
            "named feature locator, or pass at= with explicit positions and axis="
        )
    return named


def _selected_positions(
    axis: Axis, at: Sequence[str] | Sequence[float] | None
) -> set[float]:
    """Feature positions to accent (all named by default). Filled out in Task 7."""
    return set(_feature_names(axis))


def _current_labelcolor(axis: Axis) -> str:
    params = axis.get_tick_params(which="major")
    return params.get("labelcolor", params.get("color", "black"))


def accent(
    ax: Axes,
    at: Sequence[str] | Sequence[float] | None = None,
    color: ColorType | None = None,
    axis: str | None = None,
    only_features: bool = False,
    label: str = "value",
) -> Axes:
    """Emphasise named feature ticks by colouring their labels.

    Reads the `position -> names` map off the installed major locator
    (an `AugmentedLocator` forwards its `extra`'s map; a named feature
    locator exposes its own) and colours those ticks' labels with
    `color` (default `palettes.ACCENT_INK`). The tick marks are left in
    the frame colour. Re-applies on every draw, so the accent survives
    resize and re-ticking; `restore` reverts it.

    Returns
    -------
    matplotlib.axes.Axes
        The same axes, for chaining.
    """
    axes = _accent_axes(ax, axis)
    resolved = ACCENT_INK if color is None else color
    state = ensure_state(ax)
    if "accent" not in state:
        state["accent"] = {"axes": {}}
    for target in axes:
        key = target.axis_name  # ty: ignore[unresolved-attribute]
        if key not in state["accent"]["axes"]:
            state["accent"]["axes"][key] = {
                "formatter": target.get_major_formatter(),
                "labelcolor": _current_labelcolor(target),
            }
        positions = _selected_positions(target, at)
        target._vzs_accent = {  # ty: ignore[unresolved-attribute]
            "colors": dict.fromkeys(positions, resolved),
            "positions": positions,
        }
    add_applier(ax, "accent", _apply)
    _apply(ax)
    return ax


def _apply(ax: Axes) -> bool:
    """Colour the feature-tick labels on each accented axis. Runs on every draw."""
    changed = False
    for axis in (ax.xaxis, ax.yaxis):
        spec = getattr(axis, "_vzs_accent", None)
        if spec is None:
            continue
        for loc, tick in zip(
            axis.get_majorticklocs(), axis.get_major_ticks(), strict=False
        ):
            colour = next(
                (c for p, c in spec["colors"].items() if np.isclose(loc, p)), None
            )
            if colour is not None and to_rgba(tick.label1.get_color()) != to_rgba(
                colour
            ):
                tick.label1.set_color(colour)
                changed = True
    return changed
