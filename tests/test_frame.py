import datetime as dt

import matplotlib.pyplot as plt
import numpy as np
import pytest

import vanzelfsprekend as vzs
from vanzelfsprekend import range_frame
from vanzelfsprekend.hook import get_state


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
    assert ax._vanzelfsprekend_state["frame"]["mode"] == {"x": "data", "y": "data"}


def test_invalid_frame_raises(scatter_ax):
    with pytest.raises(ValueError, match="frame"):
        range_frame(scatter_ax, frame="tight")


def test_mixed_frame_modes_per_spine(scatter_ax):
    ax = range_frame(scatter_ax, frame=("data", "nice"))
    ax.figure.canvas.draw()
    assert ax.spines["bottom"].get_bounds() == tuple(ax.xaxis.get_data_interval())
    assert ax.spines["left"].get_bounds() == outermost_ticks(ax.yaxis)


def test_loose_in_tuple_offsets_only_that_spine(scatter_ax):
    ax = range_frame(scatter_ax, frame=("loose", "nice"))
    assert ax.spines["bottom"].get_position() == ("outward", 8)
    assert ax.spines["left"].get_position() == ("outward", 0)


def test_loose_in_tuple_bounds_only_that_axis(scatter_ax):
    ax = range_frame(scatter_ax, frame=("loose", "nice"))
    ax.figure.canvas.draw()
    xlo, xhi = ax.spines["bottom"].get_bounds()
    dmin, dmax = ax.xaxis.get_data_interval()
    assert xlo <= dmin
    assert xhi >= dmax
    assert ax.spines["left"].get_bounds() == outermost_ticks(ax.yaxis)


@pytest.mark.parametrize("frame", [("nice", "tight"), ("nice",), ("nice",) * 3])
def test_invalid_frame_tuple_raises(scatter_ax, frame):
    with pytest.raises(ValueError, match="frame"):
        range_frame(scatter_ax, frame=frame)


@pytest.fixture
def log_scatter_ax():
    fig, ax = plt.subplots()
    ax.set_xscale("log")
    ax.set_yscale("log")
    rng = np.random.default_rng(0)
    x = 10 ** rng.uniform(0.5, 3.5, 50)
    ax.scatter(x, 3 * x**0.8)
    yield ax
    plt.close(fig)


def test_log_axis_gets_log_locator_without_warning(log_scatter_ax):
    import warnings

    from vanzelfsprekend import LogBreaksLocator

    with warnings.catch_warnings():
        warnings.simplefilter("error")
        range_frame(log_scatter_ax)
    assert isinstance(log_scatter_ax.xaxis.get_major_locator(), LogBreaksLocator)
    assert isinstance(log_scatter_ax.yaxis.get_major_locator(), LogBreaksLocator)


def test_log_axis_minor_ticks_hidden(log_scatter_ax):
    from matplotlib.ticker import NullLocator

    range_frame(log_scatter_ax)
    assert isinstance(log_scatter_ax.xaxis.get_minor_locator(), NullLocator)
    assert isinstance(log_scatter_ax.yaxis.get_minor_locator(), NullLocator)


def test_linear_axis_minor_locator_untouched(scatter_ax):
    before = scatter_ax.xaxis.get_minor_locator()
    range_frame(scatter_ax)
    assert scatter_ax.xaxis.get_minor_locator() is before


def test_log_nice_frame_bounds_equal_outermost_ticks(log_scatter_ax):
    ax = range_frame(log_scatter_ax)
    ax.figure.canvas.draw()
    assert ax.spines["bottom"].get_bounds() == outermost_ticks(ax.xaxis)
    assert ax.spines["left"].get_bounds() == outermost_ticks(ax.yaxis)


def test_log_loose_frame_bounds_contain_data(log_scatter_ax):
    ax = range_frame(log_scatter_ax, frame="loose")
    ax.figure.canvas.draw()
    for axis, spine_name in ((ax.xaxis, "bottom"), (ax.yaxis, "left")):
        lo, hi = ax.spines[spine_name].get_bounds()
        dmin, dmax = axis.get_data_interval()
        assert lo <= dmin
        assert hi >= dmax


def test_log_base_two_axis_uses_base_two_breaks(log_scatter_ax):
    log_scatter_ax.set_xscale("log", base=2)
    range_frame(log_scatter_ax)
    log_scatter_ax.figure.canvas.draw()
    ticks = log_scatter_ax.xaxis.get_majorticklocs()
    assert len(ticks) > 0
    assert np.allclose(np.log2(ticks), np.round(np.log2(ticks)))


