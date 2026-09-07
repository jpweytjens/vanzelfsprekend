import datetime
import itertools
import warnings

import matplotlib.dates
import matplotlib.pyplot as plt
import numpy as np
import pytest
from matplotlib.transforms import Bbox

import vanzelfsprekend as vzs
from vanzelfsprekend import direct, lines
from vanzelfsprekend.hook import get_state


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


def lorentzian(f):
    return 650 / (1 + ((f - 17.2) / 0.35) ** 2)


def resonance(figsize=(5, 4)):
    fig, ax = plt.subplots(figsize=figsize)
    f = np.linspace(15.6, 19.4, 500)
    sampled = np.linspace(16, 19, 61)
    rng = np.random.default_rng(0)
    ax.plot(f, lorentzian(f), label="calculated", color="tab:orange", linewidth=1.2)
    ax.scatter(
        sampled,
        lorentzian(sampled) + rng.normal(0, 12, sampled.size),
        s=10,
        color="0.2",
        label="measured",
        zorder=3,
    )
    ax.set_ylim(0, 700)
    return fig, ax


NONE = (None, "None", "", " ")


def assert_no_marker_inside(boxes, dxdy, pts, what):
    for box, (dx, dy) in zip(boxes, dxdy, strict=True):
        grown = Bbox.from_extents(box.x0 - dx, box.y0 - dy, box.x1 + dx, box.y1 + dy)
        hits = [p for p in pts if np.isfinite(p).all() and grown.contains(*p)]
        assert not hits, f"{box} covers a marker of {what}"


# The solver's contract is directional: gap clearance along the sliding axis
# only; across it the anchor sits on the ink, so only the physical extent applies.
def assert_clear_of_ink(ax, texts):
    renderer = ax.figure.canvas.get_renderer()
    boxes = [t.get_window_extent(renderer) for t in texts]
    px_per_pt = ax.figure.dpi / 72.0
    gap_px = 2.0 * px_per_pt
    slack = 0.05  # px: exact-clearance placements are ties, decided by float noise
    along_y = [t.get_va() == "baseline" for t in texts]

    def margins(extent):
        along = extent + gap_px - slack
        across = extent - slack
        return [(across, along) if y else (along, across) for y in along_y]

    state = get_state(ax)
    above_text = (state or {}).get("labels", {}).get("ylabel_above_text")
    for line in ax.get_lines():
        path = line.get_path().transformed(line.get_transform())
        if line.get_linestyle() not in NONE:
            half_lw = line.get_linewidth() / 2 * px_per_pt
            for box, (dx, dy) in zip(boxes, margins(half_lw), strict=True):
                grown = Bbox.from_extents(
                    box.x0 - dx, box.y0 - dy, box.x1 + dx, box.y1 + dy
                )
                assert not path.intersects_bbox(grown, filled=False), (
                    f"{box} crosses {line.get_label()}"
                )
        if line.get_marker() not in NONE:
            r = (line.get_markersize() + line.get_markeredgewidth()) / 2 * px_per_pt
            assert_no_marker_inside(boxes, margins(r), path.vertices, line.get_label())
    for collection in ax.collections:
        pts = collection.get_offset_transform().transform(collection.get_offsets())
        edges = np.asarray(collection.get_linewidths(), dtype=float)
        edge = edges.max() if edges.size else 0.0
        r = (np.sqrt(collection.get_sizes().max()) + edge) / 2 * px_per_pt
        assert_no_marker_inside(boxes, margins(r), pts, collection.get_label())
    for text in ax.texts:
        if text in texts or text is above_text:
            continue
        for box in boxes:
            assert not box.overlaps(text.get_window_extent(renderer))
    for a, b in itertools.combinations(boxes, 2):
        assert not a.overlaps(b)


def test_label_text_color_and_anchor():
    fig, ax = resonance()
    (text,) = vzs.label(ax, "calculated", x=17.5, side="right")
    assert text.get_text() == "calculated"
    assert text.get_color() == "tab:orange"
    assert text.xy == pytest.approx((17.5, lorentzian(17.5)), rel=1e-3)
    assert text.get_ha() == "left"
    plt.close(fig)


