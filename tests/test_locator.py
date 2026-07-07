import matplotlib.pyplot as plt
import numpy as np
import pytest
from mizani.breaks import breaks_extended

from tufty import TalbotLocator


def test_matches_mizani_directly():
    expected = breaks_extended(n=5, only_inside=True)((0.3, 9.7))
    result = TalbotLocator(n=5).tick_values(0.3, 9.7)
    np.testing.assert_allclose(result, expected)


def test_ticks_stay_inside_data_range():
    ticks = TalbotLocator().tick_values(0.3, 9.7)
    assert ticks.min() >= 0.3
    assert ticks.max() <= 9.7


def test_respects_n():
    few = TalbotLocator(n=3).tick_values(0.0, 100.0)
    many = TalbotLocator(n=8).tick_values(0.0, 100.0)
    assert len(few) < len(many)


@pytest.mark.parametrize(
    "vmin, vmax",
    [(np.nan, 1.0), (-np.inf, np.inf), (2.0, 2.0), (5.0, 1.0)],
)
def test_degenerate_inputs_do_not_raise(vmin, vmax):
    ticks = TalbotLocator().tick_values(vmin, vmax)
    assert len(ticks) > 0


def test_empty_axes_draw_does_not_raise():
    fig, ax = plt.subplots()
    ax.xaxis.set_major_locator(TalbotLocator())
    fig.canvas.draw()
    plt.close(fig)
