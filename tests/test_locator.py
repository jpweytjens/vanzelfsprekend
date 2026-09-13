import datetime as dt

import matplotlib.dates as mdates
import matplotlib.pyplot as plt
import numpy as np
import pytest
from dateutil.relativedelta import relativedelta
from hypothesis import given, settings
from hypothesis import strategies as st
from matplotlib.ticker import FixedLocator
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
from vanzelfsprekend.locator import AugmentedLocator


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


def test_loose_pair_frees_only_the_high_end():
    ticks = TalbotLocator(n=3, loose=(False, True)).tick_values(-7.7, 196.9)
    np.testing.assert_allclose(ticks, [0, 100, 200])


def test_loose_pair_keeps_the_nice_end_inside():
    ticks = TalbotLocator(loose=(True, False)).tick_values(0.3, 9.7)
    assert ticks.min() <= 0.3
    assert ticks.max() <= 9.7
    steps = np.diff(ticks)
    np.testing.assert_allclose(steps, steps[0])


def test_loose_pair_extends_only_the_loose_end():
    ticks = TalbotLocator(loose=(False, True)).tick_values(0.3, 9.7)
    assert ticks.min() >= 0.3
    assert ticks.max() >= 9.7


def test_loose_pair_view_limits_cover_only_the_loose_end():
    fig, ax = plt.subplots()
    ax.scatter([0.3, 9.7], [0, 1])
    ax.xaxis.set_major_locator(TalbotLocator(loose=(True, False)))
    fig.canvas.draw()
    lo, hi = ax.get_xlim()
    assert lo <= 0.3
    assert lo == ax.xaxis.get_majorticklocs().min()
    assert hi == pytest.approx(9.7 + 0.05 * 9.4)
    plt.close(fig)


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


def test_log_loose_pair_frees_only_the_high_end():
    ticks = LogBreaksLocator(n=4, loose=(False, True)).tick_values(30, 4000)
    np.testing.assert_allclose(ticks, [100, 1000, 10000])


def test_log_loose_pair_frees_only_the_low_end():
    ticks = LogBreaksLocator(n=4, loose=(True, False)).tick_values(30, 4000)
    np.testing.assert_allclose(ticks, [10, 100, 1000])


def test_log_loose_pair_view_limits_cover_only_the_loose_end():
    fig, ax = plt.subplots()
    ax.set_yscale("log")
    ax.plot([1, 2, 3], [30, 400, 4000])
    ax.yaxis.set_major_locator(LogBreaksLocator(loose=(False, True)))
    fig.canvas.draw()
    lo, hi = ax.get_ylim()
    assert lo < 30
    assert lo == pytest.approx(30 / (4000 / 30) ** 0.05)
    assert hi == 10000
    plt.close(fig)


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


def test_date_loose_pair_frees_only_the_low_end():
    vmin, vmax = _date_interval(dt.datetime(2023, 2, 14), dt.datetime(2024, 11, 3))
    ticks = DateBreaksLocator(loose=(True, False)).tick_values(vmin, vmax)
    assert ticks.min() <= vmin
    assert ticks.max() <= vmax
    assert ticks.min() == mdates.date2num(dt.datetime(2023, 1, 1))


def test_date_loose_pair_view_limits_cover_only_the_loose_end():
    fig, ax = plt.subplots()
    days = [dt.datetime(2023, 2, 14) + dt.timedelta(days=20 * i) for i in range(32)]
    ax.plot(days, range(32))
    ax.xaxis.set_major_locator(DateBreaksLocator(loose=(True, False)))
    fig.canvas.draw()
    lo, hi = ax.get_xlim()
    first, last = mdates.date2num(days[0]), mdates.date2num(days[-1])
    assert lo <= first
    assert lo == mdates.date2num(dt.datetime(2023, 1, 1))
    assert hi == pytest.approx(last + 0.05 * (last - first))
    plt.close(fig)


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