def test_label_x_converts_through_the_axis_units():
    fig, ax = plt.subplots()
    dates = [datetime.date(2020, 1, d) for d in range(1, 11)]
    ax.plot(dates, range(10), label="series")
    (text,) = vzs.label(ax, "series", x=datetime.date(2020, 1, 5), side="right")
    fig.canvas.draw()
    assert text.xy[0] == pytest.approx(
        matplotlib.dates.date2num(datetime.date(2020, 1, 5))
    )
    assert text.xy[1] == pytest.approx(4.0)
    plt.close(fig)


def test_label_on_the_right_clears_the_curve_and_the_points():
    fig, ax = resonance()
    texts = vzs.label(ax, "calculated", x=17.5, side="right")
    texts += vzs.label(ax, "measured", x=17.2, side="right")
    fig.canvas.draw()
    assert_clear_of_ink(ax, texts)
    renderer = fig.canvas.get_renderer()
    for text in texts:
        anchor_x = ax.transData.transform(text.xy)[0]
        assert text.get_window_extent(renderer).x0 > anchor_x
    plt.close(fig)


def test_label_stays_on_its_own_side_of_a_crossing_line():
    fig, ax = plt.subplots()
    ax.plot([0.0, 10.0], [5.0, 5.0], label="flat")
    # "_crossing" runs through the right strip, above the anchor.
    ax.plot([4.0, 6.0], [5.4, 5.6], label="_crossing")
    (text,) = vzs.label(ax, "flat", x=4.0, side="right")
    fig.canvas.draw()
    assert_clear_of_ink(ax, [text])
    box = text.get_window_extent(fig.canvas.get_renderer())
    y_anchor = ax.transData.transform((4.0, 5.0))[1]
    y_cross = ax.transData.transform((4.0, 5.4))[1]
    # Anchor inside its own pin sorts above it, but the crossing pin sits
    # above that, so the label parks between the two.
    assert y_anchor < (box.y0 + box.y1) / 2 < y_cross
    plt.close(fig)


def test_label_moves_when_ink_enters_the_strip_and_returns_when_it_leaves():
    fig, ax = resonance()
    (text,) = vzs.label(ax, "calculated", x=18.5, side="right")
    fig.canvas.draw()
    rest = text.get_position()
    # A thick bar along the curve's own tail merges with that pin and raises
    # its top by about 5 points, so the label must climb by about as much.
    (bar,) = ax.plot([18.55, 19.4], [lorentzian(18.5)] * 2, linewidth=12, label="_bar")
    fig.canvas.draw()
    assert text.get_position()[1] - rest[1] > 3.0
    assert_clear_of_ink(ax, [text])
    bar.remove()
    fig.canvas.draw()
    assert text.get_position() == pytest.approx(rest)
    plt.close(fig)


def test_label_re_solves_on_resize():
    fig, ax = resonance()
    texts = vzs.label(ax, "calculated", x=17.5, side="right")
    texts += vzs.label(ax, "measured", x=17.2, side="right")
    fig.canvas.draw()
    fig.set_size_inches(8, 2.5)
    fig.canvas.draw()
    assert_clear_of_ink(ax, texts)
    plt.close(fig)


def test_default_side_puts_both_doumont_labels_on_the_right():
    # Pins SIDE_TOLERANCE to its provenance: below 3.0 the summit label
    # flipped left in the 2026-09-07 sweep.
    fig, ax = resonance()
    texts = vzs.label(ax, "measured", x=17.2)
    texts += vzs.label(ax, "calculated", x=17.5)
    fig.canvas.draw()
    assert [t.get_ha() for t in texts] == ["left", "left"]
    assert_clear_of_ink(ax, texts)
    plt.close(fig)


def test_label_returns_a_copy_so_callers_cannot_grow_the_group():
    fig, ax = resonance()
    first = vzs.label(ax, "calculated", x=17.5, side="right")
    first += vzs.label(ax, "measured", x=17.2, side="right")
    groups = get_state(ax)["direct"]
    assert [len(g["texts"]) for g in groups] == [1, 1]
    fig.canvas.draw()
    fig.set_size_inches(8, 2.5)
    fig.canvas.draw()
    assert_clear_of_ink(ax, first)
    plt.close(fig)


