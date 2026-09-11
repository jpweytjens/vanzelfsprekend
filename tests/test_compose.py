import datetime as dt

import matplotlib.pyplot as plt
import numpy as np
import pytest
from matplotlib.colors import to_rgba

import vanzelfsprekend as vzs
from vanzelfsprekend.hook import get_state


def test_import_installs_accessor():
    # A subprocess with a fresh import: other tests unregister/re-register
    # on the shared Axes class, so assert the import-time install in isolation.
    import subprocess
    import sys

    subprocess.run(
        [
            sys.executable,
            "-c",
            "import vanzelfsprekend; from matplotlib.axes import Axes;"
            " assert hasattr(Axes, 'vzs')",
        ],
        check=True,
    )


def test_register_adds_working_accessor_and_is_reentrant():
    vzs.register()
    vzs.register()
    fig, ax = plt.subplots()
    ax.plot([1, 2, 3], [3, 1, 2])
    nice = [1, 2.5, 5]
    result = ax.vzs.apply(frame="data", offset=5, nice_numbers=nice)
    assert result is ax
    assert not ax.spines["top"].get_visible()
    assert ax.spines["bottom"].get_position() == ("outward", 5)
    fig.canvas.draw()
    assert ax.spines["bottom"].get_bounds() == tuple(ax.xaxis.get_data_interval())
    expected = vzs.TalbotLocator(nice_numbers=nice).tick_values(
        *ax.xaxis.get_data_interval()
    )
    np.testing.assert_allclose(ax.xaxis.get_majorticklocs(), expected)
    plt.close(fig)


def test_apply_matches_range_frame_bounds():
    fig, ax = plt.subplots()
    rng = np.random.default_rng(0)
    x, y = rng.uniform(0.3, 9.7, 50), rng.uniform(-3.2, 4.1, 50)
    ax.scatter(x, y)
    vzs.apply(ax)
    fig.canvas.draw()
    bottom = ax.spines["bottom"].get_bounds()

    fig2, ax2 = plt.subplots()
    ax2.scatter(x, y)
    vzs.range_frame(ax2)
    fig2.canvas.draw()
    assert bottom == ax2.spines["bottom"].get_bounds()
    plt.close(fig)
    plt.close(fig2)


def test_apply_is_range_frame_then_mute():
    fig, ax = plt.subplots()
    ax.plot([0, 1, 2], [0, 1, 4])
    vzs.apply(ax)
    fig.canvas.draw()

    fig2, ax2 = plt.subplots()
    ax2.plot([0, 1, 2], [0, 1, 4])
    vzs.range_frame(ax2)
    vzs.mute(ax2)
    fig2.canvas.draw()

    for side in ("bottom", "left"):
        assert ax.spines[side].get_bounds() == ax2.spines[side].get_bounds()
        assert ax.spines[side].get_edgecolor() == ax2.spines[side].get_edgecolor()
    (line,) = ax.plot([0, 1], [0, 1])
    (line2,) = ax2.plot([0, 1], [0, 1])
    assert to_rgba(line.get_color()) == to_rgba(line2.get_color())
    assert not hasattr(vzs, "distill")
    plt.close(fig)
    plt.close(fig2)


def _snapshot(ax):
    return {
        "xloc": ax.xaxis.get_major_locator(),
        "yloc": ax.yaxis.get_major_locator(),
        "top": ax.spines["top"].get_visible(),
        "right": ax.spines["right"].get_visible(),
        "left_pos": ax.spines["left"].get_position(),
        "bottom_pos": ax.spines["bottom"].get_position(),
        "xlabel_ha": ax.xaxis.label.get_horizontalalignment(),
        "ylabel_rot": ax.yaxis.label.get_rotation(),
    }