def test_view_limits_over_takes_the_interval_it_is_given():
    loose = TalbotLocator(loose=True)
    assert loose.view_limits_over(0, 1, (0, 11)) == (0.0, 12.5)
    assert loose.view_limits_over(0, 1, None) == (0.0, 1.0)
    plain = TalbotLocator()
    assert plain.view_limits_over(0, 1, (0, 11)) == (0.0, 1.0)


def _drawn_ticks(figsize, locator, name="x", scale="linear", labelsize=None):
    fig, ax = plt.subplots(figsize=figsize)
    axis = ax.xaxis if name == "x" else ax.yaxis
    if scale == "log":
        ax.set_xscale("log") if name == "x" else ax.set_yscale("log")
        ax.plot([1, 1e6], [1, 1e6])
    elif scale == "date":
        span = [dt.datetime(2000, 1, 1), dt.datetime(2024, 1, 1)]
        ax.plot(span, span)
    else:
        ax.plot([0, 100], [0, 100])
    if labelsize is not None:
        ax.tick_params(axis=name, labelsize=labelsize)
    axis.set_major_locator(locator)
    fig.canvas.draw()
    ticks = axis.get_majorticklocs()
    plt.close(fig)
    return ticks


def test_count_follows_axis_length():
    wide = _drawn_ticks((10, 3), TalbotLocator())
    narrow = _drawn_ticks((2, 3), TalbotLocator())
    assert len(narrow) < len(wide)


def test_count_follows_label_size():
    small = _drawn_ticks((6, 3), TalbotLocator(), labelsize=6)
    large = _drawn_ticks((6, 3), TalbotLocator(), labelsize=24)
    assert len(large) < len(small)


def test_y_spaces_denser_than_x_by_default():
    x = _drawn_ticks((4, 4), TalbotLocator(), name="x")
    y = _drawn_ticks((4, 4), TalbotLocator(), name="y")
    assert len(x) < len(y)


def test_spacing_sets_the_gap_in_label_heights():
    tight = _drawn_ticks((6, 3), TalbotLocator(spacing=2))
    loose = _drawn_ticks((6, 3), TalbotLocator(spacing=14))
    assert len(loose) < len(tight)


def test_n_overrides_spacing():
    ticks = _drawn_ticks((10, 3), TalbotLocator(n=3, spacing=2))
    np.testing.assert_allclose(ticks, TalbotLocator(n=3).tick_values(0, 100))


def test_narrow_axis_keeps_two_ticks():
    ticks = _drawn_ticks((0.6, 3), TalbotLocator())
    assert len(ticks) >= 2


def test_unbound_default_targets_five():
    expected = breaks_extended(n=5, only_inside=True)((0.3, 9.7))
    np.testing.assert_allclose(TalbotLocator().tick_values(0.3, 9.7), expected)


def test_loose_view_follows_axis_length():
    fig, ax = plt.subplots(figsize=(1.5, 3))
    ax.plot([0.3, 9.7], [0, 1])
    ax.xaxis.set_major_locator(TalbotLocator(loose=True))
    fig.canvas.draw()
    ticks = ax.get_xticks()
    assert tuple(ax.get_xlim()) == (ticks[0], ticks[-1])
    plt.close(fig)


def test_log_count_follows_axis_length():
    wide = _drawn_ticks((10, 3), LogBreaksLocator(), scale="log")
    narrow = _drawn_ticks((1.5, 3), LogBreaksLocator(), scale="log")
    assert len(narrow) < len(wide)


def test_date_count_follows_axis_length():
    wide = _drawn_ticks((10, 3), DateBreaksLocator(), scale="date")
    narrow = _drawn_ticks((1.5, 3), DateBreaksLocator(), scale="date")
    assert len(narrow) < len(wide)


def test_date_even_month_start_still_lands_on_january():
    # A ~14-month span starting in an even month used to select mizani's
    # 2-month grid, which floors to the start month and keeps its parity
    # (June -> even months), so it never lands on 1 January. Dropping the
    # 2-month step falls back to the year-anchored quarterly grid.
    vmin, vmax = _date_interval(dt.datetime(2019, 6, 10), dt.datetime(2020, 8, 5))
    ticks = DateBreaksLocator().tick_values(vmin, vmax, 6)
    expected = mdates.date2num(
        [
            dt.datetime(2019, 7, 1),
            dt.datetime(2019, 10, 1),
            dt.datetime(2020, 1, 1),
            dt.datetime(2020, 4, 1),
            dt.datetime(2020, 7, 1),
        ]
    )
    np.testing.assert_allclose(ticks, expected)