def test_label_replaces_its_own_group_and_hides_the_legend():
    fig, ax = resonance()
    ax.legend()
    first = vzs.label(ax, "calculated", x=17.5, side="right")
    second = vzs.label(ax, "calculated", x=18.0, side="right")
    assert first[0] not in ax.texts
    assert second[0] in ax.texts
    assert not ax.get_legend().get_visible()
    plt.close(fig)


def test_label_validates_arguments():
    fig, ax = resonance()
    with pytest.raises(ValueError, match="x= or y=, not both"):
        vzs.label(ax, "calculated", x=17.0, y=100.0)
    with pytest.raises(ValueError, match="side must be one of"):
        vzs.label(ax, "calculated", x=17.0, side="north")
    with pytest.raises(ValueError, match="give x= or y="):
        vzs.label(ax, "calculated")
    with pytest.raises(ValueError, match="no artist labelled"):
        vzs.label(ax, "simulated", x=17.0)
    plt.close(fig)


def test_label_composes_with_axis_labels_in_both_orders():
    for first in ("axis", "direct"):
        fig, ax = resonance()
        vzs.distill(ax, frame="loose")
        if first == "axis":
            vzs.xlabel(ax, "frequency (GHz)")
            vzs.ylabel(ax, "output power (mW)", place="above")
            texts = vzs.label(ax, "calculated", x=17.5, side="right")
        else:
            texts = vzs.label(ax, "calculated", x=17.5, side="right")
            vzs.xlabel(ax, "frequency (GHz)")
            vzs.ylabel(ax, "output power (mW)", place="above")
        fig.canvas.draw()
        assert ax.xaxis.label.get_text() == "frequency (GHz)"
        above = [t for t in ax.texts if t.get_text() == "output power (mW)"]
        assert len(above) == 1
        assert_clear_of_ink(ax, texts)
        state = get_state(ax)
        # the axis-label dict is untouched
        assert state["labels"]["ylabel_place"] == "above"
        assert isinstance(state["direct"], list)
        assert {"labels", "direct"} <= set(state["appliers"])
        plt.close(fig)


def test_label_before_distill_survives_the_treatment():
    fig, ax = resonance()
    texts = vzs.label(ax, "measured", x=17.2, side="right")
    vzs.distill(ax, frame="loose")
    fig.canvas.draw()
    assert_clear_of_ink(ax, texts)
    plt.close(fig)


def test_above_ylabel_is_furniture_not_ink(monkeypatch):
    # The managed above-label is an `ax.text` child. The applier must hand
    # it to `_ink` as excluded, whatever else is on the axes.
    fig, ax = plt.subplots()
    ax.plot([0.0, 1.0], [1.0, 1.0], label="top")
    vzs.distill(ax, frame="loose")
    above = vzs.ylabel(ax, "output power (mW)", place="above")
    seen = []
    real_ink = direct._ink

    def spy(ax_, exclude):
        seen.append(set(exclude))
        return real_ink(ax_, exclude)

    monkeypatch.setattr(direct, "_ink", spy)
    vzs.label(ax, "top", x=0.5)
    fig.canvas.draw()
    assert seen
    assert all(above in exclude for exclude in seen)
    plt.close(fig)


