"""Scale groups: the panels whose data union feeds one axis's ticks and spine.

`distill` reads a group from matplotlib's share groupers; `small_multiples`
reads one from the gridspec and `compare`. Both hand their groups to this
module, which unions the members' data so the frame and the locators span
it. Nothing here is public.
"""

import warnings
from collections.abc import Mapping, Sequence
from functools import partial
from typing import cast

import matplotlib as mpl
import numpy as np
from matplotlib.axes import Axes
from matplotlib.ticker import Locator

from vanzelfsprekend import palettes
from vanzelfsprekend.frame import (
    AxisKind,
    axis_kind,
    install_frame,
    parse_frame_args,
    snapshot_frame,
)
from vanzelfsprekend.hook import add_applier, ensure_state, get_state, run_appliers
from vanzelfsprekend.labels import _apply_date_offset
from vanzelfsprekend.locator import DateBreaksLocator, LogBreaksLocator, TalbotLocator
from vanzelfsprekend.mute import mute
from vanzelfsprekend.ticklabels import _apply_tick_labels

BreaksLocator = TalbotLocator | LogBreaksLocator | DateBreaksLocator


def data_union(members: Sequence[Axes], name: str) -> tuple[float, float] | None:
    """Union of the members' data intervals along `name` (`'x'` or `'y'`).

    Log axes substitute `minpos` for a nonpositive minimum, mirroring
    the locators' own reading. Members with no finite data are skipped;
    returns `None` when none remain or the union is degenerate.
    """
    lo, hi = np.inf, -np.inf
    for ax in members:
        axis = ax.xaxis if name == "x" else ax.yaxis
        dmin, dmax = axis.get_data_interval()
        if axis.get_scale() == "log" and dmin <= 0:
            dmin = axis.get_minpos()
        if not np.isfinite([dmin, dmax]).all():
            continue
        lo, hi = min(lo, dmin), max(hi, dmax)
    if not np.isfinite([lo, hi]).all() or lo == hi:
        return None
    return (lo, hi)


def view_union(members: Sequence[Axes], name: str) -> tuple[float, float] | None:
    """Union of the members' view intervals along `name` (`'x'` or `'y'`).

    Each member's interval is sorted first so an inverted axis doesn't
    poison the union. Returns `None` when the result would be empty or
    degenerate.
    """
    lo, hi = np.inf, -np.inf
    for ax in members:
        axis = ax.xaxis if name == "x" else ax.yaxis
        vmin, vmax = sorted(axis.get_view_interval())
        lo, hi = min(lo, vmin), max(hi, vmax)
    if not np.isfinite([lo, hi]).all() or lo == hi:
        return None
    return (lo, hi)


class GroupLocator(Locator):
    """Delegate tick placement to `inner`, fed the group's data union.

    Installed on a panel's axis in place of the locator the frame chose,
    so ticks are recomputed on every draw from the union of the group
    members' data instead of the one panel's. Everything else defers to
    `inner`, whose own axis binding is left in place so a formatter
    constructed around it (`ConciseDateFormatter`) keeps working. View
    limits are computed over the union as well, so a loose group
    autoscales to the union's covering breaks on the first draw.
    """

    def __init__(
        self, inner: BreaksLocator, members: Sequence[Axes], name: str
    ) -> None:
        self._inner = inner
        self._members = members
        self._name = name

    def __call__(self) -> np.ndarray:  # ty: ignore[invalid-method-override]
        """Compute tick positions from the union of the group's data."""
        union = data_union(self._members, self._name)
        if union is None:
            return np.asarray(self._inner())
        return np.asarray(self._inner.tick_values(*union))

    def tick_values(self, vmin: float, vmax: float) -> np.ndarray:  # ty: ignore
        """Delegate tick value computation to the inner locator."""
        return np.asarray(self._inner.tick_values(vmin, vmax))

    def nonsingular(  # ty: ignore[invalid-method-override]
        self, vmin: float, vmax: float
    ) -> tuple[float, float]:
        """Delegate singularity handling to the inner locator."""
        return self._inner.nonsingular(vmin, vmax)

    def view_limits(self, vmin: float, vmax: float) -> tuple[float, float]:
        """View limits with the loose span covering the group's data union."""
        return self._inner.view_limits_over(
            vmin, vmax, data_union(self._members, self._name)
        )


def axis_kinds(members: Sequence[Axes], name: str) -> set[AxisKind]:
    """Kinds reported along `name` by the members that hold data.

    A member with no finite data has no converter and no say, so it
    follows the rest. When no member holds data, every member is heard,
    which is one plain kind: shared axes share their scale, and no data
    means no converter.
    """
    axes = [ax.xaxis if name == "x" else ax.yaxis for ax in members]
    with_data = [axis for axis in axes if np.isfinite(axis.get_data_interval()).all()]
    return {axis_kind(axis) for axis in (with_data or axes)}


