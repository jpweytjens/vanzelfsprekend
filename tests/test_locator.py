import datetime as dt

import matplotlib.dates as mdates
import matplotlib.pyplot as plt
import numpy as np
import pytest
from mizani.breaks import breaks_extended

from vanzelfsprekend import (
    DateBreaksLocator,
    FeatureLocator,
    LogBreaksLocator,
    QuartileLocator,
    SummaryLocator,
    TalbotLocator,
    range_frame,
)


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
    ("vmin", "vmax"),
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
    expected = breaks_extended(n=5, only_inside=True, w=(0.25, 0.4, 0.5, 0.05))(
        (0.3, 9.7)
    )
    result = TalbotLocator(weights={"coverage": 0.4}).tick_values(0.3, 9.7)
    np.testing.assert_allclose(result, expected)


def test_weights_invalid_key_raises_value_error():
    with pytest.raises(ValueError, match="coverge"):
        TalbotLocator(weights={"coverge": 0.4})


def test_quartile_ticks_are_the_five_number_summary():
    ticks = QuartileLocator(np.arange(101.0)).tick_values(0.0, 100.0)
    np.testing.assert_allclose(ticks, [0.0, 25.0, 50.0, 75.0, 100.0])


def test_quartile_ignores_non_finite_values():
    ticks = QuartileLocator([0.0, np.nan, 1.0, np.inf, 2.0, 3.0, 4.0]).tick_values(
        0.0, 4.0
    )
    np.testing.assert_allclose(ticks, [0.0, 1.0, 2.0, 3.0, 4.0])


@pytest.mark.parametrize("data", [[], [np.nan, np.inf]])
def test_quartile_without_finite_data_raises(data):
    with pytest.raises(ValueError, match="finite"):
        QuartileLocator(data)


def test_quartile_on_scatter_axes():
    fig, ax = plt.subplots()
    rng = np.random.default_rng(0)
    x = rng.uniform(0.3, 9.7, 60)
    ax.scatter(x, rng.uniform(-3.2, 4.1, 60))
    ax.xaxis.set_major_locator(QuartileLocator(x))
    fig.canvas.draw()
    np.testing.assert_allclose(
        ax.xaxis.get_majorticklocs(), np.quantile(x, (0, 0.25, 0.5, 0.75, 1))
    )
    plt.close(fig)


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


def test_log_ticks_are_mizani_breaks_inside_the_range():
    ticks = LogBreaksLocator().tick_values(30, 4000)
    np.testing.assert_allclose(ticks, [30, 100, 300, 1000, 3000])


def test_log_ticks_stay_inside_data_range():
    ticks = LogBreaksLocator().tick_values(1.3, 8.4)
    assert ticks.min() >= 1.3
    assert ticks.max() <= 8.4


def test_log_base_two():
    ticks = LogBreaksLocator(base=2).tick_values(3, 700)
    np.testing.assert_allclose(ticks, [8, 32, 128, 512])


def test_log_loose_ticks_bound_the_range():
    ticks = LogBreaksLocator(loose=True).tick_values(30, 4000)
    assert ticks.min() <= 30
    assert ticks.max() >= 4000


def test_log_loose_extends_an_under_covering_grid():
    ticks = LogBreaksLocator(base=2, loose=True).tick_values(3, 700)
    assert ticks.min() <= 3
    assert ticks.max() >= 700
    np.testing.assert_allclose(ticks, [2, 8, 32, 128, 512, 2048])


@pytest.mark.parametrize(
    ("vmin", "vmax"),
    [
        (np.nan, 1.0),
        (-np.inf, np.inf),
        (2.0, 2.0),
        (5.0, 1.0),
        (-1.0, 100.0),
        (0.0, 0.0),
    ],
)
def test_log_degenerate_inputs_do_not_raise(vmin, vmax):
    ticks = LogBreaksLocator().tick_values(vmin, vmax)
    assert len(ticks) > 0


def test_log_view_limits_loose_uses_data_interval():
    fig, ax = plt.subplots()
    ax.set_yscale("log")
    ax.plot([1, 2, 3], [30, 400, 4000])
    ax.yaxis.set_major_locator(LogBreaksLocator(loose=True))
    fig.canvas.draw()
    lo, hi = ax.get_ylim()
    assert lo <= 30
    assert hi >= 4000
    plt.close(fig)