@pytest.mark.parametrize(
    ("helper", "side"),
    [
        ({"x": 5.0}, "above"),
        ({"x": 5.0}, "below"),
        ({"y": 0.0}, "right"),
        ({"y": 0.0}, "left"),
    ],
)
def test_single_label_side_not_perpendicular_to_its_helper_stays_at_the_anchor(
    helper, side
):
    # x= picks the anchor; with side="above" it must not also be read as the
    # strip's y base. The text sits pad above (or beside) the anchor itself.
    fig, ax = plt.subplots()
    # A gentle slope, so y=0 has one crossing (a flat line at y=0 has none).
    ax.plot([0.0, 10.0], [-0.5, 0.5], label="sloped")
    ax.set_xlim(0, 10)
    ax.set_ylim(-5, 5)
    (text,) = vzs.label(ax, "sloped", side=side, **helper)
    fig.canvas.draw()
    assert text.xy == pytest.approx((5.0, 0.0))
    box = text.get_window_extent(fig.canvas.get_renderer())
    ax_x, ax_y = ax.transData.transform((5.0, 0.0))
    pad_px = 4.0 * fig.dpi / 72.0
    if side == "above":
        assert box.y0 == pytest.approx(ax_y + pad_px, abs=1.0)
        assert (box.x0 + box.x1) / 2 == pytest.approx(ax_x, abs=1.0)
    elif side == "below":
        assert box.y1 == pytest.approx(ax_y - pad_px, abs=1.0)
        assert (box.x0 + box.x1) / 2 == pytest.approx(ax_x, abs=1.0)
    elif side == "right":
        assert box.x0 == pytest.approx(ax_x + pad_px, abs=1.0)
        assert box.y0 > ax_y  # slid off its own line, upward
    else:
        assert box.x1 == pytest.approx(ax_x - pad_px, abs=1.0)
        assert box.y0 > ax_y
    plt.close(fig)


def test_label_clears_a_big_marker_on_its_own_line():
    fig, ax = plt.subplots()
    ax.plot([5.0], [0.0], "o", markersize=40, label="dot")
    ax.set_xlim(0, 10)
    ax.set_ylim(-5, 5)
    (text,) = vzs.label(ax, "dot", side="right")
    fig.canvas.draw()
    assert_clear_of_ink(ax, [text])
    box = text.get_window_extent(fig.canvas.get_renderer())
    ax_y = ax.transData.transform((5.0, 0.0))[1]
    # The strip starts pad right of the centre, inside the marker, so the
    # marker pins it and the text slides up past the marker's radius.
    assert box.y0 >= ax_y + 20.0 * fig.dpi / 72.0 - 1.0
    plt.close(fig)


def test_label_seaborn_shaped_axes_after_set_label():
    fig, ax = plt.subplots()
    (data,) = ax.plot([0.0, 10.0], [0.0, 1.0])  # _child0
    ax.plot([], [], label="A")  # empty legend proxy
    with pytest.raises(ValueError, match="set_label"):
        vzs.label(ax, "A", x=5.0)
    data.set_label("A")
    (text,) = vzs.label(ax, "A", x=5.0, side="right")
    assert text.get_text() == "A"
    assert text.xy == pytest.approx((5.0, 0.5))
    plt.close(fig)


def test_label_on_a_single_point_needs_no_anchor():
    fig, ax = plt.subplots()
    ax.scatter(np.linspace(0, 1, 30), np.linspace(0, 1, 30), s=8, color="0.7")
    ax.scatter([0.5], [0.5], s=20, color="0.1", label="Belgium")
    (text,) = vzs.label(ax, "Belgium", side="right")
    fig.canvas.draw()
    assert text.xy == (0.5, 0.5)
    assert_clear_of_ink(ax, [text])
    plt.close(fig)


def wall(ax, x0, x1, y0, y1, n=40):
    xs = np.linspace(x0, x1, n)
    ys = np.linspace(y0, y1, n)
    gx, gy = np.meshgrid(xs, ys)
    ax.scatter(gx.ravel(), gy.ravel(), s=6, color="0.6", label="_wall")


def test_side_defaults_to_right_when_it_fits():
    fig, ax = plt.subplots()
    ax.plot([0.0, 10.0], [0.0, 0.0], label="flat")
    (text,) = vzs.label(ax, "flat", x=5.0)
    fig.canvas.draw()
    assert text.get_ha() == "left"
    assert text.get_window_extent().x0 > ax.transData.transform(text.xy)[0]
    plt.close(fig)


