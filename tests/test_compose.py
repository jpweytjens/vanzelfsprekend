import matplotlib.pyplot as plt
import numpy as np

import vanzelfsprekend


def test_register_adds_working_method_and_is_reentrant():
    vanzelfsprekend.register()
    vanzelfsprekend.register()
    fig, ax = plt.subplots()
    ax.plot([1, 2, 3], [3, 1, 2])
    nice = [1, 2.5, 5]
    result = ax.klaar(frame="data", offset=5, nice_numbers=nice)
    assert result is ax
    assert not ax.spines["top"].get_visible()
    assert ax.spines["bottom"].get_position() == ("outward", 5)
    fig.canvas.draw()
    assert ax.spines["bottom"].get_bounds() == tuple(ax.xaxis.get_data_interval())
    expected = vanzelfsprekend.TalbotLocator(nice_numbers=nice).tick_values(
        *ax.xaxis.get_data_interval()
    )
    np.testing.assert_allclose(ax.xaxis.get_majorticklocs(), expected)
    plt.close(fig)


def test_klaar_matches_range_frame_bounds():
    fig, ax = plt.subplots()
    rng = np.random.default_rng(0)
    x, y = rng.uniform(0.3, 9.7, 50), rng.uniform(-3.2, 4.1, 50)
    ax.scatter(x, y)
    vanzelfsprekend.klaar(ax)
    fig.canvas.draw()
    bottom = ax.spines["bottom"].get_bounds()

    fig2, ax2 = plt.subplots()
    ax2.scatter(x, y)
    vanzelfsprekend.range_frame(ax2)
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


def test_ontklaar_restores_prior_state():
    fig, ax = plt.subplots()
    rng = np.random.default_rng(0)
    ax.scatter(rng.uniform(0.3, 9.7, 50), rng.uniform(-3.2, 4.1, 50))
    before = _snapshot(ax)

    vanzelfsprekend.range_frame(ax)
    vanzelfsprekend.xlabel(ax, "t")
    vanzelfsprekend.ylabel(ax, "v", flush=True)
    fig.canvas.draw()

    vanzelfsprekend.ontklaar(ax)
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


def test_ontklaar_disconnects_hook():
    fig, ax = plt.subplots()
    rng = np.random.default_rng(0)
    ax.scatter(rng.uniform(0.3, 9.7, 50), rng.uniform(-3.2, 4.1, 50))
    vanzelfsprekend.range_frame(ax)
    fig.canvas.draw()
    vanzelfsprekend.ontklaar(ax)
    # With the hook gone, the left spine is no longer re-trimmed to the data.
    ax.spines["left"].set_bounds(0.0, 1.0)
    ax.set_ylim(-20, 20)
    fig.canvas.draw()
    assert ax.spines["left"].get_bounds() == (0.0, 1.0)
    plt.close(fig)


def test_ontklaar_on_untouched_axes_is_noop():
    fig, ax = plt.subplots()
    ax.plot([0, 1], [0, 1])
    vanzelfsprekend.ontklaar(ax)  # must not raise
    plt.close(fig)


def test_unregister_removes_methods_and_is_reentrant():
    vanzelfsprekend.register()
    from matplotlib.axes import Axes
    assert hasattr(Axes, "klaar")
    assert hasattr(Axes, "ontklaar")
    vanzelfsprekend.unregister()
    vanzelfsprekend.unregister()
    assert not hasattr(Axes, "klaar")
    assert not hasattr(Axes, "ontklaar")


def test_ontklaar_method_via_register():
    vanzelfsprekend.register()
    fig, ax = plt.subplots()
    ax.plot([1, 2, 3], [3, 1, 2])
    ax.klaar()
    fig.canvas.draw()
    ax.ontklaar()
    assert not hasattr(ax, "_vanzelfsprekend_state")
    vanzelfsprekend.unregister()
    plt.close(fig)


def test_ontklaar_after_repeated_range_frame_restores_original_locator():
    fig, ax = plt.subplots()
    rng = np.random.default_rng(0)
    ax.scatter(rng.uniform(0.3, 9.7, 50), rng.uniform(-3.2, 4.1, 50))
    original = ax.xaxis.get_major_locator()
    vanzelfsprekend.range_frame(ax)
    vanzelfsprekend.range_frame(ax, frame="data")
    fig.canvas.draw()
    vanzelfsprekend.ontklaar(ax)
    assert ax.xaxis.get_major_locator() is original
    plt.close(fig)
