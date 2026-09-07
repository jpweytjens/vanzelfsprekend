import matplotlib.pyplot as plt
import numpy as np
import pytest

from vanzelfsprekend import direct, lines


@pytest.fixture
def ax():
    fig, ax = plt.subplots()
    yield ax
    plt.close(fig)


def test_find_by_label_and_by_artist(ax):
    (line,) = ax.plot([0, 1], [0, 1], label="alpha")
    cloud = ax.scatter([0, 1], [1, 0], label="beta")
    assert direct._find(ax, "alpha") is line
    assert direct._find(ax, "beta") is cloud
    assert direct._find(ax, cloud) is cloud


def test_find_missing_lists_present_labels(ax):
    ax.plot([0, 1], [0, 1], label="alpha")
    ax.plot([0, 1], [1, 0])  # auto-labelled, not listed
    with pytest.raises(ValueError, match=r"no artist labelled 'gamma'.*\['alpha'\]"):
        direct._find(ax, "gamma")


def test_find_duplicate_raises(ax):
    ax.plot([0, 1], [0, 1], label="alpha")
    ax.plot([0, 1], [1, 0], label="alpha")
    with pytest.raises(ValueError, match="2 artists labelled 'alpha'"):
        direct._find(ax, "alpha")


def test_find_prefers_the_drawn_artist_over_an_empty_proxy(ax):
    # seaborn's shape: the data line is `_child0`, the legend text sits on
    # an empty proxy. Naming the drawn line is the whole recipe.
    (data,) = ax.plot([0, 1], [0, 1])
    (proxy,) = ax.plot([], [], label="A")
    assert direct._find(ax, "A") is proxy  # the only match, empty or not
    data.set_label("A")
    assert direct._find(ax, "A") is data  # drawn beats empty
    ax.plot([0, 1], [1, 0], label="A")
    with pytest.raises(ValueError, match="2 artists labelled 'A'"):
        direct._find(ax, "A")  # two drawn, the artist must be passed


def test_anchor_on_an_empty_proxy_points_at_set_label(ax):
    (proxy,) = ax.plot([], [], label="A")
    with pytest.raises(ValueError, match="name the drawn artist with set_label"):
        direct._anchor(ax, proxy, ("x", 0.5))


def test_anchor_on_line_crossing_is_interpolated(ax):
    (line,) = ax.plot([0.0, 10.0], [0.0, 20.0], label="alpha")
    assert direct._anchor(ax, line, ("x", 2.5)) == pytest.approx((2.5, 5.0))
    assert direct._anchor(ax, line, ("y", 10.0)) == pytest.approx((5.0, 10.0))


def test_anchor_on_log_axis_interpolates_in_log_space(ax):
    ax.set_xscale("log")
    (line,) = ax.plot([1.0, 100.0], [0.0, 2.0], label="alpha")
    # Halfway in log x is x = 10, and the line is straight in display space.
    assert direct._anchor(ax, line, ("x", 10.0)) == pytest.approx((10.0, 1.0))


def test_anchor_y_takes_first_crossing_in_data_order(ax):
    (line,) = ax.plot([0.0, 1.0, 2.0], [0.0, 2.0, 0.0], label="peak")
    assert direct._anchor(ax, line, ("y", 1.0)) == pytest.approx((0.5, 1.0))


def test_anchor_outside_extent_or_in_gap_raises(ax):
    (line,) = ax.plot(
        [0.0, 1.0, np.nan, 3.0, 4.0], [0.0, 1.0, np.nan, 3.0, 4.0], label="gappy"
    )
    with pytest.raises(ValueError, match="x=9 is outside 'gappy'"):
        direct._anchor(ax, line, ("x", 9.0))
    with pytest.raises(ValueError, match="x=2 is outside 'gappy'"):
        direct._anchor(ax, line, ("x", 2.0))


def test_anchor_on_scatter_is_nearest_point(ax):
    cloud = ax.scatter([0.0, 1.0, 2.0], [5.0, 6.0, 7.0], label="cloud")
    assert direct._anchor(ax, cloud, ("x", 1.2)) == pytest.approx((1.0, 6.0))
    assert direct._anchor(ax, cloud, ("y", 6.9)) == pytest.approx((2.0, 7.0))
    with pytest.raises(ValueError, match="x=5 is outside 'cloud'"):
        direct._anchor(ax, cloud, ("x", 5.0))


def test_anchor_on_masked_scatter_skips_masked_points(ax):
    x = np.ma.array([0.0, 1.0, 2.0], mask=[False, True, False])
    cloud = ax.scatter(x, [5.0, 6.0, 7.0], label="cloud")
    assert direct._anchor(ax, cloud, ("y", 6.0)) == pytest.approx((2.0, 7.0))
    anchor = direct._anchor(ax, cloud, ("x", 1.0))
    assert anchor == pytest.approx((0.0, 5.0)) or anchor == pytest.approx((2.0, 7.0))


def test_anchor_on_fully_masked_scatter_raises(ax):
    x = np.ma.array([0.0, 1.0], mask=[True, True])
    cloud = ax.scatter(x, [5.0, 6.0], label="cloud")
    assert not direct._drawn(cloud)
    with pytest.raises(ValueError, match="'cloud' has no finite point"):
        direct._anchor(ax, cloud, ("x", 0.0))


def test_anchor_without_helper_needs_a_single_point(ax):
    dot = ax.scatter([3.0], [4.0], label="dot")
    (line,) = ax.plot([0, 1], [0, 1], label="alpha")
    assert direct._anchor(ax, dot, None) == (3.0, 4.0)
    with pytest.raises(ValueError, match="'alpha' has 2 points; give x= or y="):
        direct._anchor(ax, line, None)


def test_anchor_without_finite_points_raises(ax):
    (line,) = ax.plot([np.nan, np.nan], [1.0, 2.0], label="void")
    with pytest.raises(ValueError, match="'void' has no finite point"):
        direct._anchor(ax, line, ("x", 0.0))


def test_artist_color_reads_line_and_scatter(ax):
    (line,) = ax.plot([0, 1], [0, 1], color="red")
    cloud = ax.scatter([0], [0], color="blue")
    assert lines._artist_color(line) == "red"
    np.testing.assert_allclose(lines._artist_color(cloud), (0.0, 0.0, 1.0, 1.0))
