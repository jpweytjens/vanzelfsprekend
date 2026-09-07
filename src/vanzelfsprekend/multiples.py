"""Small multiples: one treatment for a grid of axes on a shared scale."""

from collections.abc import Iterable, Sequence
from typing import Literal

from matplotlib.axes import Axes
from matplotlib.gridspec import GridSpecBase, SubplotSpec

from vanzelfsprekend import labels as labels_
from vanzelfsprekend.group import axis_kinds, treat
from vanzelfsprekend.hook import ensure_state, get_state, run_appliers
from vanzelfsprekend.locator import SPACING


def _carries_furniture(ss: SubplotSpec, gridspec: GridSpecBase) -> dict[str, bool]:
    """Whether `ss` sits against the grid's bottom row / left column."""
    return {
        "x": ss.rowspan.stop == gridspec.nrows,
        "y": ss.colspan.start == 0,
    }


def _place_labels(
    panels: Sequence[Axes],
    specs: Sequence[SubplotSpec],
    gridspec: GridSpecBase,
    xlabel: str | Sequence[str] | None,
    ylabel: str | Sequence[str] | None,
) -> dict[int, dict[str, str]]:
    """Label furnished panels; return `{id(ax): {name: prior_text}}`."""
    prior: dict[int, dict[str, str]] = {}

    def _set(ax: Axes, name: str, text: str) -> None:
        prior.setdefault(id(ax), {})[name] = (
            ax.get_xlabel() if name == "x" else ax.get_ylabel()
        )
        (labels_.xlabel if name == "x" else labels_.ylabel)(ax, text)

    bottom = [
        (ax, ss)
        for ax, ss in zip(panels, specs, strict=True)
        if ss.rowspan.stop == gridspec.nrows
    ]
    left = [
        (ax, ss) for ax, ss in zip(panels, specs, strict=True) if ss.colspan.start == 0
    ]
    if isinstance(xlabel, str):
        ax, _ = max(bottom, key=lambda pair: pair[1].colspan.stop)
        _set(ax, "x", xlabel)
    elif xlabel is not None:
        for ax, ss in bottom:
            _set(ax, "x", xlabel[ss.colspan.start])
    if isinstance(ylabel, str):
        ax, _ = min(left, key=lambda pair: pair[1].rowspan.start)
        _set(ax, "y", ylabel)
    elif ylabel is not None:
        for ax, ss in left:
            _set(ax, "y", ylabel[ss.rowspan.start])
    return prior


def small_multiples(
    axes: Iterable[Axes],
    compare: Literal["figure", "row", "column"] = "figure",
    frame: str | tuple[str, str] = "nice",
    spacing: float | tuple[float, float] = SPACING,
    n: int | None = None,
    offset: float | None = None,
    nice_numbers: Sequence[float] | None = None,
    weights: dict[str, float] | None = None,
    xlabel: str | Sequence[str] | None = None,
    ylabel: str | Sequence[str] | None = None,
) -> tuple[Axes, ...]:
    """Treat a grid of axes as small multiples on a common scale.

    Distills every panel, scopes scales by `compare`
    (`'figure'` shares both axes across all panels; `'row'` scopes y
    per row; `'column'` scopes x per column), and keeps axis furniture
    only on the left column and bottom row. Works on grids from
    `plt.subplots`, `subplot_mosaic` or a raw gridspec; builds nothing.

    Every panel converges onto one ascending scale per group, so a
    panel with a deliberately inverted axis is silently re-oriented on
    the first draw.

    Panels already tied with `sharex` or `sharey` are fine as long as the
    sharing does not cut across what `compare` scopes separately; pass
    the whole shared set, since a sibling left out still shares the
    others' ticks. Restoring any panel restores the grid.

    Parameters
    ----------
    axes : iterable of matplotlib.axes.Axes
        The grid's panels, all from one figure and one gridspec.
    compare : {'figure', 'row', 'column'}
        The smallest set of panels that are fully comparable.
    frame, spacing, n, offset, nice_numbers, weights
        Forwarded to `distill` per panel; see `vanzelfsprekend.distill`.
    xlabel, ylabel : str or sequence of str, optional
        Axis labels. A sequence is accepted only for an axis `compare`
        scopes to rows or columns, one entry per row or column.

    Returns
    -------
    tuple of matplotlib.axes.Axes
        The panels, in the order given.
    """
    panels = tuple(axes)
    if compare not in ("figure", "row", "column"):
        raise ValueError(
            f"compare must be 'figure', 'row' or 'column', got {compare!r}"
        )
    specs = _subplotspecs_or_raise(panels)
    _check_spanning(specs, compare)
    groups = _scale_groups(panels, specs, compare)
    _check_group_agreement(groups)
    _check_sharing(panels, groups)
    gridspec = specs[0].get_gridspec()
    _check_label(ylabel, "ylabel", scoped=compare == "row", count=gridspec.nrows)
    _check_label(xlabel, "xlabel", scoped=compare == "column", count=gridspec.ncols)

    key_of = {
        (name, id(ax)): key
        for name, per_key in groups.items()
        for key, members in per_key.items()
        for ax in members
    }
    treat(
        {
            ax: {name: groups[name][key_of[(name, id(ax))]] for name in ("x", "y")}
            for ax in panels
        },
        frame=frame,
        spacing=spacing,
        n=n,
        offset=offset,
        nice_numbers=nice_numbers,
        weights=weights,
        stacklevel=4,
    )
    grid = {"panels": panels, "torn_down": False}
    for ax, ss in zip(panels, specs, strict=True):
        state = ensure_state(ax)
        state["multiples"] = {"grid": grid, "snapshot": {"furniture": {}}}
        carries = _carries_furniture(ss, gridspec)
        active = state["frame"]["active"]
        for name in ("x", "y"):
            if name not in active or carries[name]:
                continue
            axis = ax.xaxis if name == "x" else ax.yaxis
            side = "bottom" if name == "x" else "left"
            params = axis.get_tick_params(which="major")
            state["multiples"]["snapshot"]["furniture"][name] = {
                "spine": ax.spines[side].get_visible(),
                "tick": params.get(side, True),
                "label": params.get(f"label{side}", True),
            }
            ax.spines[side].set_visible(False)
            axis.set_tick_params(
                which="both",
                **{side: False, f"label{side}": False},
            )
    prior_labels = _place_labels(panels, specs, gridspec, xlabel, ylabel)
    for ax in panels:
        ensure_state(ax)["multiples"]["snapshot"]["labels"] = prior_labels.get(
            id(ax), {}
        )
    for ax in panels:
        run_appliers(ax)
    return panels


