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


def _build_axes() -> tuple[plt.Figure, plt.Axes]:
    fig, ax = plt.subplots(figsize=(4, 3))
    ax.plot([0, 1], [0, 10])
    vzs.apply(ax, frame="data")
    ax.yaxis.set_major_formatter("{x:.2f}")
    return fig, ax


def test_grow_past_prior_max_does_not_inherit_shift():
    fig, ax = _build_axes()
    # `apply` already materialized a tick pool for the default locator;
    # growing past it is what forces matplotlib to mint brand-new ticks.
    pool_size = len(ax.yaxis.majorTicks)

    # Two ticks close enough to collide: majorTicks[0]'s label gets shifted.
    ax.yaxis.set_major_locator(FixedLocator([4.0, 4.05]))
    fig.canvas.draw()
    assert abs(_measured_y_offsets(ax)[0]) > 0.5  # sanity: it really moved

    # Grow past the pool matplotlib already materialized: Axis.get_major_ticks
    # only ever appends, and Axis._copy_tick_props clones each new tick's
    # label from majorTicks[0] via Artist.update_from, so the new,
    # well-separated labels can inherit majorTicks[0]'s shifted transform
    # even though none of them collide with anything.
    grown = np.linspace(1.0, 9.0, pool_size + 3)
    ax.yaxis.set_major_locator(FixedLocator(grown))
    fig.canvas.draw()
    grown_offsets = _measured_y_offsets(ax)

    fig_ref, ax_ref = _build_axes()
    ax_ref.yaxis.set_major_locator(FixedLocator(grown))
    fig_ref.canvas.draw()
    reference_offsets = _measured_y_offsets(ax_ref)

    np.testing.assert_allclose(grown_offsets, reference_offsets, atol=0.5)
    plt.close(fig)
    plt.close(fig_ref)


def test_restore_reverts_tick_label_transforms():
    def boxes(ax: plt.Axes) -> list:
        ax.figure.canvas.draw()
        return [t.get_window_extent().bounds for t in ax.yaxis.get_ticklabels()]

    fig_a, ax_a = plt.subplots(figsize=(4, 3))
    ax_a.scatter(np.arange(ANSCOMBE_II_Y.size), ANSCOMBE_II_Y, s=12)
    # restore() keeps user-set formatters (only locators revert
    # unconditionally), so the pristine comparator must wear the same
    # formatter quartile_axes() sets to be a fair comparison.
    ax_a.yaxis.set_major_formatter("{x:.1f}")
    pristine = boxes(ax_a)

    fig_b, ax_b = quartile_axes()
    fig_b.canvas.draw()
    vzs.restore(ax_b)
    assert boxes(ax_b) == pristine
    plt.close(fig_a)
    plt.close(fig_b)
