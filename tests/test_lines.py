import numpy as np

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