def test_side_falls_to_left_when_right_is_blocked():
    fig, ax = plt.subplots()
    ax.plot([0.0, 10.0], [0.0, 0.0], label="flat")
    wall(ax, 5.05, 8.0, -3.0, 3.0)
    ax.set_xlim(0, 10)
    ax.set_ylim(-5, 5)
    (text,) = vzs.label(ax, "flat", x=5.0)
    fig.canvas.draw()
    assert text.get_ha() == "right"
    assert text.get_window_extent().x1 < ax.transData.transform(text.xy)[0]
    assert_clear_of_ink(ax, [text])
    plt.close(fig)


def test_side_takes_smallest_displacement_when_none_is_within_tolerance():
    fig, ax = plt.subplots()
    ax.plot([0.0, 10.0], [0.0, 0.0], label="flat")
    wall(ax, 5.05, 8.0, -0.6, 0.6)  # right: the label must climb over a short wall
    wall(ax, 2.0, 4.95, -3.0, 3.0)  # left: a tall one
    ax.set_xlim(0, 10)
    ax.set_ylim(-5, 5)
    (text,) = vzs.label(ax, "flat", x=5.0)
    fig.canvas.draw()
    assert_clear_of_ink(ax, [text])
    assert text.get_ha() in ("left", "center")  # right or above, both beat left
    plt.close(fig)


def test_all_sides_over_capacity_warns_once_and_still_draws():
    # Over capacity means trapped between two pins, not merely blocked: a
    # single wall is slid past. The guards sit about 11 px from the anchor,
    # inside the above and below bands and too close for a label on the
    # right and left, while the 0.2 unit gap between their halves is about
    # 7 px, narrower than the word.
    fig, ax = plt.subplots()
    ax.plot([0.0, 10.0], [0.0, 0.0], label="flat")
    for level in (0.3, -0.3):
        ax.plot([0.0, 4.9], [level, level], color="0.6")
        ax.plot([5.1, 10.0], [level, level], color="0.6")
    ax.set_xlim(0, 10)
    ax.set_ylim(-5, 5)
    with pytest.warns(UserWarning, match="do not fit on any side"):
        (text,) = vzs.label(ax, "flat", x=5.0)
    fig.canvas.draw()
    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter("always")
        fig.canvas.draw()  # warned once, not on every draw
    assert not [w for w in caught if "do not fit" in str(w.message)]
    assert text in ax.texts
    plt.close(fig)


def test_explicit_side_is_kept_even_when_blocked():
    fig, ax = plt.subplots()
    ax.plot([0.0, 10.0], [0.0, 0.0], label="flat")
    wall(ax, 5.05, 8.0, -3.0, 3.0)
    ax.set_xlim(0, 10)
    ax.set_ylim(-5, 5)
    (text,) = vzs.label(ax, "flat", x=5.0, side="right")
    fig.canvas.draw()
    assert text.get_ha() == "left"
    assert_clear_of_ink(ax, [text])  # slid above the wall, still on the right
    plt.close(fig)


def three_flat_lines(ax):
    x = np.linspace(0.0, 10.0, 50)
    for level, name in [(1.0, "low"), (2.0, "mid"), (3.0, "high")]:
        ax.plot(x, np.full_like(x, level), label=name)


def test_column_stacks_in_order_beside_a_shared_helper():
    fig, ax = plt.subplots()
    three_flat_lines(ax)
    texts = vzs.label(ax, ["low", "mid", "high"], x=5.0)
    fig.canvas.draw()
    assert_clear_of_ink(ax, texts)
    renderer = fig.canvas.get_renderer()
    boxes = [t.get_window_extent(renderer) for t in texts]
    centres = [(b.y0 + b.y1) / 2 for b in boxes]
    assert centres == sorted(centres)
    helper_x = ax.transData.transform((5.0, 0.0))[0]
    pad_px = 4.0 * fig.dpi / 72.0
    for box in boxes:
        # left edges share the helper
        assert box.x0 == pytest.approx(helper_x + pad_px, abs=1.0)
    plt.close(fig)


