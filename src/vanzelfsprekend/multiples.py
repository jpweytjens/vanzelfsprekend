"""Small multiples: one treatment for a grid of axes on a shared scale."""

from collections.abc import Iterable, Sequence
from typing import Literal

import numpy as np
from matplotlib.axes import Axes
from matplotlib.axis import Axis, Ticker
from matplotlib.gridspec import GridSpecBase, SubplotSpec
from matplotlib.ticker import Locator

from vanzelfsprekend import labels as labels_
from vanzelfsprekend.compose import apply
from vanzelfsprekend.frame import _is_date_converter
from vanzelfsprekend.hook import add_applier, ensure_state, get_state, run_appliers


def _data_union(axes: Sequence[Axes], name: str) -> tuple[float, float] | None:
    """Union of the members' data intervals along `name` (`'x'` or `'y'`).

    Log axes substitute `minpos` for a nonpositive minimum, mirroring
    the locators' own reading. Members with no finite data are skipped;
    returns `None` when none remain or the union is degenerate.
    """
    lo, hi = np.inf, -np.inf
    for ax in axes:
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


class _GroupLocator(Locator):
    """Delegate tick placement to `inner`, fed the group's data union.

    Installed on a panel's axis in place of the locator `apply` chose,
    so ticks are recomputed on every draw from the union of the group
    members' data instead of the one panel's. Everything else defers to
    `inner`, whose own axis binding is left in place so a formatter
    constructed around it (`ConciseDateFormatter`) keeps working.
    """

    def __init__(self, inner: Locator, members: Sequence[Axes], name: str) -> None:
        self._inner = inner
        self._members = members
        self._name = name

    def __call__(self) -> np.ndarray:  # ty: ignore[invalid-method-override]
        union = _data_union(self._members, self._name)
        if union is None:
            return np.asarray(self._inner())
        return np.asarray(self._inner.tick_values(*union))

    def tick_values(self, vmin: float, vmax: float) -> np.ndarray:  # ty: ignore
        return np.asarray(self._inner.tick_values(vmin, vmax))

    def nonsingular(  # ty: ignore[invalid-method-override]
        self, vmin: float, vmax: float
    ) -> tuple[float, float]:
        return self._inner.nonsingular(vmin, vmax)

    def view_limits(self, vmin: float, vmax: float) -> tuple[float, float]:
        return self._inner.view_limits(vmin, vmax)


def _view_union(members: Sequence[Axes], name: str) -> tuple[float, float] | None:
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


def _apply_multiples(ax: Axes) -> bool:
    """Apply the `"multiples"` treatment: the sole writer of view limits.

    Sets each treated axis' view limits to the union of its scale
    group's members, so every panel in the group converges to the same
    limits. Spine bounds stay with the frame applier; tick positions
    with the wrapped `_GroupLocator`.
    """
    state = get_state(ax)
    if state is None or "multiples" not in state:
        return False
    changed = False
    for name, members in state["multiples"]["groups"].items():
        union = _view_union(members, name)
        if union is None:
            continue
        axis = ax.xaxis if name == "x" else ax.yaxis
        if tuple(axis.get_view_interval()) != union:
            (ax.set_xlim if name == "x" else ax.set_ylim)(union)
            changed = True
    return changed


def _unshare_tickers(
    panels: tuple[Axes, ...],
) -> dict[int, dict[str, tuple[Ticker, Ticker]]]:
    """Give each matplotlib-shared axis its own `Ticker` pair.

    Must run before `apply`: shared panels hold one `Ticker` object, so
    a locator installed through it lands in every sibling and the frame
    snapshot records a sibling's locator as the original. The fresh
    pair only needs to be functional — `apply` replaces it immediately
    and restore re-attaches the saved originals.
    """
    saved: dict[int, dict[str, tuple[Ticker, Ticker]]] = {}
    for ax in panels:
        for name, axis, grouper in (
            ("x", ax.xaxis, ax.get_shared_x_axes()),
            ("y", ax.yaxis, ax.get_shared_y_axes()),
        ):
            if len(grouper.get_siblings(ax)) <= 1:
                continue
            old_major, old_minor = axis.major, axis.minor
            converter = axis.get_converter()
            is_date = converter is not None and _is_date_converter(converter)
            axis.major = Ticker()
            axis.minor = Ticker()
            locator = type(old_major.locator)()
            formatter = (
                type(old_major.formatter)(locator)  # ty: ignore[too-many-positional-arguments]
                if is_date
                else type(old_major.formatter)()
            )
            axis.set_major_locator(locator)  # ty: ignore[invalid-argument-type]
            axis.set_major_formatter(formatter)  # ty: ignore[invalid-argument-type]
            axis.set_minor_locator(type(old_minor.locator)())  # ty: ignore[invalid-argument-type]
            axis.set_minor_formatter(type(old_minor.formatter)())  # ty: ignore[invalid-argument-type]
            saved.setdefault(id(ax), {})[name] = (old_major, old_minor)
    return saved


