import matplotlib.pyplot as plt
import numpy as np
from matplotlib.colors import to_rgba

import vanzelfsprekend as vfs


def test_register_adds_working_method_and_is_reentrant():
    vfs.register()
    vfs.register()
    fig, ax = plt.subplots()
    ax.plot([1, 2, 3], [3, 1, 2])
    nice = [1, 2.5, 5]
    result = ax.apply(frame="data", offset=5, nice_numbers=nice)
    assert result is ax
    assert not ax.spines["top"].get_visible()
    assert ax.spines["bottom"].get_position() == ("outward", 5)
    fig.canvas.draw()
    assert ax.spines["bottom"].get_bounds() == tuple(ax.xaxis.get_data_interval())
    expected = vfs.TalbotLocator(nice_numbers=nice).tick_values(
        *ax.xaxis.get_data_interval()
    )
    np.testing.assert_allclose(ax.xaxis.get_majorticklocs(), expected)
    plt.close(fig)


def test_apply_matches_range_frame_bounds():
    fig, ax = plt.subplots()
    rng = np.random.default_rng(0)
    x, y = rng.uniform(0.3, 9.7, 50), rng.uniform(-3.2, 4.1, 50)
    ax.scatter(x, y)
    vfs.apply(ax)
    fig.canvas.draw()
    bottom = ax.spines["bottom"].get_bounds()

    fig2, ax2 = plt.subplots()
    ax2.scatter(x, y)
    vfs.range_frame(ax2)
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

    vfs.range_frame(ax)
    vfs.xlabel(ax, "t")
    vfs.ylabel(ax, "v", flush=True)
    fig.canvas.draw()

    vfs.restore(ax)
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
    vfs.range_frame(ax)
    fig.canvas.draw()
    vfs.restore(ax)
    # With the hook gone, the left spine is no longer re-trimmed to the data.
    ax.spines["left"].set_bounds(0.0, 1.0)
    ax.set_ylim(-20, 20)
    fig.canvas.draw()
    assert ax.spines["left"].get_bounds() == (0.0, 1.0)
    plt.close(fig)


def test_restore_on_untouched_axes_is_noop():
    fig, ax = plt.subplots()
    ax.plot([0, 1], [0, 1])
    vfs.restore(ax)  # must not raise
    plt.close(fig)


def test_unregister_removes_methods_and_is_reentrant():
    vfs.register()
    from matplotlib.axes import Axes

    assert hasattr(Axes, "apply")
    assert hasattr(Axes, "restore")
    vfs.unregister()
    vfs.unregister()
    assert not hasattr(Axes, "apply")
    assert not hasattr(Axes, "restore")


def test_restore_method_via_register():
    vfs.register()
    fig, ax = plt.subplots()
    ax.plot([1, 2, 3], [3, 1, 2])
    ax.apply()
    fig.canvas.draw()
    ax.restore()
    assert not hasattr(ax, "_vanzelfsprekend_state")
    vfs.unregister()
    plt.close(fig)


def test_restore_after_repeated_range_frame_restores_original_locator():
    fig, ax = plt.subplots()
    rng = np.random.default_rng(0)
    ax.scatter(rng.uniform(0.3, 9.7, 50), rng.uniform(-3.2, 4.1, 50))
    original = ax.xaxis.get_major_locator()
    vfs.range_frame(ax)
    vfs.range_frame(ax, frame="data")
    fig.canvas.draw()
    vfs.restore(ax)
    assert ax.xaxis.get_major_locator() is original
    plt.close(fig)


def test_apply_mutes_and_installs_ink_first_cycle():
    fig, ax = plt.subplots()
    vfs.apply(ax)
    (first,) = ax.plot([0, 1], [0, 1])
    (second,) = ax.plot([0, 1], [1, 0])
    assert to_rgba(first.get_color()) == to_rgba(vfs.palettes.DATA_INK)
    assert to_rgba(second.get_color()) == to_rgba(vfs.palettes.VIBRANT["orange"])
    assert ax.spines["left"].get_edgecolor() == to_rgba(vfs.palettes.LINE_INK)
    plt.close(fig)


def test_restore_reinstates_prior_cycle():
    fig, ax = plt.subplots()
    vfs.apply(ax)
    vfs.restore(ax)
    (line,) = ax.plot([0, 1], [0, 1])
    assert to_rgba(line.get_color()) == to_rgba("#1f77b4")  # matplotlib's default C0
    plt.close(fig)


def test_apply_before_plotting_frames_the_data_on_draw():
    fig, ax = plt.subplots()
    vfs.apply(ax)
    ax.plot([1, 2, 3], [3, 1, 2])
    fig.canvas.draw()
    assert ax.spines["bottom"].get_bounds() == (1.0, 3.0)
    plt.close(fig)
