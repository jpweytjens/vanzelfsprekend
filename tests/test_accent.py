import matplotlib.pyplot as plt
import numpy as np
import pytest

import vanzelfsprekend as vzs
from vanzelfsprekend import palettes
from vanzelfsprekend.locator import (
    AugmentedLocator,
    FeatureLocator,
    QuartileLocator,
    TalbotLocator,
)


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


def test_accent_selects_a_single_name():
    fig, ax = _quartile_axes()
    vzs.range_frame(ax)
    vzs.accent(ax, at=["median"])
    fig.canvas.draw()
    assert _label_color_at(ax, "y", 50.0) == palettes.ACCENT_INK
    assert _label_color_at(ax, "y", 25.0) != palettes.ACCENT_INK  # Q1 not selected
    plt.close(fig)


def test_accent_unknown_name_raises_listing_available():
    fig, ax = _quartile_axes()
    vzs.range_frame(ax)
    with pytest.raises(ValueError, match=r"Q9.*median"):
        vzs.accent(ax, at=["Q9"])
    plt.close(fig)


def test_accent_by_position_on_unnamed_locator():
    fig, ax = plt.subplots()
    x, y = np.linspace(0, 10, 50), np.linspace(0, 10, 50)
    ax.plot(x, y)
    ax.xaxis.set_major_locator(FeatureLocator(x, y, [lambda x, y: x[np.argmax(y)]]))
    vzs.range_frame(ax)
    vzs.accent(ax, at=[10.0], axis="x")
    fig.canvas.draw()
    assert _label_color_at(ax, "x", 10.0) == palettes.ACCENT_INK
    plt.close(fig)


def _label_text_at(ax, axis_name, position):
    axis = getattr(ax, f"{axis_name}axis")
    for loc, tick in zip(
        axis.get_majorticklocs(), axis.get_major_ticks(), strict=False
    ):
        if np.isclose(loc, position):
            return tick.label1.get_text()
    raise AssertionError(f"no tick at {position}")


def test_only_features_blanks_the_grid_labels():
    fig, ax = _quartile_axes()
    vzs.range_frame(ax)
    vzs.accent(ax, only_features=True)
    fig.canvas.draw()
    assert _label_text_at(ax, "y", 50.0) != ""  # a quartile keeps its label
    assert _label_text_at(ax, "y", 20.0) == ""  # a grid tick is blanked
    plt.close(fig)


def test_only_features_restored():
    fig, ax = _quartile_axes()
    vzs.range_frame(ax)
    vzs.accent(ax, only_features=True)
    fig.canvas.draw()
    vzs.restore(ax)
    fig.canvas.draw()
    assert _label_text_at(ax, "y", 20.0) != ""  # grid label back
    plt.close(fig)