def test_symlog_axis_warns_and_is_skipped():
    fig, ax = plt.subplots()
    ax.plot([1, 2, 3], [-50, 0, 2000])
    ax.set_yscale("symlog")
    locator_before = ax.yaxis.get_major_locator()
    with pytest.warns(UserWarning, match="y-axis"):
        range_frame(ax)
    assert ax.yaxis.get_major_locator() is locator_before
    fig.canvas.draw()
    plt.close(fig)


def test_log_axis_with_nonpositive_data_does_not_raise():
    fig, ax = plt.subplots()
    ax.plot([1, 2, 3], [-1, 10, 100])
    ax.set_yscale("log")
    range_frame(ax)
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


@pytest.fixture
def date_plot_ax():
    fig, ax = plt.subplots()
    days = [dt.datetime(2023, 2, 14) + dt.timedelta(days=20 * i) for i in range(32)]
    ax.plot(days, range(32))
    yield ax
    plt.close(fig)


def test_date_axis_gets_date_locator_and_concise_formatter(date_plot_ax):
    import warnings

    from matplotlib.dates import ConciseDateFormatter

    from vanzelfsprekend import DateBreaksLocator

    with warnings.catch_warnings():
        warnings.simplefilter("error", UserWarning)
        range_frame(date_plot_ax)
    assert isinstance(date_plot_ax.xaxis.get_major_locator(), DateBreaksLocator)
    assert isinstance(date_plot_ax.xaxis.get_major_formatter(), ConciseDateFormatter)


def test_date_frame_bounds_equal_outermost_ticks(date_plot_ax):
    ax = range_frame(date_plot_ax)
    ax.figure.canvas.draw()
    assert ax.spines["bottom"].get_bounds() == outermost_ticks(ax.xaxis)


def test_date_loose_frame_bounds_contain_data(date_plot_ax):
    ax = range_frame(date_plot_ax, frame="loose")
    ax.figure.canvas.draw()
    lo, hi = ax.spines["bottom"].get_bounds()
    dmin, dmax = ax.xaxis.get_data_interval()
    assert lo <= dmin
    assert hi >= dmax


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


def _framed_ax(frame):
    fig, ax = plt.subplots()
    ax.plot([0, 10], [0, 10])
    vzs.range_frame(ax, frame=frame)
    return fig, ax


def test_frame_span_interval_override_data_mode():
    fig, ax = _framed_ax("data")
    get_state(ax)["frame"]["intervals"] = {"x": lambda: (2.0, 3.0)}
    fig.canvas.draw()
    assert ax.spines["bottom"].get_bounds() == (2.0, 3.0)
    plt.close(fig)


def test_frame_span_interval_override_nice_mode():
    fig, ax = _framed_ax("nice")
    get_state(ax)["frame"]["intervals"] = {"x": lambda: (1.5, 8.5)}
    fig.canvas.draw()
    ticks = [t for t in ax.xaxis.get_majorticklocs() if 1.5 <= t <= 8.5]
    assert ax.spines["bottom"].get_bounds() == (min(ticks), max(ticks))
    plt.close(fig)


def test_frame_span_interval_override_loose_mode():
    fig, ax = _framed_ax("loose")
    get_state(ax)["frame"]["intervals"] = {"x": lambda: (3.1, 6.9)}
    fig.canvas.draw()
    ticks = sorted(ax.xaxis.get_majorticklocs())
    lo = max(t for t in ticks if t <= 3.1)
    hi = min(t for t in ticks if t >= 6.9)
    assert ax.spines["bottom"].get_bounds() == (lo, hi)
    plt.close(fig)


def test_frame_span_override_returning_none_leaves_panel_local_trim():
    fig, ax = _framed_ax("data")
    get_state(ax)["frame"]["intervals"] = {"x": lambda: None}
    fig.canvas.draw()
    assert ax.spines["bottom"].get_bounds() == tuple(ax.xaxis.get_data_interval())
    plt.close(fig)


def test_frame_span_loose_interval_with_no_ticks_does_not_raise():
    from matplotlib.ticker import NullLocator

    fig, ax = _framed_ax("loose")
    ax.xaxis.set_major_locator(NullLocator())
    get_state(ax)["frame"]["intervals"] = {"x": lambda: (3.1, 6.9)}
    fig.canvas.draw()  # must not raise
    plt.close(fig)