def test_date_odd_hour_start_still_lands_on_midnight():
    # The intraday analogue: a span starting on an odd hour used to select
    # the 2-hour grid, which keeps the start hour's parity and skips
    # midnight. Dropping 2-hour falls back to the day-anchored 3-hour grid.
    vmin, vmax = _date_interval(
        dt.datetime(2024, 3, 1, 21, 0), dt.datetime(2024, 3, 2, 11, 0)
    )
    ticks = DateBreaksLocator().tick_values(vmin, vmax, 6)
    expected = mdates.date2num(
        [
            dt.datetime(2024, 3, 1, 21),
            dt.datetime(2024, 3, 2, 0),
            dt.datetime(2024, 3, 2, 3),
            dt.datetime(2024, 3, 2, 6),
            dt.datetime(2024, 3, 2, 9),
        ]
    )
    np.testing.assert_allclose(ticks, expected)


@settings(max_examples=200, deadline=None)
@given(
    year=st.integers(2000, 2050),
    month=st.integers(1, 12),
    day=st.integers(1, 28),
    length_months=st.integers(13, 24),
    n=st.integers(4, 10),
)
def test_date_span_over_a_year_always_lands_on_january(
    year, month, day, length_months, n
):
    # A span of 13 months or more always straddles a 1 January, and with
    # the drifting steps gone the chosen grid (monthly, quarterly,
    # half-yearly or yearly) always lands a tick on it, wherever the data
    # starts.
    start = dt.datetime(year, month, day)
    end = start + relativedelta(months=length_months)
    vmin, vmax = _date_interval(start, end)
    ticks = mdates.num2date(DateBreaksLocator().tick_values(vmin, vmax, n))
    assert any(d.month == 1 and d.day == 1 for d in ticks)


@settings(max_examples=100, deadline=None)
@given(
    year=st.integers(2000, 2050),
    length_months=st.integers(13, 24),
    n=st.integers(4, 10),
)
def test_date_january_presence_does_not_depend_on_start_month(year, length_months, n):
    # The 2-month drift made January's presence hinge on the start month's
    # parity: even starts rode the even months and skipped it. Sliding the
    # start across all twelve months must not change whether January gets a
    # tick. (The grid's resolution may still shift between monthly and
    # quarterly near a boundary, since equal month counts are unequal
    # durations, but both land on January.)
    def has_january(start_month):
        start = dt.datetime(year, start_month, 1)
        end = start + relativedelta(months=length_months)
        vmin, vmax = _date_interval(start, end)
        ticks = mdates.num2date(DateBreaksLocator().tick_values(vmin, vmax, n))
        return any(d.month == 1 and d.day == 1 for d in ticks)

    assert {has_january(m) for m in range(1, 13)} == {True}


def test_unit_pi_full_turn_places_pi_fractions():
    ticks = TalbotLocator(unit=np.pi).tick_values(0.0, 2 * np.pi)
    np.testing.assert_allclose(ticks, [0, np.pi / 2, np.pi, 3 * np.pi / 2, 2 * np.pi])


def test_unit_pi_half_turn_places_quarters():
    ticks = TalbotLocator(unit=np.pi).tick_values(0.0, np.pi)
    np.testing.assert_allclose(ticks, [0, np.pi / 4, np.pi / 2, 3 * np.pi / 4, np.pi])


def test_unit_identity_is_bit_identical_to_default():
    # unit=1.0 divides and multiplies by 1.0 (exact in IEEE), so the tick
    # path is unchanged. Pin against the direct mizani call -- the same
    # reference test_matches_mizani_directly uses for the default.
    for vmin, vmax in [(0.3, 9.7), (0.4, 9.6), (-3.2, 7.1), (1.0, 2.0)]:
        expected = breaks_extended(n=5, only_inside=True)((vmin, vmax))
        result = TalbotLocator(n=5, unit=1.0).tick_values(vmin, vmax)
        np.testing.assert_array_equal(result, expected)
        np.testing.assert_array_equal(
            result, TalbotLocator(n=5).tick_values(vmin, vmax)
        )


