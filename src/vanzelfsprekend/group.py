"""Scale groups: the panels whose data union feeds one axis's ticks and spine.

`distill` reads a group from matplotlib's share groupers; `small_multiples`
reads one from the gridspec and `compare`. Both hand their groups to this
module, which unions the members' data so the frame and the locators span
it. Nothing here is exported; `__init__` leaves this module alone.
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
    FrameMode,
    axis_kind,
    install_frame,
    parse_frame_args,
    parse_spacing,
    snapshot_frame,
)
from vanzelfsprekend.hook import add_applier, ensure_state, get_state, run_appliers
from vanzelfsprekend.labels import _apply_date_offset
from vanzelfsprekend.locator import (
    SPACING,
    DateBreaksLocator,
    LogBreaksLocator,
    TalbotLocator,
    visible_interval,
)
from vanzelfsprekend.mute import mute
from vanzelfsprekend.ticklabels import _apply_tick_labels

BreaksLocator = TalbotLocator | LogBreaksLocator | DateBreaksLocator


def data_union(members: Sequence[Axes], name: str) -> tuple[float, float] | None:
    """Union of the members' visible data along `name` (`'x'` or `'y'`).

    Each member's data interval is cut back to its view, mirroring the
    locators' own reading, so a cropped shared axis crops the union.
    Log axes substitute `minpos` for a nonpositive minimum. Members
    with no finite data are skipped; returns `None` when none remain or
    the union is degenerate.
    """
    lo, hi = np.inf, -np.inf
    for ax in members:
        axis = ax.xaxis if name == "x" else ax.yaxis
        dmin, dmax = axis.get_data_interval()
        if axis.get_scale() == "log" and dmin <= 0:
            dmin = axis.get_minpos()
        dmin, dmax = visible_interval(axis, (dmin, dmax))
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
    members' data instead of the one panel's, and aimed at the count
    the narrowest member can carry, so panels of unequal width agree.
    Everything else defers to `inner`, whose own axis binding is left
    in place so a formatter constructed around it
    (`ConciseDateFormatter`) keeps working. View limits are computed
    over the union as well, so a loose group autoscales to the union's
    covering breaks on the first draw.
    """

    def __init__(
        self, inner: BreaksLocator, members: Sequence[Axes], name: str
    ) -> None:
        self._inner = inner
        self._members = members
        self._name = name

    def target(self) -> int:
        """Return the tick count the narrowest member can carry."""
        return min(
            self._inner.target(ax.xaxis if self._name == "x" else ax.yaxis)
            for ax in self._members
        )

    def __call__(self) -> np.ndarray:  # ty: ignore[invalid-method-override]
        """Compute tick positions from the union of the group's data."""
        union = data_union(self._members, self._name)
        if union is None:
            return np.asarray(self._inner())
        return np.asarray(self._inner.tick_values(*union, n=self.target()))

    def tick_values(self, vmin: float, vmax: float) -> np.ndarray:  # ty: ignore
        """Delegate tick value computation to the inner locator."""
        return np.asarray(self._inner.tick_values(vmin, vmax, n=self.target()))

    def nonsingular(  # ty: ignore[invalid-method-override]
        self, vmin: float, vmax: float
    ) -> tuple[float, float]:
        """Delegate singularity handling to the inner locator."""
        return self._inner.nonsingular(vmin, vmax)

    def view_limits(self, vmin: float, vmax: float) -> tuple[float, float]:
        """View limits with the loose span covering the group's data union."""
        return self._inner.view_limits_over(
            vmin, vmax, data_union(self._members, self._name), n=self.target()
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
    frame: FrameMode | tuple[FrameMode, FrameMode] = "nice",
    spacing: float | tuple[float, float] = SPACING,
    n: int | None = None,
    offset: float | tuple[float | None, float | None] | None = None,
    nice_numbers: Sequence[float] | None = None,
    weights: dict[str, float] | None = None,
    stacklevel: int = 4,
) -> None:
    """Distill every key of `members` as one unit.

    `members[ax][name]` lists the axes whose data feed `ax`'s `name`
    axis (`ax` itself for a lone axes), or is `None` to leave that axis
    alone. An axis whose group is one axes is pinned to nothing: it
    takes the frame's own path, exactly as `range_frame` would.
    `state["group"]["members"]` records the pinned axes and nothing
    else, and is the one authority every later step reads. Snapshots
    are taken for every member before any member is modified, so axes
    that share a `Ticker` record their true original once; then each
    member gets the frame for its group's kind, its pinned locators
    wrapped to read the group's data union, the spine ended at that
    union, the muted furniture, the neutral ink cycle, and the
    appliers. Once every member has its locator installed, each member
    with a pinned axis is autoscaled once so a loose frame lands edge
    to edge. `stacklevel` is the caller's depth for the warnings
    `install_frame` raises. The keys together are what `restore` undoes,
    and `members` itself is recorded so a later `distill` on any key
    treats the same unit again with the new settings.
    """
    mode, offsets = parse_frame_args(frame, offset)
    spacings = parse_spacing(spacing)
    unit = tuple(members)
    for ax in unit:
        snapshot_frame(ax)
        state = ensure_state(ax)
        if "group" not in state:
            group_state: dict = {"snapshot": {"limits": {}, "autoscale": {}}}
            state["group"] = group_state
        state["group"]["unit"] = unit
        state["group"]["groups"] = members
        # A group of one pins nothing, so it is left out here and the
        # axis keeps whatever the frame alone would have given it.
        state["group"]["members"] = {
            name: list(group)
            for name, group in members[ax].items()
            if group is not None and len(group) > 1
        }
        snapshot = state["group"]["snapshot"]
        for name in state["group"]["members"]:
            if name in snapshot["limits"]:
                continue
            # Reading a limit settles the pending autoscale, so only a
            # pinned axis, which is autoscaled again below, is read.
            snapshot["limits"][name] = ax.get_xlim() if name == "x" else ax.get_ylim()
            snapshot["autoscale"][name] = (
                ax.get_autoscalex_on() if name == "x" else ax.get_autoscaley_on()
            )

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
            spacing=spacings,
            nice_numbers=nice_numbers,
            weights=weights,
            kinds=kinds,
            stacklevel=stacklevel,
        )
        state = ensure_state(ax)
        frame_state = state["frame"]
        # Rebuilt from the recorded pinned axes, not `members[ax]`: one
        # authority for the group, shared by the locator, the applier
        # and restore, and no override left behind for an unpinned axis.
        intervals: dict[str, partial] = {}
        frame_state["intervals"] = intervals
        for name, group in state["group"]["members"].items():
            if name not in frame_state["active"]:
                continue
            axis = ax.xaxis if name == "x" else ax.yaxis
            inner = cast("BreaksLocator", axis.get_major_locator())
            axis.set_major_locator(GroupLocator(inner, group, name))
            intervals[name] = partial(data_union, group, name)
        mute(ax)
        if "cycle" not in state:
            # The ink cycle replaces only matplotlib's default; a cycle
            # the user chose is theirs, and restore returns whichever
            # was there.
            found = palettes.axes_cycle(ax)
            default = found == list(mpl.rcParams["axes.prop_cycle"])
            state["cycle"] = {
                "snapshot": mpl.rcParams["axes.prop_cycle"]
                if default
                else palettes.cycler_of(found),
                "ink": default,
            }
        if state["cycle"]["ink"]:
            ax.set_prop_cycle(palettes.cycle("ink"))
        state.setdefault("tick_labels", {"applied": {"x": {}, "y": {}}})
        add_applier(ax, "tick_labels", _apply_tick_labels)
        add_applier(ax, "date_offset", _apply_date_offset)
        add_applier(ax, "limits", _apply_limits)
    for ax in unit:
        if ensure_state(ax)["group"]["members"]:
            ax.autoscale_view()
    for ax in unit:
        run_appliers(ax)