def test_restore_reverts_to_prior_state():
    fig, ax = plt.subplots()
    rng = np.random.default_rng(0)
    ax.scatter(rng.uniform(0.3, 9.7, 50), rng.uniform(-3.2, 4.1, 50))
    before = _snapshot(ax)

    vzs.range_frame(ax)
    vzs.xlabel(ax, "t")
    vzs.ylabel(ax, "v")
    fig.canvas.draw()

    vzs.restore(ax)
    after = _snapshot(ax)

    assert after["xloc"] is before["xloc"]
    assert after["yloc"] is before["yloc"]
    assert after["top"] == before["top"] is True
    assert after["right"] == before["right"] is True
    assert after["left_pos"] == before["left_pos"]
    assert after["bottom_pos"] == before["bottom_pos"]
    assert after["xlabel_ha"] == before["xlabel_ha"]
    assert after["ylabel_rot"] == before["ylabel_rot"]
    assert not hasattr(ax, "_vanzelfsprekend_state")
    plt.close(fig)


def test_restore_disconnects_hook():
    fig, ax = plt.subplots()
    rng = np.random.default_rng(0)
    ax.scatter(rng.uniform(0.3, 9.7, 50), rng.uniform(-3.2, 4.1, 50))
    vzs.range_frame(ax)
    fig.canvas.draw()
    vzs.restore(ax)
    # With the hook gone, the left spine is no longer re-trimmed to the data.
    ax.spines["left"].set_bounds(0.0, 1.0)
    ax.set_ylim(-20, 20)
    fig.canvas.draw()
    assert ax.spines["left"].get_bounds() == (0.0, 1.0)
    plt.close(fig)


def test_restore_reinstates_date_locator_and_formatter():
    import datetime as dt

    fig, ax = plt.subplots()
    days = [dt.datetime(2023, 2, 14) + dt.timedelta(days=20 * i) for i in range(32)]
    ax.plot(days, range(32))
    locator_before = ax.xaxis.get_major_locator()
    formatter_before = ax.xaxis.get_major_formatter()
    vzs.range_frame(ax)
    fig.canvas.draw()
    vzs.restore(ax)
    assert ax.xaxis.get_major_locator() is locator_before
    assert ax.xaxis.get_major_formatter() is formatter_before
    plt.close(fig)


def test_restore_on_untouched_axes_is_noop():
    fig, ax = plt.subplots()
    ax.plot([0, 1], [0, 1])
    vzs.restore(ax)  # must not raise
    plt.close(fig)


def test_unregister_removes_accessor_and_is_reentrant():
    vzs.register()
    from matplotlib.axes import Axes

    assert hasattr(Axes, "vzs")
    vzs.unregister()
    vzs.unregister()
    assert not hasattr(Axes, "vzs")


def test_restore_via_accessor():
    vzs.register()
    fig, ax = plt.subplots()
    ax.plot([1, 2, 3], [3, 1, 2])
    ax.vzs.apply()
    fig.canvas.draw()
    ax.vzs.restore()
    assert not hasattr(ax, "_vanzelfsprekend_state")
    vzs.unregister()
    plt.close(fig)


# The accessor mimics matplotlib's method names where a matching contract
# exists; everything else keeps its module name.
ACCESSOR_NAMES = {"xlabel": "set_xlabel", "ylabel": "set_ylabel"}


def _ax_first_entry_points():
    import inspect

    for name in vzs.__all__:
        obj = getattr(vzs, name)
        if not callable(obj) or inspect.isclass(obj):
            continue
        params = list(inspect.signature(obj).parameters)
        if params and params[0] == "ax":
            yield name, obj


def test_accessor_covers_every_ax_first_entry_point():
    from vanzelfsprekend.compose import _Accessor

    for name, _func in _ax_first_entry_points():
        assert hasattr(_Accessor, ACCESSOR_NAMES.get(name, name))


def test_accessor_signatures_match_module_functions():
    import inspect

    from vanzelfsprekend.compose import _Accessor

    for name, func in _ax_first_entry_points():
        method = getattr(_Accessor, ACCESSOR_NAMES.get(name, name))
        func_params = list(inspect.signature(func).parameters.values())[1:]
        method_params = list(inspect.signature(method).parameters.values())[1:]
        assert method_params == func_params, name


def test_restore_after_repeated_range_frame_restores_original_locator():
    fig, ax = plt.subplots()
    rng = np.random.default_rng(0)
    ax.scatter(rng.uniform(0.3, 9.7, 50), rng.uniform(-3.2, 4.1, 50))
    original = ax.xaxis.get_major_locator()
    vzs.range_frame(ax)
    vzs.range_frame(ax, frame="data")
    fig.canvas.draw()
    vzs.restore(ax)
    assert ax.xaxis.get_major_locator() is original
    plt.close(fig)