def _teardown_grid(grid: dict) -> None:
    """Tear the grid layer (hidden furniture, labels) off every member; idempotent.

    Locators, spines, limits and autoscale are the group's, restored by
    `compose.restore` for every member of the unit.
    """
    if grid["torn_down"]:
        return
    grid["torn_down"] = True
    for ax in grid["panels"]:
        state = get_state(ax)
        if state is None or "multiples" not in state:
            continue
        snap = state["multiples"]["snapshot"]
        for name, prior in snap["furniture"].items():
            side = "bottom" if name == "x" else "left"
            ax.spines[side].set_visible(prior["spine"])
            axis = ax.xaxis if name == "x" else ax.yaxis
            axis.set_tick_params(
                which="both",
                **{side: prior["tick"], f"label{side}": prior["label"]},
            )
        for name, text in snap.get("labels", {}).items():
            (ax.set_xlabel if name == "x" else ax.set_ylabel)(text)


def _subplotspecs_or_raise(panels: tuple[Axes, ...]) -> list[SubplotSpec]:
    specs = []
    for i, ax in enumerate(panels):
        ss = ax.get_subplotspec()
        if ss is None:
            raise ValueError(
                f"panel {i} has no subplotspec (from fig.add_axes?); "
                "small_multiples needs a gridded axes"
            )
        specs.append(ss)
    if len({ax.get_figure() for ax in panels}) > 1:
        raise ValueError("panels come from more than one figure")
    if len({ss.get_gridspec() for ss in specs}) > 1:
        raise ValueError("panels come from more than one gridspec")
    return specs


def _check_spanning(specs: list[SubplotSpec], compare: str) -> None:
    for i, ss in enumerate(specs):
        if compare == "row" and len(ss.rowspan) > 1:
            raise ValueError(
                f"panel {i} spans rows {ss.rowspan.start}-{ss.rowspan.stop - 1}, "
                "but compare='row' scopes y per row; use compare='figure' or "
                "split the panel"
            )
        if compare == "column" and len(ss.colspan) > 1:
            raise ValueError(
                f"panel {i} spans columns {ss.colspan.start}-{ss.colspan.stop - 1}, "
                "but compare='column' scopes x per column; use compare='figure' "
                "or split the panel"
            )


def _scale_groups(
    panels: tuple[Axes, ...], specs: list[SubplotSpec], compare: str
) -> dict[str, dict[object, list[Axes]]]:
    groups: dict[str, dict[object, list[Axes]]] = {"x": {}, "y": {}}
    for ax, ss in zip(panels, specs, strict=True):
        x_key = ss.colspan.start if compare == "column" else "figure"
        y_key = ss.rowspan.start if compare == "row" else "figure"
        groups["x"].setdefault(x_key, []).append(ax)
        groups["y"].setdefault(y_key, []).append(ax)
    return groups


def _check_group_agreement(groups: dict[str, dict[object, list[Axes]]]) -> None:
    for name, per_key in groups.items():
        for members in per_key.values():
            kinds = axis_kinds(members, name)
            if len(kinds) > 1:
                raise ValueError(
                    f"panels in one {name} group disagree on scale or "
                    f"date-ness: {sorted(k[:2] for k in kinds)}; a common "
                    "scale across them means nothing"
                )


def _check_sharing(
    panels: tuple[Axes, ...], groups: dict[str, dict[object, list[Axes]]]
) -> None:
    for name, kwarg in (("x", "sharex"), ("y", "sharey")):
        key_of = {
            id(ax): key for key, members in groups[name].items() for ax in members
        }
        for ax in panels:
            grouper = ax.get_shared_x_axes() if name == "x" else ax.get_shared_y_axes()
            for sibling in grouper.get_siblings(ax):
                if id(sibling) in key_of and key_of[id(sibling)] != key_of[id(ax)]:
                    raise ValueError(
                        f"{kwarg}=True ties panels across groups that "
                        f"compare scopes separately; drop {kwarg}"
                    )


def _check_label(
    value: str | Sequence[str] | None, name: str, scoped: bool, count: int
) -> None:
    if value is None or isinstance(value, str):
        return
    if not scoped:
        raise ValueError(
            f"{name} accepts a sequence only when compare scopes that "
            "axis to rows or columns; pass a single string"
        )
    if len(value) != count:
        raise ValueError(f"{name} has {len(value)} entries for {count} groups")