def _apply_limits(ax: Axes) -> bool:
    """Pin each pinned axis of `ax` to its group's view union; the sole writer.

    Only the axes recorded in `state["group"]["members"]` are pinned, so
    a lone axes keeps an inverted axis or a hand-set view. A group
    converges onto one ascending scale on the first draw, and this
    applier then finds nothing to change.
    """
    state = get_state(ax)
    if state is None or "group" not in state:
        return False
    changed = False
    for name, group in state["group"]["members"].items():
        union = view_union(group, name)
        if union is None:
            continue
        axis = ax.xaxis if name == "x" else ax.yaxis
        if tuple(axis.get_view_interval()) != union:
            (ax.set_xlim if name == "x" else ax.set_ylim)(union)
            changed = True
    return changed


def _drop_twins(entry: Axes, unit: list[Axes]) -> list[Axes]:
    """Drop siblings that sit in a kept member's rectangle: twins, not panels.

    `twinx` and `twiny` create the twin in the host's own position, the
    public tell for a twin. The entry axes is always kept, so distilling
    a twin directly treats the twin and leaves the host out. A dropped
    twin still shares the host's Ticker on the shared axis, so that
    axis follows the host, invisibly since matplotlib hides it on the
    twin; the twin's own axis and spines are untouched, and its box
    stays, hence the warning.
    """
    # `_component` puts `ax` first, so `unit[1:]` is every sibling but it.
    kept = [entry]
    dropped = False
    for member in unit[1:]:
        rect = member.get_position(original=True).bounds
        if any(rect == k.get_position(original=True).bounds for k in kept):
            dropped = True
            continue
        kept.append(member)
    if dropped:
        warnings.warn(
            "vanzelfsprekend: the axes has a twin (twinx/twiny); twins are "
            "not supported, the twin keeps its frame",
            stacklevel=4,
        )
    return kept


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
    unit = _drop_twins(ax, _component(ax))
    groups: dict[Axes, dict[str, list[Axes] | None]] = {}
    for member in unit:
        per_axis: dict[str, list[Axes] | None] = {}
        for name, grouper in (
            ("x", member.get_shared_x_axes()),
            ("y", member.get_shared_y_axes()),
        ):
            sibling_ids = {id(s) for s in grouper.get_siblings(member)}
            per_axis[name] = [s for s in unit if id(s) in sibling_ids]
        groups[member] = per_axis
    agree: dict[tuple[str, frozenset[int]], bool] = {}
    for per_axis in groups.values():
        for name in ("x", "y"):
            # Only the assignment below writes `None`, and it never
            # revisits a pair, so every read here is a real list.
            siblings = cast("list[Axes]", per_axis[name])
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
