import matplotlib.pyplot as plt
import numpy as np
import pytest

import vanzelfsprekend as vzs


@pytest.fixture
def labeled_ax():
    fig, ax = plt.subplots()
    rng = np.random.default_rng(0)
    ax.scatter(rng.uniform(0.3, 9.7, 50), rng.uniform(-3.2, 4.1, 50))
    vzs.range_frame(ax)
    vzs.xlabel(ax, "time (s)")
    vzs.ylabel(ax, "voltage")
    fig.canvas.draw()
    yield ax
    plt.close(fig)


def tick_label_bboxes(axis, renderer):
    return [
        t.get_window_extent(renderer)
        for t in axis.get_ticklabels()
        if t.get_text() and t.get_visible()
    ]


def test_xlabel_sits_below_tick_labels_without_overlap(labeled_ax):
    renderer = labeled_ax.figure.canvas.get_renderer()
    label = labeled_ax.xaxis.label.get_window_extent(renderer)
    ticks = tick_label_bboxes(labeled_ax.xaxis, renderer)
    assert ticks
    assert all(not label.overlaps(b) for b in ticks)
    assert label.y1 <= min(b.y0 for b in ticks) + 1


def test_xlabel_right_edge_at_spine_end(labeled_ax):
    renderer = labeled_ax.figure.canvas.get_renderer()
    label = labeled_ax.xaxis.label.get_window_extent(renderer)
    spine_end = labeled_ax.spines["bottom"].get_bounds()[1]
    spine_end_px = labeled_ax.transData.transform((spine_end, 0))[0]
    assert abs(label.x1 - spine_end_px) < 2


def test_xlabel_right_edge_at_spine_end_data_mode():
    fig, ax = plt.subplots()
    rng = np.random.default_rng(0)
    ax.scatter(rng.uniform(0.3, 9.7, 50), rng.uniform(-3.2, 4.1, 50))
    vzs.range_frame(ax, frame="data")
    vzs.xlabel(ax, "time (s)")
    fig.canvas.draw()
    renderer = fig.canvas.get_renderer()
    label = ax.xaxis.label.get_window_extent(renderer)
    spine_end = ax.spines["bottom"].get_bounds()[1]
    spine_end_px = ax.transData.transform((spine_end, 0))[0]
    assert abs(label.x1 - spine_end_px) < 2
    plt.close(fig)


def test_xlabel_flush_aligns_right_edge_with_last_tick_label():
    fig, ax = plt.subplots()
    rng = np.random.default_rng(0)
    ax.scatter(rng.uniform(0.3, 9.7, 50), rng.uniform(-3.2, 4.1, 50))
    vzs.range_frame(ax)
    vzs.xlabel(ax, "time (s)", flush=True)
    fig.canvas.draw()
    renderer = fig.canvas.get_renderer()
    label = ax.xaxis.label.get_window_extent(renderer)
    ticks = tick_label_bboxes(ax.xaxis, renderer)
    right = max(ticks, key=lambda b: b.x1)
    spine_end = ax.spines["bottom"].get_bounds()[1]
    spine_end_px = ax.transData.transform((spine_end, 0))[0]
    assert abs(label.x1 - right.x1) < 2  # right edges flush with last tick label
    assert label.x1 > spine_end_px + 1  # nudged outward past the spine end
    plt.close(fig)


def test_xlabel_flush_clamps_to_spine_end_in_data_mode():
    fig, ax = plt.subplots()
    rng = np.random.default_rng(0)
    ax.scatter(rng.uniform(0.3, 9.7, 50), rng.uniform(-3.2, 4.1, 50))
    vzs.range_frame(ax, frame="data")
    vzs.xlabel(ax, "time (s)", flush=True)
    fig.canvas.draw()
    renderer = fig.canvas.get_renderer()
    label = ax.xaxis.label.get_window_extent(renderer)
    spine_end = ax.spines["bottom"].get_bounds()[1]
    spine_end_px = ax.transData.transform((spine_end, 0))[0]
    assert abs(label.x1 - spine_end_px) < 2  # clamp keeps it at the spine end
    plt.close(fig)


