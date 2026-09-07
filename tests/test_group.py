import datetime as dt
import warnings

import matplotlib.pyplot as plt
import numpy as np
import pytest
from matplotlib.dates import ConciseDateFormatter

import vanzelfsprekend as vzs
from vanzelfsprekend.frame import AxisKind
from vanzelfsprekend.group import GroupLocator, axis_kinds


def test_group_locator_computes_ticks_from_union():
    fig, axes = plt.subplots(1, 2)
    axes[0].plot([0, 4], [0, 1])
    axes[1].plot([6, 10], [0, 1])
    vzs.range_frame(axes[0], n=5)
    inner = axes[0].xaxis.get_major_locator()
    axes[0].xaxis.set_major_locator(GroupLocator(inner, list(axes), "x"))
    fig.canvas.draw()
    expected = vzs.TalbotLocator(n=5).tick_values(0, 10)
    np.testing.assert_allclose(axes[0].xaxis.get_majorticklocs(), expected)
    plt.close(fig)


def test_group_locator_falls_back_to_inner_when_union_empty():
    fig, axes = plt.subplots(1, 2)
    vzs.range_frame(axes[0])  # no data anywhere
    inner = axes[0].xaxis.get_major_locator()
    axes[0].xaxis.set_major_locator(GroupLocator(inner, list(axes), "x"))
    fig.canvas.draw()  # must not raise; inner's own fallback path runs
    plt.close(fig)


def test_group_locator_view_limits_cover_the_union():
    # Loose spans of (0, 1) and (10, 11) are (0, 1) and (10, 11); the
    # loose span of their union (0, 11) is (0, 12.5). The group must
    # report the latter, not the panel's own span.
    fig, axes = plt.subplots(1, 2)
    axes[0].plot([0, 1], [0, 1])
    axes[1].plot([10, 11], [0, 1])
    vzs.range_frame(axes[0], frame="loose", n=5)
    inner = axes[0].xaxis.get_major_locator()
    grouped = GroupLocator(inner, list(axes), "x")
    assert grouped.view_limits(0, 1) == (0.0, 12.5)
    assert inner.view_limits(0, 1) == (0.0, 1.0)
    plt.close(fig)


def test_axis_kinds_ignores_members_without_data():
    fig, axes = plt.subplots(1, 2)
    days = [dt.datetime(2024, 1, 1) + dt.timedelta(days=i) for i in range(5)]
    axes[0].plot(days, range(5))
    assert axis_kinds(list(axes), "x") == {AxisKind("linear", True, True)}
    plt.close(fig)


def test_axis_kinds_reports_a_real_disagreement():
    fig, axes = plt.subplots(1, 2)
    days = [dt.datetime(2024, 1, 1) + dt.timedelta(days=i) for i in range(5)]
    axes[0].plot(days, range(5))
    axes[1].plot(range(5), range(5))
    assert axis_kinds(list(axes), "x") == {
        AxisKind("linear", True, True),
        AxisKind("linear", False, True),
    }
    plt.close(fig)


def test_axis_kinds_falls_back_to_all_members_when_none_has_data():
    fig, axes = plt.subplots(1, 2)
    assert axis_kinds(list(axes), "x") == {AxisKind("linear", False, True)}
    plt.close(fig)


def _pair(sharey=True):
    fig, (a, b) = plt.subplots(1, 2, sharey=sharey)
    a.plot([0, 1, 2], [0, 1, 3])
    b.plot([0, 1, 2], [0, 2, 5])
    return fig, a, b


def _ticks_on_spine(ax, name):
    axis = ax.yaxis if name == "y" else ax.xaxis
    spine = ax.spines["left" if name == "y" else "bottom"]
    lo, hi = spine.get_bounds()
    return all(lo - 1e-9 <= t <= hi + 1e-9 for t in axis.get_majorticklocs())


def test_sharey_pair_puts_every_tick_on_the_spine():
    fig, a, b = _pair()
    vzs.distill(a)
    fig.canvas.draw()
    assert _ticks_on_spine(a, "y")
    assert _ticks_on_spine(b, "y")
    assert a.spines["left"].get_bounds() == b.spines["left"].get_bounds()
    assert hasattr(b, "_vanzelfsprekend_state")
    plt.close(fig)


def test_entry_axes_does_not_matter():
    def bounds(entry):
        fig, a, b = _pair()
        vzs.distill(b if entry == "b" else a)
        fig.canvas.draw()
        out = (
            tuple(a.yaxis.get_majorticklocs()),
            a.spines["left"].get_bounds(),
            tuple(b.yaxis.get_majorticklocs()),
            b.spines["left"].get_bounds(),
        )
        plt.close(fig)
        return out

    assert bounds("a") == bounds("b")