def test_unit_is_scale_invariant_with_loose():
    # unit composes with loose: the search runs in unit-space, so scaling
    # the inputs down and the ticks back up reproduces the same grid.
    u = np.pi
    scaled = TalbotLocator(unit=u, loose=True).tick_values(0.3, 6.0)
    plain = TalbotLocator(loose=True).tick_values(0.3 / u, 6.0 / u)
    np.testing.assert_allclose(scaled, u * plain)


def test_unit_is_scale_invariant_with_nice_numbers():
    u = np.pi
    nn = (1, 2.5, 5)
    scaled = TalbotLocator(unit=u, nice_numbers=nn).tick_values(0.4, 9.6)
    plain = TalbotLocator(nice_numbers=nn).tick_values(0.4 / u, 9.6 / u)
    np.testing.assert_allclose(scaled, u * plain)


@pytest.mark.parametrize("bad", [0.0, -1.0, np.inf, -np.inf, np.nan])
def test_unit_nonpositive_or_nonfinite_raises(bad):
    with pytest.raises(ValueError, match="unit"):
        TalbotLocator(unit=bad)


def test_round_numbers_view_limits_honor_unit():
    # Non-loose unit=pi locator under round_numbers: the view must round to
    # the pi family so the axis ends on a tick. Calibrated: (0.3, 6.0) ->
    # (0, 2*pi), i.e. edges / pi == [0, 2]. The decimal answer would be
    # (0.0, 6.0), where 6.0 is not a pi-multiple.
    with plt.rc_context({"axes.autolimit_mode": "round_numbers"}):
        lo, hi = TalbotLocator(unit=np.pi).view_limits(0.3, 6.0)
    assert lo <= 0.3
    assert hi >= 6.0
    np.testing.assert_allclose([lo, hi], [0.0, 2 * np.pi])
    assert hi != pytest.approx(6.0)


def test_augmented_unions_base_and_extra():
    loc = AugmentedLocator(FixedLocator([0.0, 1.0, 2.0]), [1.5])
    np.testing.assert_allclose(loc(), [0.0, 1.0, 1.5, 2.0])


def test_augmented_collapses_coincident():
    loc = AugmentedLocator(FixedLocator([0.0, 1.0, 2.0]), [1.0])
    np.testing.assert_allclose(loc(), [0.0, 1.0, 2.0])


def test_augmented_accepts_sequence_extra():
    loc = AugmentedLocator(FixedLocator([0.0]), [0.5])
    np.testing.assert_allclose(loc(), [0.0, 0.5])


def test_augmented_drops_non_finite_extra():
    loc = AugmentedLocator(FixedLocator([0.5]), [np.nan, np.inf, -np.inf])
    np.testing.assert_allclose(loc(), [0.5])


def test_augmented_empty_extra_is_base_only():
    loc = AugmentedLocator(FixedLocator([0.0, 1.0]), [])
    np.testing.assert_allclose(loc(), [0.0, 1.0])


def test_augmented_out_of_range_extra_is_kept():
    loc = AugmentedLocator(FixedLocator([0.0, 1.0]), [5.0])
    np.testing.assert_allclose(loc(), [0.0, 1.0, 5.0])


def test_augmented_tick_values_unions():
    loc = AugmentedLocator(TalbotLocator(n=5), [0.5])
    ticks = loc.tick_values(0.0, 1.0)
    assert 0.5 in ticks
    assert ticks.min() <= 0.5 <= ticks.max()


def test_augmented_accepts_locator_extra():
    loc = AugmentedLocator(FixedLocator([0.0, 2.0]), FixedLocator([1.0]))
    np.testing.assert_allclose(loc(), [0.0, 1.0, 2.0])


