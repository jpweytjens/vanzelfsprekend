from itertools import pairwise

import matplotlib.pyplot as plt
import numpy as np
from matplotlib.ticker import FixedLocator

import vanzelfsprekend as vzs
from vanzelfsprekend.hook import get_state

# Anscombe set II's y: its upper quartile (8.95) and maximum (9.26)
# land close enough to collide at default font size.
ANSCOMBE_II_Y = np.array(
    [9.14, 8.14, 8.74, 8.77, 9.26, 8.10, 6.13, 3.10, 9.13, 7.26, 4.74]
)


def quartile_axes() -> tuple[plt.Figure, plt.Axes]:
    fig, ax = plt.subplots(figsize=(4, 3))
    ax.scatter(np.arange(ANSCOMBE_II_Y.size), ANSCOMBE_II_Y, s=12)
    vzs.apply(ax, frame="data")
    ax.yaxis.set_major_locator(vzs.QuartileLocator(ANSCOMBE_II_Y))
    ax.yaxis.set_major_formatter("{x:.1f}")
    return fig, ax


def _measured_y_offsets(ax: plt.Axes) -> np.ndarray:
    """Return each y tick label's actual pixel displacement off its tick."""
    locs = ax.yaxis.get_majorticklocs()
    boxes = [t.get_window_extent() for t in ax.yaxis.get_ticklabels()]
    points = np.ones((len(locs), 2))
    points[:, 1] = locs
    desired = ax.transData.transform(points)[:, 1]
    centers = np.array([0.5 * (b.y0 + b.y1) for b in boxes])
    return centers - desired


def test_colliding_quartile_labels_separate():
    fig, ax = quartile_axes()
    fig.canvas.draw()
    boxes = [t.get_window_extent() for t in ax.yaxis.get_ticklabels()]
    order = np.argsort(ax.yaxis.get_majorticklocs())
    for lower, upper in pairwise(order):
        assert boxes[upper].y0 - boxes[lower].y1 >= -0.5
    plt.close(fig)


def test_tick_marks_stay_at_the_quantiles():
    fig, ax = quartile_axes()
    fig.canvas.draw()
    np.testing.assert_allclose(
        ax.yaxis.get_majorticklocs(),
        np.quantile(ANSCOMBE_II_Y, (0, 0.25, 0.5, 0.75, 1)),
    )
    plt.close(fig)


def test_well_spaced_labels_stay_put():
    fig, ax = plt.subplots()
    ax.plot([0, 1, 2], [0, 1, 4])
    vzs.apply(ax)
    fig.canvas.draw()
    applied = get_state(ax)["tick_labels"]["applied"]
    offsets = [entry[1] for per_axis in applied.values() for entry in per_axis.values()]
    assert offsets
    assert np.allclose(offsets, 0.0)
    plt.close(fig)


def test_second_draw_is_stable():
    fig, ax = quartile_axes()
    fig.canvas.draw()
    from vanzelfsprekend.hook import run_appliers

    assert run_appliers(ax) is False
    plt.close(fig)


def test_shrink_then_grow_does_not_compound_displacement():
    fig, ax = quartile_axes()
    fig.canvas.draw()
    first = _measured_y_offsets(ax)

    # Matplotlib pools tick label Text objects (Axis.majorTicks only ever
    # grows), so dropping to fewer ticks and growing back to five reuses
    # the same, already-displaced label objects for the colliding pair.
    ax.yaxis.set_major_locator(FixedLocator(np.quantile(ANSCOMBE_II_Y, (0, 0.5, 1))))
    fig.canvas.draw()

    ax.yaxis.set_major_locator(vzs.QuartileLocator(ANSCOMBE_II_Y))
    fig.canvas.draw()
    second = _measured_y_offsets(ax)

    np.testing.assert_allclose(second, first, atol=0.5)
    plt.close(fig)
