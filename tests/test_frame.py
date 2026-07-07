import matplotlib.pyplot as plt
import numpy as np
import pytest

from tufty import tuftify


@pytest.fixture
def scatter_ax():
    fig, ax = plt.subplots()
    rng = np.random.default_rng(0)
    ax.scatter(rng.uniform(0.3, 9.7, 50), rng.uniform(-3.2, 4.1, 50))
    yield ax
    plt.close(fig)


def outermost_ticks(axis):
    dmin, dmax = axis.get_data_interval()
    ticks = [t for t in axis.get_majorticklocs() if dmin <= t <= dmax]
    return min(ticks), max(ticks)


def test_nice_frame_bounds_equal_outermost_ticks(scatter_ax):
    ax = tuftify(scatter_ax)
    ax.figure.canvas.draw()
    assert ax.spines["bottom"].get_bounds() == outermost_ticks(ax.xaxis)
    assert ax.spines["left"].get_bounds() == outermost_ticks(ax.yaxis)


def test_data_frame_bounds_equal_data_extremes(scatter_ax):
    ax = tuftify(scatter_ax, frame="data")
    ax.figure.canvas.draw()
    assert ax.spines["bottom"].get_bounds() == tuple(ax.xaxis.get_data_interval())
    assert ax.spines["left"].get_bounds() == tuple(ax.yaxis.get_data_interval())


def test_top_and_right_spines_hidden(scatter_ax):
    ax = tuftify(scatter_ax)
    assert not ax.spines["top"].get_visible()
    assert not ax.spines["right"].get_visible()


def test_bounds_track_new_data(scatter_ax):
    ax = tuftify(scatter_ax)
    ax.figure.canvas.draw()
    before = ax.spines["bottom"].get_bounds()
    ax.scatter([25.0], [10.0])
    ax.figure.canvas.draw()
    after = ax.spines["bottom"].get_bounds()
    assert after != before
    assert after == outermost_ticks(ax.xaxis)


def test_bounds_survive_resize(scatter_ax):
    ax = tuftify(scatter_ax)
    fig = ax.figure
    fig.canvas.draw()
    fig.set_size_inches(3, 2)
    fig.canvas.draw()
    assert ax.spines["bottom"].get_bounds() == outermost_ticks(ax.xaxis)
    assert ax.spines["left"].get_bounds() == outermost_ticks(ax.yaxis)


def test_bounds_survive_xlim_change(scatter_ax):
    ax = tuftify(scatter_ax)
    ax.figure.canvas.draw()
    ax.set_xlim(-5, 30)
    ax.figure.canvas.draw()
    assert ax.spines["bottom"].get_bounds() == outermost_ticks(ax.xaxis)


def test_histogram():
    fig, ax = plt.subplots()
    ax.hist(np.random.default_rng(1).normal(size=200))
    tuftify(ax)
    fig.canvas.draw()
    assert ax.spines["bottom"].get_bounds() == outermost_ticks(ax.xaxis)
    plt.close(fig)


def test_repeated_calls_keep_one_hook(scatter_ax):
    ax = tuftify(scatter_ax)
    first_cid = ax._tufty_state["cid"]
    tuftify(ax, frame="data")
    assert ax._tufty_state["cid"] == first_cid
    assert ax._tufty_state["frame"] == "data"


def test_invalid_frame_raises(scatter_ax):
    with pytest.raises(ValueError, match="frame"):
        tuftify(scatter_ax, frame="tight")


def test_log_axis_warns_and_is_skipped():
    fig, ax = plt.subplots()
    ax.plot([1, 2, 3], [1, 10, 100])
    ax.set_yscale("log")
    locator_before = ax.yaxis.get_major_locator()
    with pytest.warns(UserWarning, match="y-axis"):
        tuftify(ax)
    assert ax.yaxis.get_major_locator() is locator_before
    fig.canvas.draw()
    plt.close(fig)


def test_categorical_axis_warns_and_is_skipped():
    fig, ax = plt.subplots()
    ax.bar(["a", "b", "c"], [1, 2, 3])
    locator_before = ax.xaxis.get_major_locator()
    with pytest.warns(UserWarning, match="x-axis"):
        tuftify(ax)
    assert ax.xaxis.get_major_locator() is locator_before
    fig.canvas.draw()
    plt.close(fig)


def test_empty_axes_never_raises():
    fig, ax = plt.subplots()
    tuftify(ax)
    fig.canvas.draw()
    plt.close(fig)