def test_augmented_set_axis_forwards_to_base():
    fig, ax = plt.subplots()
    x = np.linspace(0.0, 10.0, 50)
    ax.plot(x, np.sin(x))
    ax.xaxis.set_major_locator(AugmentedLocator(TalbotLocator(), [3.3]))
    fig.canvas.draw()
    ticks = ax.xaxis.get_majorticklocs()
    assert 3.3 in ticks  # the extra tick
    assert len(ticks) > 1  # base produced nice ticks -> set_axis reached it
    plt.close(fig)


def test_augmented_view_limits_delegate_to_base():
    fig, ax = plt.subplots()
    ax.plot([0.0, 10.0], [0.0, 1.0])
    base = TalbotLocator(loose=True)
    loc = AugmentedLocator(base, [3.0])
    ax.xaxis.set_major_locator(loc)  # binds the axis to loc and, via set_axis, to base
    np.testing.assert_allclose(loc.view_limits(0.0, 10.0), base.view_limits(0.0, 10.0))
    plt.close(fig)


def test_augmented_nonsingular_delegates_to_base():
    base = LogBreaksLocator()
    loc = AugmentedLocator(base, [1.0])
    assert loc.nonsingular(5.0, 5.0) == base.nonsingular(5.0, 5.0)


def test_augmented_locator_is_public():
    import vanzelfsprekend as vzs
    from vanzelfsprekend.locator import AugmentedLocator as _Direct

    assert vzs.AugmentedLocator is _Direct
    assert "AugmentedLocator" in vzs.__all__


def test_augmented_feature_tick_after_range_frame():
    fig, ax = plt.subplots()
    x, y = _lorentzian_peak()
    ax.plot(x, y)
    range_frame(ax)
    ax.xaxis.set_major_locator(
        AugmentedLocator(
            TalbotLocator(loose=True),
            FeatureLocator(x, y, [lambda x, y: x[np.argmax(y)]]),
        )
    )
    fig.canvas.draw()
    ticks = ax.xaxis.get_majorticklocs()
    assert 17.2 in ticks  # the peak, from the extra
    assert len(ticks) > 1  # plus nice ticks, from the base
    lo, hi = ax.get_xlim()
    assert lo <= x.min()  # spine/view still bounds the data
    assert hi >= x.max()  # spine/view still bounds the data
    plt.close(fig)


def test_named_positions_sequence_form_has_no_names():
    from vanzelfsprekend.locator import _named_positions

    positions, names = _named_positions([np.min, np.max], np.array([0.0, 1.0, 2.0]))
    assert positions == [0.0, 2.0]
    assert names == {}


def test_named_positions_mapping_form_maps_each_name():
    from vanzelfsprekend.locator import _named_positions

    positions, names = _named_positions(
        {"lo": np.min, "hi": np.max}, np.array([0.0, 1.0, 2.0])
    )
    assert positions == [0.0, 2.0]
    assert names == {0.0: ("lo",), 2.0: ("hi",)}


def test_named_positions_coincident_names_collapse_to_a_tuple():
    from vanzelfsprekend.locator import _named_positions

    positions, names = _named_positions(
        {"a": lambda v: v.min(), "b": lambda v: v[0]}, np.array([5.0, 6.0])
    )
    assert positions == [5.0]
    assert names == {5.0: ("a", "b")}


def test_named_positions_named_array_result_raises():
    from vanzelfsprekend.locator import _named_positions

    with pytest.raises(ValueError, match="one position"):
        _named_positions({"q": lambda v: np.quantile(v, (0.25, 0.75))}, np.arange(10.0))


def test_named_positions_drops_non_finite_and_its_name():
    from vanzelfsprekend.locator import _named_positions

    positions, names = _named_positions(
        {"ok": lambda v: v[0], "bad": lambda v: np.nan}, np.array([3.0, 4.0])
    )
    assert positions == [3.0]
    assert names == {3.0: ("ok",)}


def test_named_positions_without_finite_positions_raises():
    from vanzelfsprekend.locator import _named_positions

    with pytest.raises(ValueError, match="finite"):
        _named_positions([lambda v: np.nan], np.array([0.0, 1.0]))
