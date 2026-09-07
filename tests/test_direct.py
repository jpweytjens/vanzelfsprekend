import matplotlib.pyplot as plt
import numpy as np
import pytest
from matplotlib.transforms import Bbox

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


def test_ink_collects_segments_points_and_boxes(ax):
    ax.plot([0, 1, 2], [0, 1, 0], linewidth=2.0)
    ax.scatter([0.5], [0.5], s=16, linewidths=0)
    text = ax.text(1, 1, "hello")
    ax.figure.canvas.draw()
    ink = direct._ink(ax, set())
    assert ink.segments.shape == (2, 2, 2)
    px_per_pt = ax.figure.dpi / 72.0
    np.testing.assert_allclose(ink.half_widths, px_per_pt)  # linewidth 2 pt, half of it
    assert ink.points.shape == (1, 2)
    np.testing.assert_allclose(ink.radii, 2.0 * px_per_pt)  # sqrt(16) / 2 pt
    assert len(ink.boxes) == 1
    assert ink.boxes[0].overlaps(text.get_window_extent())


def test_ink_includes_line_markers_and_skips_an_unstroked_line(ax):
    ax.plot([5.0], [0.0], "o", markersize=40, markeredgewidth=2)
    ax.plot([0.0, 1.0], [0.0, 1.0], "s-", markersize=6, markeredgewidth=0)
    ax.figure.canvas.draw()
    ink = direct._ink(ax, set())
    px_per_pt = ax.figure.dpi / 72.0
    assert ink.segments.shape == (1, 2, 2)  # only the stroked line has a segment
    assert ink.points.shape == (3, 2)  # one big dot, two squares
    np.testing.assert_allclose(
        sorted(ink.radii), [3.0 * px_per_pt, 3.0 * px_per_pt, 21.0 * px_per_pt]
    )


def test_ink_scatter_radius_includes_the_edge_width(ax):
    ax.scatter([0.5], [0.5], s=16, linewidths=2)
    ax.figure.canvas.draw()
    px_per_pt = ax.figure.dpi / 72.0
    np.testing.assert_allclose(direct._ink(ax, set()).radii, (2.0 + 1.0) * px_per_pt)


def test_ink_skips_a_masked_scatter_point(ax):
    x = np.ma.array([0.0, 1.0], mask=[False, True])
    ax.scatter(x, [0.0, 1.0])
    ax.figure.canvas.draw()
    ink = direct._ink(ax, set())
    assert ink.points.shape == (1, 2)


def test_ink_skips_excluded_invisible_and_nan(ax):
    (line,) = ax.plot([0, 1, np.nan, 2, 3], [0, 1, np.nan, 2, 3])
    hidden = ax.scatter([0.5], [0.5])
    hidden.set_visible(False)
    text = ax.text(1, 1, "skip me")
    ax.figure.canvas.draw()
    ink = direct._ink(ax, {text})
    assert ink.segments.shape == (2, 2, 2)  # the NaN break drops two segments
    assert ink.points.shape == (0, 2)
    assert ink.boxes == []
    assert direct._ink(ax, {line, text}).segments.shape == (0, 2, 2)


def test_merge_joins_intervals_within_gap():
    merged = direct._merge([(10.0, 12.0), (0.0, 5.0), (6.0, 8.0), (30.0, 31.0)], 1.5)
    np.testing.assert_allclose(merged, [[0.0, 8.0], [10.0, 12.0], [30.0, 31.0]])
    assert direct._merge([], 1.0).shape == (0, 2)


def test_pins_from_a_segment_crossing_the_strip():
    # Sliding along y (axis 1); strip is x in [10, 20]. A segment from
    # (0, 0) to (40, 40) enters at y=10, leaves at y=20; half width 1.
    ink = direct.Ink(
        segments=np.array([[[0.0, 0.0], [40.0, 40.0]]]),
        half_widths=np.array([1.0]),
        points=np.zeros((0, 2)),
        radii=np.zeros(0),
        boxes=[],
    )
    pins = direct._pins(ink, (10.0, 20.0), 1, 0.0)
    np.testing.assert_allclose(
        pins, [[8.0, 22.0]]
    )  # [10-1-1, 20+1+1]: strip widened by w, then padded by w


def test_pins_ignore_segments_outside_the_strip_and_keep_parallel_ones_inside():
    ink = direct.Ink(
        segments=np.array(
            [
                [[30.0, 0.0], [40.0, 5.0]],  # entirely right of the strip
                [[15.0, 50.0], [15.0, 60.0]],  # vertical, inside the strip
            ]
        ),
        half_widths=np.array([0.5, 0.5]),
        points=np.zeros((0, 2)),
        radii=np.zeros(0),
        boxes=[],
    )
    pins = direct._pins(ink, (10.0, 20.0), 1, 0.0)
    np.testing.assert_allclose(pins, [[49.5, 60.5]])


def test_pins_from_points_and_boxes():
    ink = direct.Ink(
        segments=np.zeros((0, 2, 2)),
        half_widths=np.zeros(0),
        points=np.array([[12.0, 100.0], [25.0, 200.0], [21.0, 300.0]]),
        radii=np.array([2.0, 2.0, 2.0]),
        boxes=[
            Bbox.from_extents(5.0, 400.0, 11.0, 410.0),
            Bbox.from_extents(50.0, 0.0, 60.0, 1.0),
        ],
    )
    pins = direct._pins(ink, (10.0, 20.0), 1, 0.0)
    # point at x=12 is inside; x=25 is out; x=21 with radius 2 touches; the
    # first box reaches x=11 and counts, the second does not.
    np.testing.assert_allclose(pins, [[98.0, 102.0], [298.0, 302.0], [400.0, 410.0]])


def test_pins_slide_along_x_for_above_and_below():
    # axis 0: strip bounds y; a horizontal segment inside it pins an x-interval.
    ink = direct.Ink(
        segments=np.array([[[100.0, 15.0], [130.0, 15.0]]]),
        half_widths=np.array([1.0]),
        points=np.zeros((0, 2)),
        radii=np.zeros(0),
        boxes=[],
    )
    np.testing.assert_allclose(direct._pins(ink, (10.0, 20.0), 0, 0.0), [[99.0, 131.0]])
