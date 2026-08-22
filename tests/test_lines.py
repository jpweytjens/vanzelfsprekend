import datetime
import itertools

import matplotlib
import matplotlib.pyplot as plt
import numpy as np
import pytest

import vanzelfsprekend as vfs
from vanzelfsprekend.lines import _stack


def test_stack_passthrough_when_separated():
    desired = np.array([0.0, 100.0, 200.0])
    heights = np.array([10.0, 10.0, 10.0])
    np.testing.assert_allclose(_stack(desired, heights, 2.0), desired)


def test_stack_centers_coincident_pair_on_mean():
    desired = np.array([50.0, 50.0])
    heights = np.array([10.0, 10.0])
    np.testing.assert_allclose(_stack(desired, heights, 2.0), [44.0, 56.0])


def test_stack_leaves_far_neighbours_untouched():
    desired = np.array([0.0, 50.0, 51.0, 200.0])
    heights = np.full(4, 10.0)
    placed = _stack(desired, heights, 2.0)
    assert placed[0] == 0.0
    assert placed[3] == 200.0
    np.testing.assert_allclose(placed[1:3], [44.5, 56.5])


def test_stack_keeps_order_and_gaps_on_random_input():
    rng = np.random.default_rng(0)
    desired = rng.uniform(0, 100, 20)
    heights = rng.uniform(8, 16, 20)
    placed = _stack(desired, heights, 2.0)
    order = np.argsort(desired, kind="stable")
    separations = np.diff(placed[order])
    required = (heights[order][:-1] + heights[order][1:]) / 2 + 2.0
    assert np.all(separations >= required - 1e-9)


def test_stack_preserves_index_order_of_unsorted_input():
    desired = np.array([50.0, 0.0])
    heights = np.array([10.0, 10.0])
    np.testing.assert_allclose(_stack(desired, heights, 2.0), [50.0, 0.0])


def test_stack_empty_and_single():
    assert _stack(np.array([]), np.array([]), 2.0).size == 0
    np.testing.assert_allclose(_stack(np.array([7.0]), np.array([10.0]), 2.0), [7.0])


def converging_lines(ax):
    x = np.linspace(0.0, 10.0, 200)
    for asymptote, name in [(1.00, "alpha"), (1.02, "beta"), (1.04, "gamma")]:
        ax.plot(x, asymptote - np.exp(-x), label=name)


@pytest.fixture
def converging_ax():
    fig, ax = plt.subplots()
    converging_lines(ax)
    vfs.range_frame(ax)
    texts = vfs.line_labels(ax)
    fig.canvas.draw()
    yield ax, texts
    plt.close(fig)


def label_bboxes(ax, texts):
    renderer = ax.figure.canvas.get_renderer()
    return [t.get_window_extent(renderer) for t in texts]


def test_end_labels_do_not_overlap(converging_ax):
    ax, texts = converging_ax
    boxes = label_bboxes(ax, texts)
    assert len(boxes) == 3
    assert all(not a.overlaps(b) for a, b in itertools.combinations(boxes, 2))


def test_end_labels_keep_end_value_order(converging_ax):
    ax, texts = converging_ax
    ends = [line.get_ydata()[-1] for line in ax.get_lines()]
    centers = [(b.y0 + b.y1) / 2 for b in label_bboxes(ax, texts)]
    assert np.argsort(ends).tolist() == np.argsort(centers).tolist()


def test_labels_take_line_colors(converging_ax):
    ax, texts = converging_ax
    for line, text in zip(ax.get_lines(), texts, strict=True):
        assert text.get_color() == line.get_color()


def test_separated_labels_stay_at_their_lines():
    fig, ax = plt.subplots()
    x = np.linspace(0.0, 10.0, 200)
    for asymptote, name in [(1.0, "alpha"), (3.0, "beta"), (5.0, "gamma")]:
        ax.plot(x, asymptote - np.exp(-x), label=name)
    vfs.range_frame(ax)
    texts = vfs.line_labels(ax)
    fig.canvas.draw()
    renderer = fig.canvas.get_renderer()
    for line, text in zip(ax.get_lines(), texts, strict=True):
        anchor_y = ax.transData.transform((10.0, line.get_ydata()[-1]))[1]
        box = text.get_window_extent(renderer)
        assert abs((box.y0 + box.y1) / 2 - anchor_y) < 2
    plt.close(fig)


