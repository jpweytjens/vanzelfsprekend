import matplotlib.pyplot as plt
import numpy as np
from matplotlib.colors import to_rgba

import vanzelfsprekend as vzs


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
    result = ax.vzs.distill(frame="data", offset=5, nice_numbers=nice)
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


def test_distill_matches_range_frame_bounds():
    fig, ax = plt.subplots()
    rng = np.random.default_rng(0)
    x, y = rng.uniform(0.3, 9.7, 50), rng.uniform(-3.2, 4.1, 50)
    ax.scatter(x, y)
    vzs.distill(ax)
    fig.canvas.draw()
    bottom = ax.spines["bottom"].get_bounds()

    fig2, ax2 = plt.subplots()
    ax2.scatter(x, y)
    vzs.range_frame(ax2)
    fig2.canvas.draw()
    assert bottom == ax2.spines["bottom"].get_bounds()
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
    ax.vzs.distill()
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


def test_distill_mutes_and_installs_ink_cycle():
    fig, ax = plt.subplots()
    vzs.distill(ax)
    (first,) = ax.plot([0, 1], [0, 1])
    (second,) = ax.plot([0, 1], [1, 0])
    assert to_rgba(first.get_color()) == to_rgba(vzs.palettes.DATA_INK)
    assert to_rgba(second.get_color()) == to_rgba(vzs.palettes.DATA_INK)
    assert ax.spines["left"].get_edgecolor() == to_rgba(vzs.palettes.LINE_INK)
    plt.close(fig)


def test_restore_reinstates_prior_cycle():
    fig, ax = plt.subplots()
    vzs.distill(ax)
    vzs.restore(ax)
    (line,) = ax.plot([0, 1], [0, 1])
    assert to_rgba(line.get_color()) == to_rgba("#1f77b4")  # matplotlib's default C0
    plt.close(fig)


def test_distill_before_plotting_frames_the_data_on_draw():
    fig, ax = plt.subplots()
    vzs.distill(ax)
    ax.plot([1, 2, 3], [3, 1, 2])
    fig.canvas.draw()
    assert ax.spines["bottom"].get_bounds() == (1.0, 3.0)
    plt.close(fig)


def test_restore_reinstates_minor_locators():
    fig, ax = plt.subplots()
    ax.set_yscale("log")
    ax.plot([1, 2, 3], [3, 40, 700])
    minor_before = ax.yaxis.get_minor_locator()
    vzs.distill(ax)
    vzs.restore(ax)
    assert ax.yaxis.get_minor_locator() is minor_before
    plt.close(fig)
