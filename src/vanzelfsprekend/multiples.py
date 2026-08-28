"""Small multiples: one treatment for a grid of axes on a shared scale."""

from collections.abc import Iterable, Sequence
from typing import Literal

import numpy as np
from matplotlib.axes import Axes
from matplotlib.axis import Axis, Ticker
from matplotlib.gridspec import SubplotSpec
from matplotlib.ticker import Locator

from vanzelfsprekend.compose import apply
from vanzelfsprekend.frame import _is_date_converter
from vanzelfsprekend.hook import ensure_state


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
    treated = _check_group_agreement(groups)  # noqa: F841
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
    return panels


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