def test_apply_mutes_and_installs_ink_cycle():
    fig, ax = plt.subplots()
    vzs.apply(ax)
    (first,) = ax.plot([0, 1], [0, 1])
    (second,) = ax.plot([0, 1], [1, 0])
    assert to_rgba(first.get_color()) == to_rgba(vzs.palettes.DATA_INK)
    assert to_rgba(second.get_color()) == to_rgba(vzs.palettes.DATA_INK)
    assert ax.spines["left"].get_edgecolor() == to_rgba(vzs.palettes.LINE_INK)
    plt.close(fig)


def test_restore_reinstates_prior_cycle():
    fig, ax = plt.subplots()
    vzs.apply(ax)
    vzs.restore(ax)
    (line,) = ax.plot([0, 1], [0, 1])
    assert to_rgba(line.get_color()) == to_rgba("#1f77b4")  # matplotlib's default C0
    plt.close(fig)


def test_apply_before_plotting_frames_the_data_on_draw():
    fig, ax = plt.subplots()
    vzs.apply(ax)
    ax.plot([1, 2, 3], [3, 1, 2])
    fig.canvas.draw()
    assert ax.spines["bottom"].get_bounds() == (1.0, 3.0)
    plt.close(fig)


def test_restore_reinstates_minor_locators():
    fig, ax = plt.subplots()
    ax.set_yscale("log")
    ax.plot([1, 2, 3], [3, 40, 700])
    minor_before = ax.yaxis.get_minor_locator()
    vzs.apply(ax)
    vzs.restore(ax)
    assert ax.yaxis.get_minor_locator() is minor_before
    plt.close(fig)


def test_restore_clears_spine_bounds():
    fig, ax = plt.subplots()
    ax.plot([0, 1], [0, 1])
    vzs.apply(ax)
    fig.canvas.draw()
    vzs.restore(ax)
    assert ax.spines["left"].get_bounds() is None
    assert ax.spines["bottom"].get_bounds() is None
    plt.close(fig)


def test_apply_leaves_a_lone_inverted_axis_inverted():
    fig, ax = plt.subplots()
    ax.plot([0, 1], [0, 1])
    ax.invert_yaxis()
    vzs.apply(ax)
    fig.canvas.draw()
    lo, hi = ax.get_ylim()
    assert lo > hi
    plt.close(fig)


def test_apply_loose_frame_view_equals_tick_span():
    fig, ax = plt.subplots()
    rng = np.random.default_rng(0)
    ax.scatter(rng.uniform(0.3, 9.7, 50), rng.uniform(-3.2, 4.1, 50))
    vzs.apply(ax, frame="loose")
    fig.canvas.draw()
    for axis, get_lim in ((ax.xaxis, ax.get_xlim), (ax.yaxis, ax.get_ylim)):
        ticks = axis.get_majorticklocs()
        assert get_lim() == pytest.approx((ticks.min(), ticks.max()))
    plt.close(fig)


def _plot_linear(ax):
    ax.plot([0.3, 4.5, 9.7], [-3.2, 1.0, 4.1])


def _plot_log(ax):
    ax.set_yscale("log")
    ax.plot([1, 2, 3], [3, 40, 700])


def _plot_dates(ax):
    days = [dt.datetime(2024, 1, 1) + dt.timedelta(days=30 * i) for i in range(4)]
    ax.plot(days, [1.0, 4.0, 2.0, 3.5])


@pytest.mark.parametrize("plot", [_plot_linear, _plot_log, _plot_dates])
@pytest.mark.parametrize("frame", ["nice", "data", "loose"])
def test_apply_frames_a_lone_axes_exactly_as_range_frame(plot, frame):
    # mute must not disturb the frame: same spines, same view, on every scale and mode.
    fig_applied, applied = plt.subplots()
    fig_framed, framed = plt.subplots()
    for ax in (applied, framed):
        plot(ax)
    vzs.apply(applied, frame=frame)
    vzs.range_frame(framed, frame=frame)
    fig_applied.canvas.draw()
    fig_framed.canvas.draw()
    for side in ("bottom", "left"):
        assert applied.spines[side].get_bounds() == framed.spines[side].get_bounds()
    assert applied.get_xlim() == framed.get_xlim()
    assert applied.get_ylim() == framed.get_ylim()
    plt.close(fig_applied)
    plt.close(fig_framed)


