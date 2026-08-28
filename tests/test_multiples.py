import matplotlib.pyplot as plt
import numpy as np

import vanzelfsprekend as vzs
from vanzelfsprekend.multiples import _GroupLocator


def test_group_locator_computes_ticks_from_union():
    fig, axes = plt.subplots(1, 2)
    axes[0].plot([0, 4], [0, 1])
    axes[1].plot([6, 10], [0, 1])
    vzs.range_frame(axes[0])
    inner = axes[0].xaxis.get_major_locator()
    axes[0].xaxis.set_major_locator(_GroupLocator(inner, list(axes), "x"))
    fig.canvas.draw()
    expected = vzs.TalbotLocator().tick_values(0, 10)
    np.testing.assert_allclose(axes[0].xaxis.get_majorticklocs(), expected)
    plt.close(fig)


def test_group_locator_falls_back_to_inner_when_union_empty():
    fig, axes = plt.subplots(1, 2)
    vzs.range_frame(axes[0])  # no data anywhere
    inner = axes[0].xaxis.get_major_locator()
    axes[0].xaxis.set_major_locator(_GroupLocator(inner, list(axes), "x"))
    fig.canvas.draw()  # must not raise; inner's own fallback path runs
    plt.close(fig)