def treat(
    members: Mapping[Axes, Mapping[str, Sequence[Axes] | None]],
    *,
    frame: str | tuple[str, str] = "nice",
    n: int = 5,
    offset: float | tuple[float | None, float | None] | None = None,
    nice_numbers: Sequence[float] | None = None,
    weights: dict[str, float] | None = None,
) -> None:
    """Distill every key of `members` as one unit.

    `members[ax][name]` lists the axes whose data feed `ax`'s `name`
    axis (`ax` itself for a lone axes), or is `None` to leave that axis
    alone. Snapshots are taken for every member before any member is
    modified, so axes that share a `Ticker` record their true original
    once; then each member gets the frame for its group's kind, its
    locators wrapped to read the group's data union, the spine ended at
    that union, the muted furniture, the neutral ink cycle, and the
    appliers. Once every member has its locator installed, each is
    autoscaled once so a loose frame lands edge to edge. The keys
    together are what `restore` undoes.
    """
    mode, offsets = parse_frame_args(frame, offset)
    unit = tuple(members)
    for ax in unit:
        snapshot_frame(ax)
        state = ensure_state(ax)
        if "group" not in state:
            group_state: dict = {
                "snapshot": {
                    "limits": {"x": ax.get_xlim(), "y": ax.get_ylim()},
                    "autoscale": {
                        "x": ax.get_autoscalex_on(),
                        "y": ax.get_autoscaley_on(),
                    },
                }
            }
            state["group"] = group_state
        state["group"]["unit"] = unit
        state["group"]["members"] = {
            name: list(group)
            for name, group in members[ax].items()
            if group is not None
        }

    kind_of: dict[tuple[str, frozenset[int]], AxisKind | None] = {}
    for ax in unit:
        kinds: dict[str, AxisKind | None] = {}
        for name in ("x", "y"):
            group = members[ax].get(name)
            if group is None:
                kinds[name] = None
                continue
            key = (name, frozenset(id(member) for member in group))
            if key not in kind_of:
                found = axis_kinds(group, name)
                kind_of[key] = found.pop() if len(found) == 1 else None
            kinds[name] = kind_of[key]
        install_frame(
            ax,
            mode,
            offsets,
            n=n,
            nice_numbers=nice_numbers,
            weights=weights,
            kinds=kinds,
        )
        state = ensure_state(ax)
        frame_state = state["frame"]
        intervals = frame_state.setdefault("intervals", {})
        for name in frame_state["active"]:
            # The recorded list, not `members[ax][name]`: one authority for
            # the group, shared by the locator, the applier and restore.
            group = state["group"]["members"][name]
            axis = ax.xaxis if name == "x" else ax.yaxis
            inner = cast("BreaksLocator", axis.get_major_locator())
            axis.set_major_locator(GroupLocator(inner, group, name))
            intervals[name] = partial(data_union, group, name)
        mute(ax)
        if "cycle" not in state:
            state["cycle"] = {"snapshot": mpl.rcParams["axes.prop_cycle"]}
        ax.set_prop_cycle(palettes.cycle("ink"))
        state.setdefault("tick_labels", {"applied": {"x": {}, "y": {}}})
        add_applier(ax, "tick_labels", _apply_tick_labels)
        add_applier(ax, "date_offset", _apply_date_offset)
        add_applier(ax, "limits", apply_limits)
    for ax in unit:
        ax.autoscale_view()
    for ax in unit:
        run_appliers(ax)


def apply_limits(ax: Axes) -> bool:
    """Pin each axis of `ax` to its group's view union; the sole writer of limits.

    A group of one is left alone, so a lone axes keeps an inverted axis
    or a hand-set view. Groups of two or more converge onto one
    ascending scale on the first draw, and this applier then finds
    nothing to change.
    """
    state = get_state(ax)
    if state is None or "group" not in state:
        return False
    changed = False
    for name, group in state["group"]["members"].items():
        if len(group) < 2:
            continue
        union = view_union(group, name)
        if union is None:
            continue
        axis = ax.xaxis if name == "x" else ax.yaxis
        if tuple(axis.get_view_interval()) != union:
            (ax.set_xlim if name == "x" else ax.set_ylim)(union)
            changed = True
    return changed


def share_groups(ax: Axes) -> dict[Axes, dict[str, list[Axes] | None]]:
    """Form `ax`'s scale groups from matplotlib's sharing.

    The unit is the connected component over the x and y share groupers
    starting at `ax`; on a grid built with `sharex="col", sharey="row"`
    that is every panel. Each member's x group is its x siblings within
    the unit, likewise y, so a column shares x while a row shares y. A
    lone axes is a unit of one.

    When the data-holding members of one group disagree on kind (dates
    beside plain numbers), a common scale means nothing: warn once and
    set that axis to `None` for every member, which leaves it untouched.
    """
    unit = _component(ax)
    unit_ids = {id(member) for member in unit}
    groups: dict[Axes, dict[str, list[Axes] | None]] = {}
    for member in unit:
        per_axis: dict[str, list[Axes] | None] = {}
        for name, grouper in (
            ("x", member.get_shared_x_axes()),
            ("y", member.get_shared_y_axes()),
        ):
            sibling_ids = {id(s) for s in grouper.get_siblings(member)}
            per_axis[name] = [
                s for s in unit if id(s) in sibling_ids and id(s) in unit_ids
            ]
        groups[member] = per_axis
    agree: dict[tuple[str, frozenset[int]], bool] = {}
    for per_axis in groups.values():
        for name in ("x", "y"):
            siblings = per_axis[name]
            if siblings is None:
                continue
            key = (name, frozenset(id(s) for s in siblings))
            if key not in agree:
                agree[key] = len(axis_kinds(siblings, name)) <= 1
                if not agree[key]:
                    warnings.warn(
                        f"vanzelfsprekend: shared {name}-axis mixes panels of "
                        "different scale or date-ness; a common scale means "
                        "nothing, leaving it untouched",
                        stacklevel=3,
                    )
            if not agree[key]:
                per_axis[name] = None
    return groups


def _component(ax: Axes) -> list[Axes]:
    """Every axes reachable from `ax` through x or y sharing, `ax` first."""
    unit = [ax]
    seen = {id(ax)}
    queue = [ax]
    while queue:
        current = queue.pop()
        for grouper in (current.get_shared_x_axes(), current.get_shared_y_axes()):
            for sibling in grouper.get_siblings(current):
                if id(sibling) not in seen:
                    seen.add(id(sibling))
                    unit.append(sibling)
                    queue.append(sibling)
    return unit