def test_log_empty_axes_draw_does_not_raise():
    fig, ax = plt.subplots()
    ax.set_xscale("log")
    ax.xaxis.set_major_locator(LogBreaksLocator())
    fig.canvas.draw()
    plt.close(fig)


def test_log_constant_data_still_shows_ticks():
    fig, ax = plt.subplots()
    ax.set_yscale("log")
    ax.plot([1, 2, 3], [5, 5, 5])
    ax.yaxis.set_major_locator(LogBreaksLocator())
    fig.canvas.draw()
    lo, hi = ax.get_ylim()
    ticks = ax.yaxis.get_majorticklocs()
    assert np.any((ticks >= lo) & (ticks <= hi))
    plt.close(fig)


def test_extend_to_cover_log_equal_grid_does_not_hang():
    from vanzelfsprekend.locator import _extend_to_cover_log

    ticks = _extend_to_cover_log(np.array([5.0, 5.0]), 1.0, 10.0)
    np.testing.assert_allclose(ticks, [5.0, 5.0])


def test_log_huge_constant_value_does_not_raise():
    fig, ax = plt.subplots()
    ax.set_yscale("log")
    ax.plot([1, 2, 3], [1e308, 1e308, 1e308])
    ax.yaxis.set_major_locator(LogBreaksLocator())
    fig.canvas.draw()
    plt.close(fig)


def test_log_base_below_one_loose_ticks_are_positive():
    ticks = LogBreaksLocator(base=0.5, loose=True).tick_values(1, 100)
    assert ticks.size > 0
    assert np.all(ticks > 0)


def test_log_view_limits_round_numbers():
    with plt.rc_context({"axes.autolimit_mode": "round_numbers"}):
        lo, hi = LogBreaksLocator().view_limits(30, 4000)
    assert lo <= 30
    assert hi >= 4000


def _date_interval(lo, hi):
    return mdates.date2num(lo), mdates.date2num(hi)


def test_date_ticks_are_month_starts_inside_the_range():
    vmin, vmax = _date_interval(dt.datetime(2023, 2, 14), dt.datetime(2024, 11, 3))
    ticks = DateBreaksLocator().tick_values(vmin, vmax)
    expected = mdates.date2num(
        [
            dt.datetime(2023, 5, 1),
            dt.datetime(2023, 9, 1),
            dt.datetime(2024, 1, 1),
            dt.datetime(2024, 5, 1),
            dt.datetime(2024, 9, 1),
        ]
    )
    np.testing.assert_allclose(ticks, expected)


def test_date_ticks_stay_inside_data_range():
    vmin, vmax = _date_interval(dt.datetime(2023, 2, 14), dt.datetime(2024, 11, 3))
    ticks = DateBreaksLocator().tick_values(vmin, vmax)
    assert ticks.min() >= vmin
    assert ticks.max() <= vmax


def test_date_intraday_ticks_are_hour_marks():
    vmin, vmax = _date_interval(
        dt.datetime(2024, 3, 1, 6, 30), dt.datetime(2024, 3, 1, 18, 45)
    )
    ticks = DateBreaksLocator().tick_values(vmin, vmax)
    expected = mdates.date2num([dt.datetime(2024, 3, 1, h) for h in (9, 12, 15, 18)])
    np.testing.assert_allclose(ticks, expected)


def test_date_loose_ticks_bound_the_range():
    vmin, vmax = _date_interval(dt.datetime(2023, 2, 14), dt.datetime(2024, 11, 3))
    ticks = DateBreaksLocator(loose=True).tick_values(vmin, vmax)
    assert ticks.min() <= vmin
    assert ticks.max() >= vmax


@pytest.mark.parametrize(
    ("vmin", "vmax"),
    [(np.nan, 1.0), (-np.inf, np.inf), (2.0, 2.0), (5.0, 1.0), (-1e300, 1e300)],
)
def test_date_degenerate_inputs_do_not_raise(vmin, vmax):
    ticks = DateBreaksLocator().tick_values(vmin, vmax)
    assert len(ticks) > 0


def test_date_empty_axes_draw_does_not_raise():
    fig, ax = plt.subplots()
    ax.xaxis.set_major_locator(DateBreaksLocator())
    fig.canvas.draw()
    plt.close(fig)


def test_date_view_limits_loose_uses_data_interval():
    fig, ax = plt.subplots()
    days = [dt.datetime(2023, 2, 14) + dt.timedelta(days=20 * i) for i in range(32)]
    ax.plot(days, range(32))
    ax.xaxis.set_major_locator(DateBreaksLocator(loose=True))
    fig.canvas.draw()
    lo, hi = ax.get_xlim()
    assert lo <= mdates.date2num(days[0])
    assert hi >= mdates.date2num(days[-1])
    plt.close(fig)


