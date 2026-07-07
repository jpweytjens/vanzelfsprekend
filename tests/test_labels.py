import matplotlib.pyplot as plt
import numpy as np
import pytest

import tufty


@pytest.fixture
def labeled_ax():
    fig, ax = plt.subplots()
    rng = np.random.default_rng(0)
    ax.scatter(rng.uniform(0.3, 9.7, 50), rng.uniform(-3.2, 4.1, 50))
    tufty.tuftify(ax)
    tufty.xlabel(ax, "time (s)")
    tufty.ylabel(ax, "voltage")
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


def test_ylabel_sits_above_spine_top_without_overlap(labeled_ax):
    renderer = labeled_ax.figure.canvas.get_renderer()
    label = labeled_ax.yaxis.label.get_window_extent(renderer)
    ticks = tick_label_bboxes(labeled_ax.yaxis, renderer)
    assert ticks
    assert all(not label.overlaps(b) for b in ticks)
    spine_top = labeled_ax.spines["left"].get_bounds()[1]
    spine_top_px = labeled_ax.transData.transform((0, spine_top))[1]
    assert label.y0 >= spine_top_px - 1


def test_labels_follow_after_resize(labeled_ax):
    fig = labeled_ax.figure
    fig.set_size_inches(3, 2)
    fig.canvas.draw()
    renderer = fig.canvas.get_renderer()
    label = labeled_ax.xaxis.label.get_window_extent(renderer)
    spine_end = labeled_ax.spines["bottom"].get_bounds()[1]
    spine_end_px = labeled_ax.transData.transform((spine_end, 0))[0]
    assert abs(label.x1 - spine_end_px) < 2


def test_flush_ylabel_top_aligns_with_top_tick_label():
    fig, ax = plt.subplots()
    rng = np.random.default_rng(0)
    ax.scatter(rng.uniform(0.3, 9.7, 50), rng.uniform(-3.2, 4.1, 50))
    tufty.tuftify(ax)
    tufty.ylabel(ax, "voltage", flush=True)
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
    tufty.tuftify(ax)
    tufty.xlabel(ax, "time (s)", labelpad=xlabelpad)
    tufty.ylabel(ax, "voltage", labelpad=ylabelpad)
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


def test_flush_ylabel_with_loose_frame_no_overlap():
    fig, ax = plt.subplots()
    rng = np.random.default_rng(0)
    ax.scatter(rng.uniform(0.3, 9.7, 50), rng.uniform(-3.2, 4.1, 50))
    tufty.tuftify(ax, frame="loose")
    tufty.ylabel(ax, "voltage", flush=True)
    fig.canvas.draw()
    renderer = fig.canvas.get_renderer()
    label = ax.yaxis.label.get_window_extent(renderer)
    ticks = tick_label_bboxes(ax.yaxis, renderer)
    assert ticks
    assert all(not label.overlaps(b) for b in ticks)
    top = max(ticks, key=lambda b: b.y1)
    assert abs(label.y1 - top.y1) < 1
    plt.close(fig)
