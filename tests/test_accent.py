import matplotlib.pyplot as plt
import numpy as np
import pytest

import vanzelfsprekend as vzs
from vanzelfsprekend import palettes
from vanzelfsprekend.locator import AugmentedLocator, QuartileLocator, TalbotLocator


def _quartile_axes():
    fig, ax = plt.subplots()
    y = np.arange(101.0)
    ax.plot(y, y)
    ax.yaxis.set_major_locator(AugmentedLocator(TalbotLocator(), QuartileLocator(y)))
    return fig, ax


def _label_color_at(ax, axis_name, position):
    axis = getattr(ax, f"{axis_name}axis")
    for loc, tick in zip(
        axis.get_majorticklocs(), axis.get_major_ticks(), strict=False
    ):
        if np.isclose(loc, position):
            return tick.label1.get_color()
    raise AssertionError(f"no tick at {position}")


def test_accent_colours_feature_labels():
    fig, ax = _quartile_axes()
    vzs.range_frame(ax)
    vzs.accent(ax)
    fig.canvas.draw()
    assert _label_color_at(ax, "y", 50.0) == palettes.ACCENT_INK
    plt.close(fig)


def test_accent_leaves_base_labels_uncoloured():
    fig, ax = _quartile_axes()
    vzs.range_frame(ax)
    vzs.accent(ax)
    fig.canvas.draw()
    assert _label_color_at(ax, "y", 50.0) == palettes.ACCENT_INK  # feature
    assert _label_color_at(ax, "y", 20.0) != palettes.ACCENT_INK  # grid tick
    plt.close(fig)


def test_accent_custom_colour():
    fig, ax = _quartile_axes()
    vzs.range_frame(ax)
    vzs.accent(ax, color="#EE7733")
    fig.canvas.draw()
    assert _label_color_at(ax, "y", 50.0) == "#EE7733"
    plt.close(fig)


def test_accent_survives_redraw():
    fig, ax = _quartile_axes()
    vzs.range_frame(ax)
    vzs.accent(ax)
    fig.canvas.draw()
    ax.set_ylim(0, 100)
    fig.canvas.draw()
    assert _label_color_at(ax, "y", 50.0) == palettes.ACCENT_INK
    plt.close(fig)


def test_accent_restore_reverts_label_colour():
    fig, ax = _quartile_axes()
    vzs.range_frame(ax)
    vzs.accent(ax)
    fig.canvas.draw()
    before = _label_color_at(ax, "y", 20.0)
    vzs.restore(ax)
    fig.canvas.draw()
    assert _label_color_at(ax, "y", 50.0) == before
    plt.close(fig)


def test_accent_without_named_locator_raises():
    fig, ax = plt.subplots()
    ax.plot([0, 1], [0, 1])
    vzs.range_frame(ax)
    with pytest.raises(ValueError, match="no named features"):
        vzs.accent(ax)
    plt.close(fig)
