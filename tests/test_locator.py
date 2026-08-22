import matplotlib.pyplot as plt
import numpy as np
import pytest
from mizani.breaks import breaks_extended

from vanzelfsprekend import TalbotLocator, range_frame


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


def test_huge_range_does_not_raise():
    ticks = TalbotLocator().tick_values(-1e300, 1e300)
    assert len(ticks) > 0


def test_empty_axes_draw_does_not_raise():
    fig, ax = plt.subplots()
    ax.xaxis.set_major_locator(TalbotLocator())
    fig.canvas.draw()
    plt.close(fig)


def test_loose_ticks_bound_the_range():
    ticks = TalbotLocator(loose=True).tick_values(-3.2, 4.1)
    assert ticks.min() <= -3.2
    assert ticks.max() >= 4.1
    steps = np.diff(ticks)
    np.testing.assert_allclose(steps, steps[0])


def test_loose_without_extension_when_already_covered():
    ticks = TalbotLocator(loose=True).tick_values(0.0, 100.0)
    assert ticks.min() == 0.0
    assert ticks.max() == 100.0


def test_view_limits_bound_the_range():
    with plt.rc_context({"axes.autolimit_mode": "round_numbers"}):
        lo, hi = TalbotLocator().view_limits(0.3, 9.7)
    assert lo <= 0.3
    assert hi >= 9.7


def test_view_limits_degenerate_does_not_raise():
    lo, hi = TalbotLocator().view_limits(2.0, 2.0)
    assert lo < hi


def test_loose_bounds_large_magnitude_range():
    vmin, vmax = -3049020730.258315, 2605259400.20343
    ticks = TalbotLocator(n=5, loose=True).tick_values(vmin, vmax)
    assert ticks.min() <= vmin
    assert ticks.max() >= vmax


def test_view_limits_bound_large_magnitude_range():
    vmin, vmax = -3049020730.258315, 2605259400.20343
    with plt.rc_context({"axes.autolimit_mode": "round_numbers"}):
        lo, hi = TalbotLocator().view_limits(vmin, vmax)
    assert lo <= vmin
    assert hi >= vmax


def test_view_limits_swapped_input():
    with plt.rc_context({"axes.autolimit_mode": "round_numbers"}):
        lo, hi = TalbotLocator().view_limits(9.7, 0.3)
    assert lo <= 0.3
    assert hi >= 9.7


def test_view_limits_data_mode_returns_input():
    with plt.rc_context({"axes.autolimit_mode": "data"}):
        lo, hi = TalbotLocator().view_limits(0.3, 9.7)
    assert (lo, hi) == (0.3, 9.7)


def test_view_limits_round_numbers_rounds_outward():
    with plt.rc_context({"axes.autolimit_mode": "round_numbers"}):
        lo, hi = TalbotLocator().view_limits(0.3, 9.7)
    assert lo <= 0.3
    assert hi >= 9.7
    assert (lo, hi) != (0.3, 9.7)


def test_nice_numbers_forwarded_to_mizani():
    expected = breaks_extended(n=5, Q=[1, 2.5, 5], only_inside=True)((0.4, 9.6))
    result = TalbotLocator(nice_numbers=[1, 2.5, 5]).tick_values(0.4, 9.6)
    np.testing.assert_allclose(result, expected)


def test_weights_merged_over_defaults_in_slot_order():
    expected = breaks_extended(n=5, only_inside=True, w=(0.25, 0.4, 0.5, 0.05))((0.3, 9.7))
    result = TalbotLocator(weights={"coverage": 0.4}).tick_values(0.3, 9.7)
    np.testing.assert_allclose(result, expected)


def test_weights_invalid_key_raises_value_error():
    with pytest.raises(ValueError, match="coverge"):
        TalbotLocator(weights={"coverge": 0.4})


def test_range_frame_nice_numbers_forwarded_to_both_axes():
    nice = [1, 2.5, 5]
    fig, ax = plt.subplots()
    rng = np.random.default_rng(0)
    ax.scatter(rng.uniform(0.3, 9.7, 50), rng.uniform(-3.2, 4.1, 50))
    range_frame(ax, nice_numbers=nice)
    fig.canvas.draw()
    expected = breaks_extended(n=5, Q=nice, only_inside=True)
    for axis in (ax.xaxis, ax.yaxis):
        np.testing.assert_allclose(
            axis.get_majorticklocs(), expected(tuple(axis.get_data_interval()))
        )
    plt.close(fig)