def test_xlabel_flush_falls_back_to_spine_end_without_tick_labels():
    fig, ax = plt.subplots()
    rng = np.random.default_rng(0)
    ax.scatter(rng.uniform(0.3, 9.7, 50), rng.uniform(-3.2, 4.1, 50))
    vzs.range_frame(ax)
    ax.set_xticklabels([])
    vzs.xlabel(ax, "time (s)", flush=True)
    fig.canvas.draw()
    renderer = fig.canvas.get_renderer()
    label = ax.xaxis.label.get_window_extent(renderer)
    spine_end = ax.spines["bottom"].get_bounds()[1]
    spine_end_px = ax.transData.transform((spine_end, 0))[0]
    assert abs(label.x1 - spine_end_px) < 2
    plt.close(fig)


def test_ylabel_above_stacks_over_top_tick_left_aligned():
    fig, ax = plt.subplots()
    rng = np.random.default_rng(0)
    ax.scatter(rng.uniform(0.3, 9.7, 50), rng.uniform(-3.2, 4.1, 50))
    vzs.range_frame(ax)
    vzs.ylabel(ax, "voltage", place="above")
    fig.canvas.draw()
    renderer = fig.canvas.get_renderer()
    label = ax.yaxis.label.get_window_extent(renderer)
    ticks = tick_label_bboxes(ax.yaxis, renderer)
    assert ticks
    top = max(ticks, key=lambda b: b.y1)
    assert all(not label.overlaps(b) for b in ticks)
    assert label.y0 >= top.y1 - 1  # sits above the top tick label
    assert abs(label.x0 - top.x0) < 2  # left edges aligned
    plt.close(fig)


def test_ylabel_invalid_place_raises():
    fig, ax = plt.subplots()
    vzs.range_frame(ax)
    with pytest.raises(ValueError, match="place"):
        vzs.ylabel(ax, "voltage", place="over")
    plt.close(fig)


def test_ylabel_defaults_to_beside_with_top_tick_label(labeled_ax):
    renderer = labeled_ax.figure.canvas.get_renderer()
    label = labeled_ax.yaxis.label.get_window_extent(renderer)
    ticks = tick_label_bboxes(labeled_ax.yaxis, renderer)
    top = max(ticks, key=lambda b: b.y1)
    assert abs(label.y1 - top.y1) < 1
    assert all(not label.overlaps(b) for b in ticks)


def test_labels_follow_after_resize(labeled_ax):
    fig = labeled_ax.figure
    fig.set_size_inches(3, 2)
    fig.canvas.draw()
    renderer = fig.canvas.get_renderer()
    label = labeled_ax.xaxis.label.get_window_extent(renderer)
    spine_end = labeled_ax.spines["bottom"].get_bounds()[1]
    spine_end_px = labeled_ax.transData.transform((spine_end, 0))[0]
    assert abs(label.x1 - spine_end_px) < 2


def test_beside_ylabel_top_aligns_with_top_tick_label():
    fig, ax = plt.subplots()
    rng = np.random.default_rng(0)
    ax.scatter(rng.uniform(0.3, 9.7, 50), rng.uniform(-3.2, 4.1, 50))
    vzs.range_frame(ax)
    vzs.ylabel(ax, "voltage", place="beside")
    fig.canvas.draw()
    renderer = fig.canvas.get_renderer()
    label = ax.yaxis.label.get_window_extent(renderer)
    ticks = tick_label_bboxes(ax.yaxis, renderer)
    top = max(ticks, key=lambda b: b.y1)
    assert abs(label.y1 - top.y1) < 1
    assert all(not label.overlaps(b) for b in ticks)
    plt.close(fig)


