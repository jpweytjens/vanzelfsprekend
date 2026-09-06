import matplotlib.pyplot as plt
import numpy as np

import vanzelfsprekend as vzs
from vanzelfsprekend.group import GroupLocator


def test_group_locator_computes_ticks_from_union():
    fig, axes = plt.subplots(1, 2)
    axes[0].plot([0, 4], [0, 1])
    axes[1].plot([6, 10], [0, 1])
    vzs.range_frame(axes[0])
    inner = axes[0].xaxis.get_major_locator()
    axes[0].xaxis.set_major_locator(GroupLocator(inner, list(axes), "x"))
    fig.canvas.draw()
    expected = vzs.TalbotLocator().tick_values(0, 10)
    np.testing.assert_allclose(axes[0].xaxis.get_majorticklocs(), expected)
    plt.close(fig)


def test_group_locator_falls_back_to_inner_when_union_empty():
    fig, axes = plt.subplots(1, 2)
    vzs.range_frame(axes[0])  # no data anywhere
    inner = axes[0].xaxis.get_major_locator()
    axes[0].xaxis.set_major_locator(GroupLocator(inner, list(axes), "x"))
    fig.canvas.draw()  # must not raise; inner's own fallback path runs
    plt.close(fig)


def test_group_locator_view_limits_cover_the_union():
    # Loose spans of (0, 1) and (10, 11) are (0, 1) and (10, 11); the
    # loose span of their union (0, 11) is (0, 12.5). The group must
    # report the latter, not the panel's own span.
    fig, axes = plt.subplots(1, 2)
    axes[0].plot([0, 1], [0, 1])
    axes[1].plot([10, 11], [0, 1])
    vzs.range_frame(axes[0], frame="loose")
    inner = axes[0].xaxis.get_major_locator()
    grouped = GroupLocator(inner, list(axes), "x")
    assert grouped.view_limits(0, 1) == (0.0, 12.5)
    assert inner.view_limits(0, 1) == (0.0, 1.0)
    plt.close(fig)