def test_restore_returns_the_shared_ticker_original():
    fig, a, b = _pair()
    original = a.yaxis.get_major_locator()
    assert b.yaxis.get_major_locator() is original
    vzs.distill(a)
    fig.canvas.draw()
    vzs.restore(a)
    assert a.yaxis.get_major_locator() is original
    assert b.yaxis.get_major_locator() is original
    assert not hasattr(b, "_vanzelfsprekend_state")
    vzs.restore(b)  # no state left: a no-op
    plt.close(fig)


def test_later_call_updates_the_group():
    fig, a, b = _pair()
    vzs.distill(a)
    fig.canvas.draw()
    vzs.distill(b, frame="data")
    fig.canvas.draw()
    assert a.spines["left"].get_bounds() == (0.0, 5.0)
    assert b.spines["left"].get_bounds() == (0.0, 5.0)
    plt.close(fig)


def test_col_row_sharing_is_one_unit_with_two_scopes():
    fig, axes = plt.subplots(2, 2, sharex="col", sharey="row")
    spans = {(0, 0): (0, 1), (0, 1): (2, 5), (1, 0): (-3, 0), (1, 1): (4, 9)}
    for (r, c), (lo, hi) in spans.items():
        axes[r, c].plot([lo, hi], [lo, hi])
    vzs.distill(axes[0, 0])
    fig.canvas.draw()
    assert all(hasattr(ax, "_vanzelfsprekend_state") for ax in axes.flat)
    for c in range(2):
        assert (
            axes[0, c].spines["bottom"].get_bounds()
            == axes[1, c].spines["bottom"].get_bounds()
        )
    for r in range(2):
        assert (
            axes[r, 0].spines["left"].get_bounds()
            == axes[r, 1].spines["left"].get_bounds()
        )
    assert (
        axes[0, 0].spines["bottom"].get_bounds()
        != axes[0, 1].spines["bottom"].get_bounds()
    )
    plt.close(fig)


def test_one_plumbing_small_multiples_matches_shared_distill():
    def draw(shared):
        fig, axes = plt.subplots(2, 2, sharex=shared, sharey=shared)
        for ax, (lo, hi) in zip(
            axes.flat, [(0, 1), (2, 5), (-3, 0), (4, 9)], strict=True
        ):
            ax.plot([lo, hi], [lo, hi])
        if shared:
            vzs.distill(axes[0, 0])
        else:
            vzs.small_multiples(axes.flat)
        fig.canvas.draw()
        out = [
            (
                tuple(ax.xaxis.get_majorticklocs()),
                tuple(ax.yaxis.get_majorticklocs()),
                ax.spines["bottom"].get_bounds(),
                ax.spines["left"].get_bounds(),
            )
            for ax in axes.flat
        ]
        plt.close(fig)
        return out

    assert draw(shared=True) == draw(shared=False)


def test_loose_shared_pair_autoscales_to_the_union_span():
    fig, (a, b) = plt.subplots(1, 2, sharex=True)
    a.plot([0, 1], [0, 1])
    b.plot([10, 11], [0, 1])
    vzs.distill(a, frame="loose", n=5)
    fig.canvas.draw()
    assert a.get_xlim() == (0.0, 12.5)
    assert b.get_xlim() == (0.0, 12.5)
    fig.canvas.draw()
    assert a.get_xlim() == (0.0, 12.5)
    plt.close(fig)


def test_loose_compare_grid_autoscales_to_the_union_span():
    fig, (a, b) = plt.subplots(1, 2)
    a.plot([0, 1], [0, 1])
    b.plot([10, 11], [0, 1])
    vzs.small_multiples((a, b), frame="loose", n=5)
    fig.canvas.draw()
    assert a.get_xlim() == (0.0, 12.5)
    assert b.get_xlim() == (0.0, 12.5)
    fig.canvas.draw()
    assert a.get_xlim() == (0.0, 12.5)
    plt.close(fig)


def test_empty_sibling_follows_the_date_kind():
    fig, (a, b) = plt.subplots(1, 2, sharex=True)
    days = [dt.datetime(2024, 1, 1) + dt.timedelta(days=i) for i in range(5)]
    a.plot(days, range(5))
    with warnings.catch_warnings(record=True) as record:
        warnings.simplefilter("always")
        vzs.distill(b)  # the empty one installs last
        fig.canvas.draw()
    assert not [w for w in record if "vanzelfsprekend" in str(w.message)]
    assert isinstance(a.xaxis.get_major_locator(), GroupLocator)
    assert isinstance(a.xaxis.get_major_formatter(), ConciseDateFormatter)
    assert a.xaxis.get_major_locator() is b.xaxis.get_major_locator()
    plt.close(fig)


