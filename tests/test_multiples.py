import matplotlib.pyplot as plt
import numpy as np
import pytest

import vanzelfsprekend as vzs
from vanzelfsprekend.hook import run_appliers
from vanzelfsprekend.multiples import _GroupLocator


def test_group_locator_computes_ticks_from_union():
    fig, axes = plt.subplots(1, 2)
    axes[0].plot([0, 4], [0, 1])
    axes[1].plot([6, 10], [0, 1])
    vzs.range_frame(axes[0])
    inner = axes[0].xaxis.get_major_locator()
    axes[0].xaxis.set_major_locator(_GroupLocator(inner, list(axes), "x"))
    fig.canvas.draw()
    expected = vzs.TalbotLocator().tick_values(0, 10)
    np.testing.assert_allclose(axes[0].xaxis.get_majorticklocs(), expected)
    plt.close(fig)


def test_group_locator_falls_back_to_inner_when_union_empty():
    fig, axes = plt.subplots(1, 2)
    vzs.range_frame(axes[0])  # no data anywhere
    inner = axes[0].xaxis.get_major_locator()
    axes[0].xaxis.set_major_locator(_GroupLocator(inner, list(axes), "x"))
    fig.canvas.draw()  # must not raise; inner's own fallback path runs
    plt.close(fig)


def _grid22():
    fig, axes = plt.subplots(2, 2)
    for ax, (lo, hi) in zip(axes.flat, [(0, 1), (2, 5), (-3, 0), (4, 9)], strict=True):
        ax.plot([lo, hi], [lo, hi])
    return fig, axes


def test_small_multiples_returns_panels_framed():
    fig, axes = _grid22()
    result = vzs.small_multiples(axes.flat)
    assert result == tuple(axes.flat)
    assert all(not ax.spines["top"].get_visible() for ax in axes.flat)
    plt.close(fig)


def test_rejects_panel_without_subplotspec():
    fig = plt.figure()
    free = fig.add_axes((0.1, 0.1, 0.8, 0.8))
    with pytest.raises(ValueError, match="subplotspec"):
        vzs.small_multiples([free])
    plt.close(fig)


def test_rejects_panels_from_two_figures():
    fig1, ax1 = plt.subplots()
    fig2, ax2 = plt.subplots()
    with pytest.raises(ValueError, match="figure"):
        vzs.small_multiples([ax1, ax2])
    plt.close(fig1)
    plt.close(fig2)


def test_rejects_mixed_scales_in_one_group():
    fig, axes = plt.subplots(1, 2)
    axes[0].set_yscale("log")
    axes[0].plot([1, 2], [1, 10])
    axes[1].plot([1, 2], [1, 10])
    with pytest.raises(ValueError, match="scale"):
        vzs.small_multiples(axes)
    plt.close(fig)


def test_rejects_date_beside_plain_axis():
    import datetime as dt

    fig, axes = plt.subplots(1, 2)
    days = [dt.datetime(2024, 1, 1) + dt.timedelta(days=i) for i in range(5)]
    axes[0].plot(days, range(5))
    axes[1].plot(range(5), range(5))
    with pytest.raises(ValueError, match="date"):
        vzs.small_multiples(axes)
    plt.close(fig)


def test_rejects_spanning_panel_under_scoped_compare():
    fig = plt.figure()
    panels = fig.subplot_mosaic("AB;AC")
    for ax in panels.values():
        ax.plot([0, 1], [0, 1])
    with pytest.raises(ValueError, match="spans rows"):
        vzs.small_multiples(panels.values(), compare="row")
    plt.close(fig)


def test_accepts_spanning_panel_under_figure_compare():
    fig = plt.figure()
    panels = fig.subplot_mosaic("AB;AC")
    for ax in panels.values():
        ax.plot([0, 1], [0, 1])
    vzs.small_multiples(panels.values())  # must not raise
    plt.close(fig)


def test_rejects_sharing_that_contradicts_compare():
    fig, axes = plt.subplots(2, 2, sharey=True)
    for ax in axes.flat:
        ax.plot([0, 1], [0, 1])
    with pytest.raises(ValueError, match="sharey"):
        vzs.small_multiples(axes.flat, compare="row")
    plt.close(fig)


