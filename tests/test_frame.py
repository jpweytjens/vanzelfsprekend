import matplotlib.pyplot as plt
import numpy as np
import pytest

from vanzelfsprekend import range_frame


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
    ax = range_frame(scatter_ax)
    ax.figure.canvas.draw()
    assert ax.spines["bottom"].get_bounds() == outermost_ticks(ax.xaxis)
    assert ax.spines["left"].get_bounds() == outermost_ticks(ax.yaxis)


def test_data_frame_bounds_equal_data_extremes(scatter_ax):
    ax = range_frame(scatter_ax, frame="data")
    ax.figure.canvas.draw()
    assert ax.spines["bottom"].get_bounds() == tuple(ax.xaxis.get_data_interval())
    assert ax.spines["left"].get_bounds() == tuple(ax.yaxis.get_data_interval())


def test_top_and_right_spines_hidden(scatter_ax):
    ax = range_frame(scatter_ax)
    assert not ax.spines["top"].get_visible()
    assert not ax.spines["right"].get_visible()


def test_bounds_track_new_data(scatter_ax):
    ax = range_frame(scatter_ax)
    ax.figure.canvas.draw()
    before = ax.spines["bottom"].get_bounds()
    ax.scatter([25.0], [10.0])
    ax.figure.canvas.draw()
    after = ax.spines["bottom"].get_bounds()
    assert after != before
    assert after == outermost_ticks(ax.xaxis)


def test_bounds_survive_resize(scatter_ax):
    ax = range_frame(scatter_ax)
    fig = ax.figure
    fig.canvas.draw()
    fig.set_size_inches(3, 2)
    fig.canvas.draw()
    assert ax.spines["bottom"].get_bounds() == outermost_ticks(ax.xaxis)
    assert ax.spines["left"].get_bounds() == outermost_ticks(ax.yaxis)


def test_bounds_survive_xlim_change(scatter_ax):
    ax = range_frame(scatter_ax)
    ax.figure.canvas.draw()
    ax.set_xlim(-5, 30)
    ax.figure.canvas.draw()
    assert ax.spines["bottom"].get_bounds() == outermost_ticks(ax.xaxis)


def test_histogram():
    fig, ax = plt.subplots()
    ax.hist(np.random.default_rng(1).normal(size=200))
    range_frame(ax)
    fig.canvas.draw()
    assert ax.spines["bottom"].get_bounds() == outermost_ticks(ax.xaxis)
    plt.close(fig)


def test_repeated_calls_keep_one_hook(scatter_ax):
    ax = range_frame(scatter_ax)
    first_cid = ax._vanzelfsprekend_state["cid"]
    range_frame(ax, frame="data")
    assert ax._vanzelfsprekend_state["cid"] == first_cid
    assert ax._vanzelfsprekend_state["frame"]["mode"] == "data"


def test_invalid_frame_raises(scatter_ax):
    with pytest.raises(ValueError, match="frame"):
        range_frame(scatter_ax, frame="tight")


def test_log_axis_warns_and_is_skipped():
    fig, ax = plt.subplots()
    ax.plot([1, 2, 3], [1, 10, 100])
    ax.set_yscale("log")
    locator_before = ax.yaxis.get_major_locator()
    with pytest.warns(UserWarning, match="y-axis"):
        range_frame(ax)
    assert ax.yaxis.get_major_locator() is locator_before
    fig.canvas.draw()
    plt.close(fig)


def test_categorical_axis_warns_and_is_skipped():
    fig, ax = plt.subplots()
    ax.bar(["a", "b", "c"], [1, 2, 3])
    locator_before = ax.xaxis.get_major_locator()
    with pytest.warns(UserWarning, match="x-axis"):
        range_frame(ax)
    assert ax.xaxis.get_major_locator() is locator_before
    fig.canvas.draw()
    plt.close(fig)


def test_empty_axes_never_raises():
    fig, ax = plt.subplots()
    range_frame(ax)
    fig.canvas.draw()
    plt.close(fig)


def test_loose_frame_bounds_contain_data(scatter_ax):
    ax = range_frame(scatter_ax, frame="loose")
    ax.figure.canvas.draw()
    for axis, spine_name in ((ax.xaxis, "bottom"), (ax.yaxis, "left")):
        lo, hi = ax.spines[spine_name].get_bounds()
        dmin, dmax = axis.get_data_interval()
        ticks = axis.get_majorticklocs()
        assert lo <= dmin
        assert hi >= dmax
        assert lo == ticks.min()
        assert hi == ticks.max()


def test_nice_frame_leaves_view_limits_alone():
    fig, ax = plt.subplots()
    rng = np.random.default_rng(0)
    x, y = rng.uniform(0.3, 9.7, 50), rng.uniform(-3.2, 4.1, 50)
    ax.scatter(x, y)
    range_frame(ax)
    fig.canvas.draw()
    pad = 0.05 * (x.max() - x.min())
    assert ax.get_xlim() == pytest.approx((x.min() - pad, x.max() + pad))
    plt.close(fig)


def test_loose_frame_view_equals_tick_span():
    fig, ax = plt.subplots()
    rng = np.random.default_rng(0)
    ax.scatter(rng.uniform(0.3, 9.7, 50), rng.uniform(-3.2, 4.1, 50))
    range_frame(ax, frame="loose")
    fig.canvas.draw()
    for axis, get_lim in ((ax.xaxis, ax.get_xlim), (ax.yaxis, ax.get_ylim)):
        ticks = axis.get_majorticklocs()
        assert get_lim() == pytest.approx((ticks.min(), ticks.max()))
    plt.close(fig)


def test_loose_frame_offsets_spines_outward_by_default(scatter_ax):
    ax = range_frame(scatter_ax, frame="loose")
    assert ax.spines["bottom"].get_position() == ("outward", 8)
    assert ax.spines["left"].get_position() == ("outward", 8)


def test_nice_frame_keeps_spines_in_place(scatter_ax):
    ax = range_frame(scatter_ax)
    assert ax.spines["bottom"].get_position() == ("outward", 0)


def test_explicit_offset_overrides_default(scatter_ax):
    ax = range_frame(scatter_ax, offset=12)
    assert ax.spines["left"].get_position() == ("outward", 12)


def test_one_hook_shared_by_frame_and_labels():
    import vanzelfsprekend as vzs

    fig, ax = plt.subplots()
    rng = np.random.default_rng(0)
    ax.scatter(rng.uniform(0.3, 9.7, 50), rng.uniform(-3.2, 4.1, 50))
    vzs.range_frame(ax)
    vzs.xlabel(ax, "t")
    vzs.ylabel(ax, "v")
    state = ax._vanzelfsprekend_state
    assert set(state["appliers"]) == {"frame", "labels"}
    assert isinstance(state["cid"], int)
    plt.close(fig)


def test_draw_hook_swallows_applier_errors():
    import vanzelfsprekend as vzs
    from vanzelfsprekend import hook

    fig, ax = plt.subplots()
    ax.plot([0, 1], [0, 1])
    vzs.range_frame(ax)

    def boom(_ax):
        raise RuntimeError("applier blew up")

    hook.add_applier(ax, "boom", boom)
    fig.canvas.draw()  # must not raise
    plt.close(fig)
