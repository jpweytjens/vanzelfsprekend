import matplotlib.pyplot as plt
import numpy as np
import pytest

import vanzelfsprekend as vzs
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