def test_rejects_label_sequence_on_figure_scoped_axis():
    fig, axes = _grid22()
    with pytest.raises(ValueError, match="ylabel"):
        vzs.small_multiples(axes.flat, ylabel=["a", "b"])
    plt.close(fig)


def test_rejects_label_sequence_length_mismatch():
    fig, axes = _grid22()
    with pytest.raises(ValueError, match=r"3.*2|2.*3"):
        vzs.small_multiples(axes.flat, compare="row", ylabel=["a", "b", "c"])
    plt.close(fig)


def test_sharex_panels_get_their_own_tickers():
    fig, axes = plt.subplots(1, 2, sharex=True)
    axes[0].plot([0, 4], [0, 1])
    axes[1].plot([6, 10], [0, 1])
    assert axes[0].xaxis.major is axes[1].xaxis.major  # matplotlib's sharing
    vzs.small_multiples(axes)
    assert axes[0].xaxis.major is not axes[1].xaxis.major
    fig.canvas.draw()  # and the treatment survives a draw
    plt.close(fig)


def test_sharex_date_grid_draws():
    import datetime as dt

    fig, axes = plt.subplots(1, 2, sharex=True)
    days = [dt.datetime(2024, 1, 1) + dt.timedelta(days=7 * i) for i in range(9)]
    axes[0].plot(days[:5], range(5))
    axes[1].plot(days[4:], range(5))
    vzs.small_multiples(axes)
    fig.canvas.draw()  # fresh date locator/formatter pair must be functional
    plt.close(fig)


def test_compare_figure_shares_both_limits():
    fig, axes = _grid22()
    vzs.small_multiples(axes.flat)
    fig.canvas.draw()
    assert len({ax.get_xlim() for ax in axes.flat}) == 1
    assert len({ax.get_ylim() for ax in axes.flat}) == 1
    lo, hi = axes.flat[0].get_ylim()
    assert lo <= -3  # covers every panel's data
    assert hi >= 9
    plt.close(fig)


def test_compare_row_scopes_y_per_row():
    fig, axes = _grid22()
    vzs.small_multiples(axes.flat, compare="row")
    fig.canvas.draw()
    assert axes[0, 0].get_ylim() == axes[0, 1].get_ylim()
    assert axes[1, 0].get_ylim() == axes[1, 1].get_ylim()
    assert axes[0, 0].get_ylim() != axes[1, 0].get_ylim()
    assert len({ax.get_xlim() for ax in axes.flat}) == 1
    plt.close(fig)


def test_compare_column_scopes_x_per_column():
    fig, axes = _grid22()
    vzs.small_multiples(axes.flat, compare="column")
    fig.canvas.draw()
    assert axes[0, 0].get_xlim() == axes[1, 0].get_xlim()
    assert axes[0, 1].get_xlim() == axes[1, 1].get_xlim()
    assert axes[0, 0].get_xlim() != axes[0, 1].get_xlim()
    assert len({ax.get_ylim() for ax in axes.flat}) == 1
    plt.close(fig)


def test_ticks_come_from_group_union():
    fig, axes = plt.subplots(1, 2)
    axes[0].plot([0, 4], [0, 1])
    axes[1].plot([6, 10], [0, 1])
    vzs.small_multiples(axes)
    fig.canvas.draw()
    expected = vzs.TalbotLocator().tick_values(0, 10)
    np.testing.assert_allclose(axes[0].xaxis.get_majorticklocs(), expected)
    plt.close(fig)


@pytest.mark.parametrize("sharex", [False, True])
def test_appliers_reach_a_fixed_point(sharex):
    fig, axes = plt.subplots(2, 2, sharex=sharex)
    for ax, (lo, hi) in zip(axes.flat, [(0, 1), (2, 5), (-3, 0), (4, 9)], strict=True):
        ax.plot([lo, hi], [lo, hi])
    vzs.small_multiples(axes.flat)
    fig.canvas.draw()
    fig.canvas.draw()
    assert not any(run_appliers(ax) for ax in axes.flat)
    plt.close(fig)