def test_date_view_limits_round_numbers():
    vmin, vmax = _date_interval(dt.datetime(2023, 2, 14), dt.datetime(2024, 11, 3))
    with plt.rc_context({"axes.autolimit_mode": "round_numbers"}):
        lo, hi = DateBreaksLocator().view_limits(vmin, vmax)
    assert lo <= vmin
    assert hi >= vmax


def test_quartile_locator_collapses_coincident_quantiles():
    locator = QuartileLocator([8, 8, 8, 8, 8, 8, 8, 8, 8, 8, 19])
    assert list(locator()) == [8.0, 19.0]


def _lorentzian_peak():
    x = np.linspace(16, 19, 61)
    y = 1 / (1 + ((x - 17.2) / 0.3) ** 2)
    return x, y


def test_feature_locator_marks_the_peak():
    x, y = _lorentzian_peak()
    locator = FeatureLocator(x, y, [lambda x, y: x[np.argmax(y)]])
    np.testing.assert_allclose(locator(), [17.2])


def test_feature_locator_flattens_array_valued_features():
    x = np.array([0.0, 1.0, 2.0, 3.0, 4.0])
    y = np.array([0.0, 1.0, 0.0, 1.0, 0.0])
    locator = FeatureLocator(x, y, [lambda x, y: x[y > 0.5]])
    np.testing.assert_allclose(locator(), [1.0, 3.0])


def test_feature_locator_drops_non_finite_results():
    x = np.array([0.0, 1.0, 2.0])
    y = np.array([0.0, 1.0, 2.0])
    locator = FeatureLocator(x, y, [lambda x, y: x[-1], lambda x, y: np.nan])
    np.testing.assert_allclose(locator(), [2.0])


def test_feature_locator_collapses_coincident_features():
    x = np.array([0.0, 1.0, 2.0])
    y = np.array([0.0, 1.0, 2.0])
    locator = FeatureLocator(x, y, [lambda x, y: x.min(), lambda x, y: x[0]])
    assert list(locator()) == [0.0]


def test_feature_locator_without_finite_positions_raises():
    with pytest.raises(ValueError, match="finite"):
        FeatureLocator([0.0, 1.0], [0.0, 1.0], [lambda x, y: np.nan])


def test_feature_locator_marks_the_peak_on_axes():
    fig, ax = plt.subplots()
    x, y = _lorentzian_peak()
    ax.plot(x, y)
    ax.xaxis.set_major_locator(FeatureLocator(x, y, [lambda x, y: x[np.argmax(y)]]))
    fig.canvas.draw()
    np.testing.assert_allclose(ax.xaxis.get_majorticklocs(), [17.2])
    plt.close(fig)


def test_feature_locator_accepts_constant_positions():
    x = np.array([0.0, 1.0, 2.0])
    y = np.array([0.0, 1.0, 2.0])
    locator = FeatureLocator(x, y, [0, lambda x, y: y.max()])
    np.testing.assert_allclose(locator(), [0.0, 2.0])


def test_summary_locator_marks_reducer_results():
    locator = SummaryLocator([0.0, 1.0, 2.0, 3.0, 4.0], [np.min, np.mean, np.max])
    np.testing.assert_allclose(locator(), [0.0, 2.0, 4.0])


def test_summary_locator_flattens_array_valued_reducers():
    locator = SummaryLocator(np.arange(101.0), [lambda v: np.quantile(v, (0.25, 0.75))])
    np.testing.assert_allclose(locator(), [25.0, 75.0])


def test_summary_locator_ignores_non_finite_values():
    locator = SummaryLocator([0.0, np.nan, 2.0, np.inf, 4.0], [np.min, np.max])
    np.testing.assert_allclose(locator(), [0.0, 4.0])


@pytest.mark.parametrize("values", [[], [np.nan, np.inf]])
def test_summary_locator_without_finite_data_raises(values):
    with pytest.raises(ValueError, match="finite"):
        SummaryLocator(values, [np.mean])


def test_summary_locator_accepts_constant_positions():
    locator = SummaryLocator([1.0, 2.0, 3.0], [0, np.max])
    np.testing.assert_allclose(locator(), [0.0, 3.0])
