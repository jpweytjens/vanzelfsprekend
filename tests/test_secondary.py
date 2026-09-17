import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt
import numpy as np
import pytest
from matplotlib.ticker import FixedLocator

import vanzelfsprekend as vzs
from vanzelfsprekend.mute import LINE_WIDTH
from vanzelfsprekend.palettes import ACCENT_INK, LINE_INK, TEXT_INK


def _sin_axes():
    fig, ax = plt.subplots()
    x = np.linspace(0, 2 * np.pi, 200)
    ax.plot(x, np.sin(x))
    vzs.apply(ax, frame="loose")
    ax.xaxis.set_major_locator(vzs.TalbotLocator(unit=np.pi))
    return fig, ax


def test_mirrors_host_ticks_as_degrees():
    fig, ax = _sin_axes()
    secax = vzs.secondary_frame(ax, (np.rad2deg, np.deg2rad))
    fig.canvas.draw()
    np.testing.assert_allclose(secax.xaxis.get_majorticklocs(), [0, 90, 180, 270, 360])
    plt.close(fig)


def test_degree_ticks_sit_under_host():
    fig, ax = _sin_axes()
    secax = vzs.secondary_frame(ax, (np.rad2deg, np.deg2rad))
    fig.canvas.draw()
    # the secondary is laid out so its units are rad2deg of the host's
    np.testing.assert_allclose(secax.get_xlim(), np.rad2deg(ax.get_xlim()))
    plt.close(fig)


def test_styles_to_frame_ink():
    fig, ax = _sin_axes()
    secax = vzs.secondary_frame(ax, (np.rad2deg, np.deg2rad))
    fig.canvas.draw()
    spine = secax.spines["top"]
    assert spine.get_edgecolor() == matplotlib.colors.to_rgba(LINE_INK)
    assert spine.get_linewidth() == LINE_WIDTH
    # spine trimmed to the host's data extent, in degrees
    np.testing.assert_allclose(spine.get_bounds(), (0.0, 360.0))
    tick = secax.xaxis.get_major_ticks()[0]
    to_rgba = matplotlib.colors.to_rgba
    assert to_rgba(tick.tick1line.get_color()) == to_rgba(LINE_INK)
    assert to_rgba(tick.label1.get_color()) == to_rgba(TEXT_INK)
    plt.close(fig)


def test_remirrors_when_host_reticks():
    # The applier re-reads host ticks each draw, so a host re-tick is followed.
    fig, ax = _sin_axes()
    secax = vzs.secondary_frame(ax, (np.rad2deg, np.deg2rad))
    fig.canvas.draw()
    ax.xaxis.set_major_locator(FixedLocator([0.0, np.pi]))
    fig.canvas.draw()
    np.testing.assert_allclose(secax.xaxis.get_majorticklocs(), [0, 180])
    plt.close(fig)


def test_where_left_mirrors_the_y_axis():
    fig, ax = plt.subplots()
    ax.plot(np.linspace(0, 2 * np.pi, 50), np.linspace(0, 2 * np.pi, 50))
    vzs.apply(ax)
    ax.yaxis.set_major_locator(vzs.TalbotLocator(unit=np.pi))
    secax = vzs.secondary_frame(ax, (np.rad2deg, np.deg2rad), where="left")
    fig.canvas.draw()
    np.testing.assert_allclose(secax.yaxis.get_majorticklocs(), [0, 90, 180, 270, 360])
    plt.close(fig)


@pytest.mark.parametrize("bad", ["middle", "up", "x"])
def test_invalid_where_raises(bad):
    fig, ax = plt.subplots()
    with pytest.raises(ValueError, match="where"):
        vzs.secondary_frame(ax, (np.rad2deg, np.deg2rad), where=bad)
    plt.close(fig)


def test_restore_removes_the_secondary():
    fig, ax = _sin_axes()
    secax = vzs.secondary_frame(ax, (np.rad2deg, np.deg2rad))
    fig.canvas.draw()
    assert secax in ax.child_axes
    vzs.restore(ax)
    fig.canvas.draw()  # must not raise after teardown
    assert secax not in ax.child_axes
    plt.close(fig)


def test_secondary_spine_matches_host_offset():
    # _sin_axes applies a loose frame, which stands the host axis spine off
    # by a few points; the secondary must take the same offset to match.
    fig, ax = _sin_axes()
    secax = vzs.secondary_frame(ax, (np.rad2deg, np.deg2rad))
    assert secax.spines["top"].get_position() == ax.spines["bottom"].get_position()
    assert ax.spines["bottom"].get_position() == ("outward", 8)
    plt.close(fig)