def test_inner_panels_carry_no_furniture():
    fig, axes = _grid22()
    vzs.small_multiples(axes.flat)
    fig.canvas.draw()
    inner = axes[0, 1]  # top-right: neither left column nor bottom row
    assert not inner.spines["bottom"].get_visible()
    assert not inner.spines["left"].get_visible()
    assert not any(t.get_visible() for t in inner.xaxis.get_ticklabels())
    outer = axes[1, 0]  # bottom-left: both
    assert outer.spines["bottom"].get_visible()
    assert outer.spines["left"].get_visible()
    assert any(t.get_visible() for t in outer.xaxis.get_ticklabels())
    # top-left keeps y furniture but not x; bottom-right the reverse
    assert axes[0, 0].spines["left"].get_visible()
    assert not axes[0, 0].spines["bottom"].get_visible()
    assert axes[1, 1].spines["bottom"].get_visible()
    assert not axes[1, 1].spines["left"].get_visible()
    plt.close(fig)


def _column_union_x(axes, col):
    return (
        min(ax.xaxis.get_data_interval()[0] for ax in axes[:, col]),
        max(ax.xaxis.get_data_interval()[1] for ax in axes[:, col]),
    )


@pytest.mark.parametrize("frame", ["nice", "data", "loose"])
def test_bottom_spine_trims_to_column_union(frame):
    fig, axes = _grid22()
    vzs.small_multiples(axes.flat, frame=frame)
    fig.canvas.draw()
    ax = axes[1, 0]
    dmin, dmax = _column_union_x(axes, 0)
    ticks = sorted(ax.xaxis.get_majorticklocs())
    if frame == "data":
        expected = (dmin, dmax)
    elif frame == "nice":
        inside = [t for t in ticks if dmin <= t <= dmax]
        expected = (min(inside), max(inside))
    else:
        below = [t for t in ticks if t <= dmin + 1e-9]
        above = [t for t in ticks if t >= dmax - 1e-9]
        expected = (
            max(below) if below else min(ticks),
            min(above) if above else max(ticks),
        )
    assert ax.spines["bottom"].get_bounds() == pytest.approx(expected)
    plt.close(fig)


def test_spanning_panel_trims_over_covered_columns():
    fig = plt.figure()
    panels = fig.subplot_mosaic("AB;CC")  # C spans both columns, bottom row
    panels["A"].plot([0, 2], [0, 1])
    panels["B"].plot([5, 7], [0, 1])
    panels["C"].plot([1, 3], [0, 1])
    vzs.small_multiples(panels.values(), frame="data")
    fig.canvas.draw()
    # C's bottom spine speaks for both columns: union of all x data.
    assert panels["C"].spines["bottom"].get_bounds() == (0.0, 7.0)
    plt.close(fig)


def test_single_ylabel_lands_once_on_top_left():
    fig, axes = _grid22()
    vzs.small_multiples(axes.flat, ylabel="rate")
    assert axes[0, 0].get_ylabel() == "rate"
    assert all(ax.get_ylabel() == "" for ax in axes.flat if ax is not axes[0, 0])
    plt.close(fig)


def test_grid_ylabel_sits_flush_with_top_tick():
    fig, axes = _grid22()
    vzs.small_multiples(axes.flat, ylabel="rate")
    fig.canvas.draw()
    ax = axes[0, 0]
    label = ax.yaxis.label.get_window_extent()
    ticks = [
        t.get_window_extent()
        for t in ax.yaxis.get_ticklabels()
        if t.get_text() and t.get_visible()
    ]
    top = max(ticks, key=lambda b: b.y1)
    assert abs(label.y1 - top.y1) < 1
    plt.close(fig)


def test_single_xlabel_lands_once_on_bottom_right():
    fig, axes = _grid22()
    vzs.small_multiples(axes.flat, xlabel="year")
    assert axes[1, 1].get_xlabel() == "year"
    assert all(ax.get_xlabel() == "" for ax in axes.flat if ax is not axes[1, 1])
    plt.close(fig)


def test_ylabel_sequence_labels_each_row():
    fig, axes = _grid22()
    vzs.small_multiples(axes.flat, compare="row", ylabel=["a", "b"])
    assert axes[0, 0].get_ylabel() == "a"
    assert axes[1, 0].get_ylabel() == "b"
    assert axes[0, 1].get_ylabel() == ""
    plt.close(fig)


