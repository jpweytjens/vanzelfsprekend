import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt
import numpy as np
import pytest
from matplotlib.ticker import FixedLocator

import vanzelfsprekend as vzs
from vanzelfsprekend.mute import LINE_WIDTH
from vanzelfsprekend.palettes import LINE_INK, TEXT_INK


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


def test_accessor_secondary_frame():
    fig, ax = _sin_axes()
    secax = ax.vzs.secondary_frame((np.rad2deg, np.deg2rad))
    fig.canvas.draw()
    np.testing.assert_allclose(secax.xaxis.get_majorticklocs(), [0, 90, 180, 270, 360])
    plt.close(fig)