def test_column_keeps_order_across_a_crossing_curve():
    fig, ax = plt.subplots()
    three_flat_lines(ax)
    # through the middle label's strip, above it
    ax.plot([4.0, 6.0], [2.15, 2.6], label="_cross")
    texts = vzs.label(ax, ["low", "mid", "high"], x=5.0, side="right")
    fig.canvas.draw()
    assert_clear_of_ink(ax, texts)
    renderer = fig.canvas.get_renderer()
    boxes = [t.get_window_extent(renderer) for t in texts]
    centres = [(box.y0 + box.y1) / 2 for box in boxes]
    assert centres == sorted(centres)
    mid_anchor = ax.transData.transform((5.0, 2.0))[1]
    cross_low = ax.transData.transform((5.0, 2.15))[1]
    # parked under the crossing, above its own line
    assert mid_anchor < centres[1] < cross_low
    plt.close(fig)


def test_column_takes_the_left_when_told():
    fig, ax = plt.subplots()
    three_flat_lines(ax)
    texts = vzs.label(ax, ["low", "mid", "high"], x=5.0, side="left")
    fig.canvas.draw()
    helper_x = ax.transData.transform((5.0, 0.0))[0]
    for text in texts:
        assert text.get_ha() == "right"
        assert text.get_window_extent().x1 < helper_x
    plt.close(fig)


def test_column_on_y_slides_in_x():
    fig, ax = plt.subplots()
    x = np.linspace(0.0, 10.0, 50)
    ax.plot(x, x, label="rising")
    ax.plot(x, 10 - x, label="falling")
    texts = vzs.label(ax, ["falling", "rising"], y=7.0)
    fig.canvas.draw()
    assert_clear_of_ink(ax, texts)
    assert {t.get_va() for t in texts} <= {"bottom", "top"}
    xs = [t.get_window_extent().x0 for t in texts]
    assert xs[0] < xs[1]  # falling crosses y=7 at x=3, rising at x=7
    plt.close(fig)


def test_column_rejects_a_side_parallel_to_its_helper_and_a_missing_helper():
    fig, ax = plt.subplots()
    three_flat_lines(ax)
    with pytest.raises(ValueError, match="a column on x= can only go right or left"):
        vzs.label(ax, ["low", "mid"], x=5.0, side="above")
    with pytest.raises(ValueError, match="a column of labels needs x= or y="):
        vzs.label(ax, ["low", "mid"])
    with pytest.raises(ValueError, match="no names given"):
        vzs.label(ax, [], x=5.0)
    plt.close(fig)


def test_second_group_sees_the_first_as_ink():
    fig, ax = plt.subplots()
    three_flat_lines(ax)
    first = vzs.label(ax, "mid", x=5.0, side="right")
    ax.plot([0.0, 10.0], [2.05, 2.05], label="twin", color="0.5")
    second = vzs.label(ax, "twin", x=5.0, side="right")
    fig.canvas.draw()
    assert_clear_of_ink(ax, first + second)
    plt.close(fig)


def test_restore_removes_labels_and_brings_the_legend_back():
    fig, ax = resonance()
    ax.legend()
    texts = vzs.label(ax, "calculated", x=17.5)
    texts += vzs.label(ax, ["calculated", "measured"], x=18.5)
    vzs.restore(ax)
    assert all(text not in ax.texts for text in texts)
    assert ax.get_legend().get_visible()
    plt.close(fig)


def test_restore_after_axis_and_direct_labels_in_both_orders():
    for first in ("axis", "direct"):
        fig, ax = resonance()
        vzs.distill(ax)
        calls = [
            lambda ax=ax: vzs.ylabel(ax, "output power (mW)", place="above"),
            lambda ax=ax: vzs.label(ax, "calculated", x=17.5),
        ]
        if first == "direct":
            calls.reverse()
        for call in calls:
            call()
        fig.canvas.draw()
        vzs.restore(ax)
        remaining = {t.get_text() for t in ax.texts}
        assert "calculated" not in remaining
        assert "output power (mW)" not in remaining
        assert get_state(ax) is None
        fig.canvas.draw()  # nothing re-applies after restore
        plt.close(fig)


def test_accessor_label_matches_the_function():
    vzs.register()
    fig, ax = resonance()
    (text,) = ax.vzs.label("calculated", x=17.5, side="right")
    assert text.get_text() == "calculated"
    assert "label" in vzs.__all__
    plt.close(fig)