def test_shared_axis_that_mixes_dates_and_floats_warns_and_is_left_alone():
    fig, (a, b) = plt.subplots(1, 2, sharex=True)
    days = [dt.datetime(2024, 1, 1) + dt.timedelta(days=i) for i in range(5)]
    a.plot(days, range(5))
    b.plot(range(5), range(5))
    with pytest.warns(UserWarning, match="shared x-axis") as record:
        vzs.distill(a)
    assert len(record) == 1
    fig.canvas.draw()
    assert a.spines["bottom"].get_bounds() is None
    assert b.spines["bottom"].get_bounds() is None
    assert a.spines["left"].get_bounds() is not None
    plt.close(fig)


def test_twin_is_left_out_of_the_group_with_a_warning():
    fig, host = plt.subplots()
    host.plot([0, 1, 2], [0, 1, 3])
    twin = host.twinx()
    twin.plot([0, 1, 2], [100, 300, 200])
    twin_y_locator = twin.yaxis.get_major_locator()
    shared_x_original = host.xaxis.get_major_locator()
    assert twin.xaxis.get_major_locator() is shared_x_original
    with pytest.warns(UserWarning, match="twin") as record:
        vzs.distill(host)
    assert len(record) == 1
    fig.canvas.draw()
    # The twin owns its y axis and its spines; those are untouched.
    assert twin.yaxis.get_major_locator() is twin_y_locator
    assert all(spine.get_visible() for spine in twin.spines.values())
    assert not hasattr(twin, "_vanzelfsprekend_state")
    # The twin's x axis is the host's x axis: one shared Ticker.
    assert twin.xaxis.get_major_locator() is host.xaxis.get_major_locator()
    # The twin's y data stays out of the host's y frame.
    assert host.spines["left"].get_bounds()[1] <= 3.0
    vzs.restore(host)
    assert twin.xaxis.get_major_locator() is shared_x_original
    plt.close(fig)


def test_unsupported_scale_warns_at_the_call_site_for_every_entry_point():
    # Pointing at the call site is also what keeps Python's default
    # filter from collapsing every panel's warning into one.
    fig, axes = plt.subplots(1, 3)
    for ax in axes:
        ax.set_yscale("symlog")
        ax.plot([1, 2, 3], [1, 20, 300])
    with warnings.catch_warnings(record=True) as record:
        warnings.simplefilter("always")
        vzs.range_frame(axes[0])
        vzs.distill(axes[1])
        vzs.small_multiples([axes[2]])
    assert len(record) == 3
    assert [w.filename for w in record] == [__file__] * 3
    plt.close(fig)


def test_group_locator_targets_the_narrowest_member():
    fig, axes = plt.subplots(1, 2, figsize=(8, 3), gridspec_kw={"width_ratios": [5, 1]})
    axes[0].plot([0, 4], [0, 1])
    axes[1].plot([6, 10], [0, 1])
    vzs.range_frame(axes[0])
    inner = axes[0].xaxis.get_major_locator()
    axes[0].xaxis.set_major_locator(GroupLocator(inner, list(axes), "x"))
    fig.canvas.draw()
    expected = inner.tick_values(0, 10, n=inner.target(axes[1].xaxis))
    np.testing.assert_allclose(axes[0].xaxis.get_majorticklocs(), expected)
    plt.close(fig)


def test_loose_unequal_pair_view_matches_its_ticks():
    fig, axes = plt.subplots(
        1, 2, figsize=(8, 3), sharex=True, gridspec_kw={"width_ratios": [5, 1]}
    )
    axes[0].plot([0.3, 4.1], [0, 1])
    axes[1].plot([6.2, 9.7], [0, 1])
    vzs.distill(axes[0], frame="loose")
    fig.canvas.draw()
    for ax in axes:
        ticks = ax.xaxis.get_majorticklocs()
        assert tuple(ax.get_xlim()) == (ticks[0], ticks[-1])
    plt.close(fig)


def test_cropped_shared_view_trims_the_union_to_the_visible_data():
    fig, a, b = _pair()
    vzs.distill(a, frame="data")
    a.set_ylim(1.5, 10.0)
    fig.canvas.draw()
    assert a.spines["left"].get_bounds() == (1.5, 5.0)
    assert b.spines["left"].get_bounds() == (1.5, 5.0)
    assert a.yaxis.get_majorticklocs().min() >= 1.5
    plt.close(fig)