def _carries_furniture(ss: SubplotSpec, gridspec: GridSpecBase) -> dict[str, bool]:
    """Whether `ss` sits against the grid's bottom row / left column."""
    return {
        "x": ss.rowspan.stop == gridspec.nrows,
        "y": ss.colspan.start == 0,
    }


def _spans_intersect(a: range, b: range) -> bool:
    return max(a.start, b.start) < min(a.stop, b.stop)


def _trim_members(
    panels: Sequence[Axes],
    specs: Sequence[SubplotSpec],
    ss: SubplotSpec,
    name: str,
) -> list[Axes]:
    """Panels whose colspan (`'x'`) / rowspan (`'y'`) intersects `ss`'s."""
    span = ss.colspan if name == "x" else ss.rowspan
    return [
        ax
        for ax, other in zip(panels, specs, strict=True)
        if _spans_intersect(span, other.colspan if name == "x" else other.rowspan)
    ]


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
    n: int = 5,
    offset: float | None = None,
    nice_numbers: Sequence[float] | None = None,
    weights: dict[str, float] | None = None,
    xlabel: str | Sequence[str] | None = None,
    ylabel: str | Sequence[str] | None = None,
) -> tuple[Axes, ...]:
    """Treat a grid of axes as small multiples on a common scale.

    Applies `apply` to every panel, scopes scales by `compare`
    (`'figure'` shares both axes across all panels; `'row'` scopes y
    per row; `'column'` scopes x per column), and keeps axis furniture
    only on the left column and bottom row. Works on grids from
    `plt.subplots`, `subplot_mosaic` or a raw gridspec; builds nothing.

    Parameters
    ----------
    axes : iterable of matplotlib.axes.Axes
        The grid's panels, all from one figure and one gridspec.
    compare : {'figure', 'row', 'column'}
        The smallest set of panels that are fully comparable.
    frame, n, offset, nice_numbers, weights
        Forwarded to `apply` per panel; see `vanzelfsprekend.apply`.
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
    treated = _check_group_agreement(groups)
    _check_sharing(panels, groups)
    gridspec = specs[0].get_gridspec()
    _check_label(ylabel, "ylabel", scoped=compare == "row", count=gridspec.nrows)
    _check_label(xlabel, "xlabel", scoped=compare == "column", count=gridspec.ncols)

    saved_tickers = _unshare_tickers(panels)
    for ax in panels:
        ensure_state(ax)["multiples"] = {
            "snapshot": {"tickers": saved_tickers.get(id(ax), {})}
        }
    for ax in panels:
        apply(
            ax,
            frame=frame,
            n=n,
            offset=offset,
            nice_numbers=nice_numbers,
            weights=weights,
        )
    grid = {"panels": panels, "torn_down": False}
    key_of = {
        (name, id(ax)): key
        for name, per_key in groups.items()
        for key, members in per_key.items()
        for ax in members
    }
    for ax, ss in zip(panels, specs, strict=True):
        panel_groups = {}
        for name in ("x", "y"):
            key = key_of[(name, id(ax))]
            if not treated[(name, key)]:
                continue
            members = groups[name][key]
            panel_groups[name] = members
            axis = ax.xaxis if name == "x" else ax.yaxis
            frame_state = ensure_state(ax)["frame"]
            if name in frame_state["active"]:
                axis.set_major_locator(
                    _GroupLocator(axis.get_major_locator(), members, name)
                )
        state = ensure_state(ax)
        state["multiples"]["groups"] = panel_groups
        state["multiples"]["grid"] = grid
        state["multiples"]["snapshot"].update(
            limits={"x": ax.get_xlim(), "y": ax.get_ylim()},
            autoscale={
                "x": ax.get_autoscalex_on(),
                "y": ax.get_autoscaley_on(),
            },
        )
        carries = _carries_furniture(ss, gridspec)
        snapshot = state["multiples"]["snapshot"]
        snapshot["furniture"] = {}
        for name in panel_groups:
            axis = ax.xaxis if name == "x" else ax.yaxis
            side = "bottom" if name == "x" else "left"
            if carries[name]:
                members = _trim_members(panels, specs, ss, name)
                intervals = ensure_state(ax)["frame"].setdefault("intervals", {})
                intervals[name] = lambda members=members, name=name: _data_union(
                    members, name
                )
            else:
                params = axis.get_tick_params(which="major")
                snapshot["furniture"][name] = {
                    "spine": ax.spines[side].get_visible(),
                    "tick": params.get(side, True),
                    "label": params.get(f"label{side}", True),
                }
                ax.spines[side].set_visible(False)
                axis.set_tick_params(
                    which="both",
                    **{side: False, f"label{side}": False},
                )
        add_applier(ax, "multiples", _apply_multiples)
    prior_labels = _place_labels(panels, specs, gridspec, xlabel, ylabel)
    for ax in panels:
        ensure_state(ax)["multiples"]["snapshot"]["labels"] = prior_labels.get(
            id(ax), {}
        )
    for ax in panels:
        run_appliers(ax)
    return panels


def _teardown_grid(grid: dict) -> None:
    """Tear the grid layer off every member; idempotent.

    Everything figure-level comes off in one pass — the shared scale
    cannot survive losing a member. Tickers stay: re-sharing here would
    hand every still-treated sibling a shared container again, so each
    panel's original `Ticker` waits for that panel's own restore.
    """
    if grid["torn_down"]:
        return
    grid["torn_down"] = True
    # Two passes: a matplotlib-shared `set_xlim`/`set_ylim` disables
    # autoscale on every sibling sharing that axis, so restoring
    # autoscale inline here would have a later panel's limits undo an
    # earlier panel's autoscale. Limits land in the first pass;
    # autoscale only after every panel's limits have settled.
    for ax in grid["panels"]:
        state = get_state(ax)
        if state is None or "multiples" not in state:
            continue
        state["appliers"].pop("multiples", None)
        snap = state["multiples"]["snapshot"]
        frame_state = state.get("frame")
        if frame_state is not None:
            frame_state.pop("intervals", None)
        for name in state["multiples"]["groups"]:
            axis = ax.xaxis if name == "x" else ax.yaxis
            locator = axis.get_major_locator()
            if isinstance(locator, _GroupLocator):
                axis.set_major_locator(locator._inner)
        ax.set_xlim(snap["limits"]["x"])
        ax.set_ylim(snap["limits"]["y"])
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
    for ax in grid["panels"]:
        state = get_state(ax)
        if state is None or "multiples" not in state:
            continue
        snap = state["multiples"]["snapshot"]
        ax.set_autoscalex_on(snap["autoscale"]["x"])
        ax.set_autoscaley_on(snap["autoscale"]["y"])


def _reattach_tickers(ax: Axes, snapshot: dict) -> None:
    """Re-attach this panel's original shared tickers.

    Runs from `compose.restore` after its frame block, so the pristine
    locator has already been written into the fresh unshared ticker and
    the shared container comes back untouched. Also clears the spine
    bounds the frame block just stamped: `Spine.set_bounds(None, None)`
    reads "leave unchanged", not "unset", so it always writes the
    current view interval — never the `None` a panel this treatment
    framed needs in order to end up as unbounded as one it never
    touched.
    """
    for name, (major, minor) in snapshot["tickers"].items():
        axis = ax.xaxis if name == "x" else ax.yaxis
        axis.major = major
        axis.minor = minor
        axis.stale = True
    for side in ("bottom", "left"):
        ax.spines[side]._bounds = None  # ty: ignore[unresolved-attribute]


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


def _axis_kind(axis: Axis) -> tuple[str, bool, bool]:
    scale = axis.get_scale()
    converter = axis.get_converter()
    is_date = converter is not None and _is_date_converter(converter)
    supported = scale in ("linear", "log") and (converter is None or is_date)
    return (scale, is_date, supported)


def _check_group_agreement(
    groups: dict[str, dict[object, list[Axes]]],
) -> dict[tuple[str, object], bool]:
    treated: dict[tuple[str, object], bool] = {}
    for name, per_key in groups.items():
        for key, members in per_key.items():
            kinds = {
                _axis_kind(ax.xaxis if name == "x" else ax.yaxis) for ax in members
            }
            if len(kinds) > 1:
                raise ValueError(
                    f"panels in one {name} group disagree on scale or "
                    f"date-ness: {sorted(k[:2] for k in kinds)}; a common "
                    "scale across them means nothing"
                )
            treated[(name, key)] = kinds.pop()[2]
    return treated


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