def test_restore_one_panel_degrades_siblings_to_single_axes():
    fig, axes = _grid22()
    vzs.small_multiples(axes.flat)
    fig.canvas.draw()
    vzs.restore(axes[0, 0])
    fig.canvas.draw()
    # Restored panel: autoscaling back on, no vzs state left.
    assert axes[0, 0].get_autoscalex_on()
    assert not hasattr(axes[0, 0], "_vanzelfsprekend_state")
    # Sibling: still treated, but panel-local — its own data, its own trim.
    sibling = axes[1, 1]
    assert sibling.get_autoscalex_on()
    assert sibling.spines["bottom"].get_visible()  # furniture back
    ticks = [
        t
        for t in sibling.xaxis.get_majorticklocs()
        if 4 <= t <= 9  # sibling's own data range
    ]
    assert sibling.spines["bottom"].get_bounds() == (min(ticks), max(ticks))
    plt.close(fig)


def test_restore_every_panel_matches_pristine_grid():
    def build(treat):
        fig, axes = plt.subplots(2, 2, sharex=True)
        for ax, (lo, hi) in zip(
            axes.flat, [(0, 1), (2, 5), (-3, 0), (4, 9)], strict=True
        ):
            ax.plot([lo, hi], [lo, hi])
        if treat:
            vzs.small_multiples(axes.flat)
            fig.canvas.draw()
            for ax in axes.flat:
                vzs.restore(ax)
        fig.canvas.draw()
        return fig, axes

    fig_a, treated = build(treat=True)
    fig_b, pristine = build(treat=False)
    for ta, pa in zip(treated.flat, pristine.flat, strict=True):
        assert ta.get_xlim() == pa.get_xlim()
        assert ta.get_ylim() == pa.get_ylim()
        assert ta.get_autoscalex_on() == pa.get_autoscalex_on()
        assert ta.spines["bottom"].get_visible() == pa.spines["bottom"].get_visible()
        assert ta.spines["bottom"].get_bounds() == pa.spines["bottom"].get_bounds()
        np.testing.assert_allclose(
            ta.xaxis.get_majorticklocs(), pa.xaxis.get_majorticklocs()
        )
    plt.close(fig_a)
    plt.close(fig_b)


def test_restore_reattaches_original_shared_tickers():
    fig, axes = plt.subplots(1, 2, sharex=True)
    axes[0].plot([0, 4], [0, 1])
    axes[1].plot([6, 10], [0, 1])
    before = axes[0].xaxis.major
    assert axes[1].xaxis.major is before
    vzs.small_multiples(axes)
    fig.canvas.draw()
    for ax in axes:
        vzs.restore(ax)
    assert axes[0].xaxis.major is before
    assert axes[1].xaxis.major is before
    plt.close(fig)


def test_restore_reinstates_label_text():
    fig, axes = _grid22()
    axes[0, 0].set_ylabel("prior")
    vzs.small_multiples(axes.flat, ylabel="rate")
    for ax in axes.flat:
        vzs.restore(ax)
    assert axes[0, 0].get_ylabel() == "prior"
    plt.close(fig)


def test_log_grid_ticks_are_decades_of_the_union():
    fig, axes = plt.subplots(1, 2)
    for ax, (lo, hi) in zip(axes, [(1, 100), (1000, 100000)], strict=True):
        ax.set_xscale("log")
        ax.plot([lo, hi], [1, 2])
    vzs.small_multiples(axes)
    fig.canvas.draw()
    ticks = axes[0].xaxis.get_majorticklocs()
    exponents = np.log10(ticks)
    np.testing.assert_allclose(exponents, np.round(exponents))
    assert ticks.max() >= 1000  # reaches into the sibling's decades
    plt.close(fig)


def test_date_grid_ticks_span_the_union():
    import datetime as dt

    fig, axes = plt.subplots(1, 2)
    jan = [dt.datetime(2024, 1, 1) + dt.timedelta(days=i) for i in range(0, 60, 6)]
    sep = [dt.datetime(2024, 9, 1) + dt.timedelta(days=i) for i in range(0, 90, 9)]
    axes[0].plot(jan, range(10))
    axes[1].plot(sep, range(10))
    vzs.small_multiples(axes)
    fig.canvas.draw()
    from matplotlib.dates import date2num

    ticks = axes[0].xaxis.get_majorticklocs()
    assert ticks.max() > date2num(dt.datetime(2024, 6, 1))  # beyond own data
    labels = [t.get_text() for t in axes[0].xaxis.get_ticklabels()]
    assert any(labels)  # ConciseDateFormatter still renders
    plt.close(fig)