def test_only_the_shared_axis_is_pinned_to_a_group():
    fig, (upper, lower) = plt.subplots(2, 1, sharey=True)
    upper.plot([0, 1], [0, 1])
    lower.plot([0, 2], [0, 4])
    lower.set_autoscaley_on(False)
    before_autoscale = [
        (ax.get_autoscalex_on(), ax.get_autoscaley_on()) for ax in (upper, lower)
    ]
    before_xlim = (upper.get_xlim(), lower.get_xlim())
    vzs.apply(upper)
    assert set(get_state(upper)["group"]["members"]) == {"y"}
    fig.canvas.draw()
    vzs.restore(upper)
    assert [
        (ax.get_autoscalex_on(), ax.get_autoscaley_on()) for ax in (upper, lower)
    ] == before_autoscale
    assert (upper.get_xlim(), lower.get_xlim()) == before_xlim
    plt.close(fig)


def test_apply_on_a_grid_panel_updates_the_whole_grid():
    fig, axes = plt.subplots(2, 2)
    for ax, (lo, hi) in zip(axes.flat, [(0, 1), (2, 5), (-3, 0), (4, 9)], strict=True):
        ax.plot([lo, hi], [lo, hi])
    vzs.small_multiples(axes.flat)
    fig.canvas.draw()
    vzs.apply(axes[0, 0], frame="data")
    fig.canvas.draw()
    for ax in axes.flat:
        assert ax.spines["left"].get_bounds() == (-3.0, 9.0)
    vzs.restore(axes[1, 1])
    assert not any(hasattr(ax, "_vanzelfsprekend_state") for ax in axes.flat)
    plt.close(fig)


@pytest.mark.parametrize(
    "entry",
    [
        lambda ax, **kw: vzs.apply(ax, **kw),
        lambda ax, **kw: ax.vzs.apply(**kw),
        lambda ax, **kw: ax.vzs.range_frame(**kw),
    ],
)
def test_spacing_reaches_the_locator_from_every_entry_point(entry):
    vzs.register()
    counts = []
    for spacing in (2, 14):
        fig, ax = plt.subplots(figsize=(6, 3))
        ax.plot([0, 100], [0, 100])
        entry(ax, spacing=spacing)
        fig.canvas.draw()
        counts.append(len(ax.xaxis.get_majorticklocs()))
        plt.close(fig)
    assert counts[1] < counts[0]


def test_apply_keeps_a_cycle_set_before_it():
    fig, ax = plt.subplots()
    ax.set_prop_cycle(color=["#4477AA", "#EE6677"])
    vzs.apply(ax)
    (first,) = ax.plot([0, 1], [0, 1])
    (second,) = ax.plot([0, 1], [1, 0])
    assert to_rgba(first.get_color()) == to_rgba("#4477AA")
    assert to_rgba(second.get_color()) == to_rgba("#EE6677")
    plt.close(fig)


def test_restore_returns_the_cycle_set_before_apply():
    fig, ax = plt.subplots()
    ax.set_prop_cycle(color=["#4477AA", "#EE6677"])
    vzs.apply(ax)
    vzs.restore(ax)
    (line,) = ax.plot([0, 1], [0, 1])
    assert to_rgba(line.get_color()) == to_rgba("#4477AA")
    plt.close(fig)


def test_range_frame_alone_leaves_ink_and_cycle_alone():
    fig, ax = plt.subplots()
    ax.plot([0, 1, 2], [0, 1, 4])
    vzs.range_frame(ax)
    fig.canvas.draw()
    (line,) = ax.plot([0, 1], [0, 1])
    assert to_rgba(line.get_color()) == to_rgba("#ff7f0e")  # matplotlib's default C1
    assert ax.spines["left"].get_edgecolor() == to_rgba("black")
    plt.close(fig)