def test_unlabeled_and_all_nan_lines_are_skipped():
    fig, ax = plt.subplots()
    x = np.linspace(0.0, 10.0, 50)
    ax.plot(x, x, label="keep")
    ax.plot(x, x + 1)
    ax.plot(x, np.full_like(x, np.nan), label="empty")
    vfs.range_frame(ax)
    texts = vfs.line_labels(ax)
    fig.canvas.draw()
    assert [t.get_text() for t in texts] == ["keep"]
    plt.close(fig)


def test_anchor_skips_trailing_nan():
    fig, ax = plt.subplots()
    x = np.linspace(0.0, 10.0, 50)
    y = x.copy()
    y[45:] = np.nan
    ax.plot(x, y, label="cut")
    vfs.range_frame(ax)
    (text,) = vfs.line_labels(ax)
    fig.canvas.draw()
    assert text.xy == (x[44], y[44])
    plt.close(fig)


def test_labels_stay_disjoint_after_resize(converging_ax):
    ax, texts = converging_ax
    ax.figure.set_size_inches(4, 3)
    ax.figure.canvas.draw()
    boxes = label_bboxes(ax, texts)
    assert all(not a.overlaps(b) for a, b in itertools.combinations(boxes, 2))


def test_labelcolor_single_and_list():
    fig, ax = plt.subplots()
    converging_lines(ax)
    vfs.range_frame(ax)
    texts = vfs.line_labels(ax, labelcolor="black")
    assert [t.get_color() for t in texts] == ["black"] * 3
    texts = vfs.line_labels(ax, labelcolor=["red", "green"])
    assert [t.get_color() for t in texts] == ["red", "green", "red"]
    plt.close(fig)


def test_recall_replaces_instead_of_stacking_duplicates():
    fig, ax = plt.subplots()
    converging_lines(ax)
    vfs.range_frame(ax)
    vfs.line_labels(ax)
    texts = vfs.line_labels(ax)
    fig.canvas.draw()
    assert len(ax.texts) == len(texts) == 3
    plt.close(fig)


def test_invalid_at_raises():
    fig, ax = plt.subplots()
    with pytest.raises(ValueError, match="start"):
        vfs.line_labels(ax, at="middle")
    plt.close(fig)


def test_start_labels_right_align_and_separate():
    fig, ax = plt.subplots()
    x = np.linspace(0.0, 10.0, 200)
    for slope, name in [(1.0, "alpha"), (1.01, "beta")]:
        ax.plot(x, slope * x, label=name)
    vfs.range_frame(ax, frame="loose")
    texts = vfs.line_labels(ax, at="start")
    fig.canvas.draw()
    renderer = fig.canvas.get_renderer()
    pad_px = 4.0 * fig.dpi / 72
    boxes = [t.get_window_extent(renderer) for t in texts]
    assert not boxes[0].overlaps(boxes[1])
    anchor_x = ax.transData.transform((0.0, 0.0))[0]
    for box in boxes:
        assert abs(box.x1 - (anchor_x - pad_px)) < 1
    plt.close(fig)


def test_both_sides_coexist(converging_ax):
    ax, end_texts = converging_ax
    start_texts = vfs.line_labels(ax, at="start")
    ax.figure.canvas.draw()
    assert len(start_texts) == 3
    assert set(end_texts) <= set(ax.texts)
    assert set(start_texts) <= set(ax.texts)


def test_labels_anchor_correctly_on_date_axes():
    fig, ax = plt.subplots()
    days = [datetime.date(2026, 1, d) for d in range(1, 31)]
    values = np.linspace(3.0, 7.0, 30)
    ax.plot(days, values, label="series")
    (text,) = vfs.line_labels(ax)
    fig.canvas.draw()
    renderer = fig.canvas.get_renderer()
    anchor_display = ax.transData.transform(
        (matplotlib.dates.date2num(days[-1]), values[-1])
    )
    box = text.get_window_extent(renderer)
    assert abs((box.y0 + box.y1) / 2 - anchor_display[1]) < 2
    assert abs(box.x0 - (anchor_display[0] + 4.0 * fig.dpi / 72)) < 1
    plt.close(fig)


def test_restore_removes_line_labels():
    fig, ax = plt.subplots()
    converging_lines(ax)
    vfs.apply(ax)
    vfs.line_labels(ax)
    vfs.line_labels(ax, at="start")
    fig.canvas.draw()
    vfs.restore(ax)
    assert not ax.texts
    plt.close(fig)