def _make_labeled_ax(*, xlabelpad=None, ylabelpad=None):
    fig, ax = plt.subplots()
    rng = np.random.default_rng(0)
    ax.scatter(rng.uniform(0.3, 9.7, 50), rng.uniform(-3.2, 4.1, 50))
    vzs.range_frame(ax)
    vzs.xlabel(ax, "time (s)", labelpad=xlabelpad)
    vzs.ylabel(ax, "voltage", labelpad=ylabelpad)
    fig.canvas.draw()
    return fig, ax


def test_ylabel_labelpad_shifts_right_edge_left():
    fig_default, ax_default = _make_labeled_ax()
    fig_pad, ax_pad = _make_labeled_ax(ylabelpad=20)
    default_x1 = ax_default.yaxis.label.get_window_extent(
        fig_default.canvas.get_renderer()
    ).x1
    pad_x1 = ax_pad.yaxis.label.get_window_extent(fig_pad.canvas.get_renderer()).x1
    expected_shift = (20 - 4) * fig_pad.dpi / 72
    assert abs((default_x1 - pad_x1) - expected_shift) < 1
    plt.close(fig_default)
    plt.close(fig_pad)


def test_xlabel_labelpad_shifts_down():
    fig_default, ax_default = _make_labeled_ax()
    fig_pad, ax_pad = _make_labeled_ax(xlabelpad=20)
    default_y0 = ax_default.xaxis.label.get_window_extent(
        fig_default.canvas.get_renderer()
    ).y0
    pad_y0 = ax_pad.xaxis.label.get_window_extent(fig_pad.canvas.get_renderer()).y0
    expected_shift = (20 - 4) * fig_pad.dpi / 72
    assert abs((default_y0 - pad_y0) - expected_shift) < 1
    plt.close(fig_default)
    plt.close(fig_pad)


def test_beside_ylabel_with_loose_frame_no_overlap():
    fig, ax = plt.subplots()
    rng = np.random.default_rng(0)
    ax.scatter(rng.uniform(0.3, 9.7, 50), rng.uniform(-3.2, 4.1, 50))
    vzs.range_frame(ax, frame="loose")
    vzs.ylabel(ax, "voltage", place="beside")
    fig.canvas.draw()
    renderer = fig.canvas.get_renderer()
    label = ax.yaxis.label.get_window_extent(renderer)
    ticks = tick_label_bboxes(ax.yaxis, renderer)
    assert ticks
    assert all(not label.overlaps(b) for b in ticks)
    top = max(ticks, key=lambda b: b.y1)
    assert abs(label.y1 - top.y1) < 1
    plt.close(fig)


def test_log_axes_labels_anchor_in_log_space():
    fig, ax = plt.subplots()
    ax.set_xscale("log")
    ax.set_yscale("log")
    rng = np.random.default_rng(0)
    x = 10 ** rng.uniform(0.5, 3.5, 60)
    y = 3 * x**0.8 * 10 ** rng.normal(0, 0.15, 60)
    ax.scatter(x, y)
    vzs.range_frame(ax)
    vzs.xlabel(ax, "body mass (g)")
    vzs.ylabel(ax, "metabolic rate", place="beside")
    fig.canvas.draw()

    xmin, xmax = ax.get_xlim()
    top_x_tick = max(ax.xaxis.get_majorticklocs())
    expected_x = (np.log10(top_x_tick) - np.log10(xmin)) / (
        np.log10(xmax) - np.log10(xmin)
    )
    assert ax.xaxis.label.get_position()[0] == pytest.approx(expected_x)

    ymin, ymax = ax.get_ylim()
    top_y_tick = max(ax.yaxis.get_majorticklocs())
    expected_y = (np.log10(top_y_tick) - np.log10(ymin)) / (
        np.log10(ymax) - np.log10(ymin)
    )
    assert ax.yaxis.label.get_position()[1] == pytest.approx(expected_y)
    plt.close(fig)