def test_accessor_secondary_frame():
    fig, ax = _sin_axes()
    secax = ax.vzs.secondary_frame((np.rad2deg, np.deg2rad))
    fig.canvas.draw()
    np.testing.assert_allclose(secax.xaxis.get_majorticklocs(), [0, 90, 180, 270, 360])
    plt.close(fig)


def _peak_axes():
    # A Talbot grid in units of pi plus one named feature, the peak; 201
    # points put a sample exactly on pi/2, so the peak is that tick.
    fig, ax = plt.subplots()
    x = np.linspace(0, 2 * np.pi, 201)
    y = np.sin(x)
    ax.plot(x, y)
    vzs.apply(ax)
    ax.xaxis.set_major_locator(
        vzs.AugmentedLocator(
            vzs.TalbotLocator(unit=np.pi),
            vzs.FeatureLocator(x, y, {"peak": lambda x, y: x[np.argmax(y)]}),
        )
    )
    return fig, ax


def _sec_label_at(secax, position):
    axis = secax.xaxis
    for loc, tick in zip(
        axis.get_majorticklocs(), axis.get_major_ticks(), strict=False
    ):
        if np.isclose(loc, position):
            return tick.label1
    raise AssertionError(f"no secondary tick at {position}")


def test_secondary_mirrors_the_hosts_accent():
    fig, ax = _peak_axes()
    secax = vzs.secondary_frame(ax, (np.rad2deg, np.deg2rad))
    vzs.accent(ax)
    fig.canvas.draw()
    to_rgba = matplotlib.colors.to_rgba
    assert to_rgba(_sec_label_at(secax, 90).get_color()) == to_rgba(ACCENT_INK)
    assert to_rgba(_sec_label_at(secax, 180).get_color()) == to_rgba(TEXT_INK)
    plt.close(fig)


def test_secondary_mirrors_only_features_blanking():
    fig, ax = _peak_axes()
    secax = vzs.secondary_frame(ax, (np.rad2deg, np.deg2rad))
    vzs.accent(ax, only_features=True)
    fig.canvas.draw()
    assert _sec_label_at(secax, 90).get_text() != ""
    assert _sec_label_at(secax, 180).get_text() == ""
    plt.close(fig)


def test_secondary_follows_a_later_mute_ink():
    fig, ax = _sin_axes()
    secax = vzs.secondary_frame(ax, (np.rad2deg, np.deg2rad))
    fig.canvas.draw()
    vzs.mute(ax, line_ink="red", line_width=1.4)
    fig.canvas.draw()
    to_rgba = matplotlib.colors.to_rgba
    assert secax.spines["top"].get_edgecolor() == to_rgba("red")
    assert secax.spines["top"].get_linewidth() == 1.4
    tick = secax.xaxis.get_major_ticks()[0]
    assert to_rgba(tick.tick2line.get_color()) == to_rgba("red")
    assert tick.tick2line.get_markeredgewidth() == 1.4
    plt.close(fig)


def test_secondary_follows_a_later_tick_direction():
    fig, ax = _sin_axes()
    secax = vzs.secondary_frame(ax, (np.rad2deg, np.deg2rad))
    fig.canvas.draw()
    vzs.tick_direction(ax, "in")
    fig.canvas.draw()
    assert secax.xaxis.get_tick_params()["direction"] == "in"
    vzs.tick_direction(ax, "none")
    fig.canvas.draw()
    assert secax.xaxis.get_tick_params()["length"] == 0
    plt.close(fig)


def test_unmuted_host_gives_an_unmuted_secondary():
    # A range frame without mute keeps matplotlib's black spines; the
    # secondary takes the host's ink, whatever it is, not the palette's.
    fig, ax = plt.subplots()
    ax.plot([0, 1], [0, 1])
    vzs.range_frame(ax)
    secax = vzs.secondary_frame(ax, (lambda v: 2 * v, lambda v: v / 2))
    fig.canvas.draw()
    assert secax.spines["top"].get_edgecolor() == ax.spines["bottom"].get_edgecolor()
    assert secax.spines["top"].get_linewidth() == ax.spines["bottom"].get_linewidth()
    plt.close(fig)
