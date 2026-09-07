import numpy as np

from vanzelfsprekend import placement


def test_weighted_pava_equals_unweighted_with_unit_weights():
    y = np.array([3.0, 1.0, 2.0, 5.0, 4.0])
    np.testing.assert_allclose(placement.pava(y, np.ones(5)), placement.pava(y))


def test_weighted_pava_pools_by_weighted_mean():
    # 3 and 1 violate; pooled weighted mean is (3*1 + 1*3) / 4 = 1.5
    np.testing.assert_allclose(
        placement.pava(np.array([3.0, 1.0]), np.array([1.0, 3.0])), [1.5, 1.5]
    )
    # 3 and 2 violate; pooled (3*1 + 2*2) / 3 = 7/3, still above 1
    np.testing.assert_allclose(
        placement.pava(np.array([1.0, 3.0, 2.0]), np.array([1.0, 1.0, 2.0])),
        [1.0, 7 / 3, 7 / 3],
    )


def test_heavy_element_barely_moves():
    placed = placement.pava(np.array([10.0, 0.0]), np.array([1.0, 1e9]))
    assert abs(placed[1]) < 1e-6
    assert abs(placed[0]) < 1e-6  # pooled onto the heavy one


def test_stack_pin_holds_and_label_clears_it():
    # A label (size 10) whose desired position sits on a pin (size 4) at 50,
    # ordered above it by the key: it lands at 50 + (4 + 10) / 2 + gap 2 = 59.
    desired = np.array([50.0, 50.0])
    sizes = np.array([10.0, 4.0])
    weights = np.array([1.0, placement.PIN_WEIGHT])
    key = np.array([50.0 + 1e-9, 50.0])
    placed = placement.stack(desired, sizes, 2.0, weights=weights, key=key)
    assert abs(placed[1] - 50.0) < placement.PIN_TOLERANCE
    np.testing.assert_allclose(placed[0], 59.0, atol=1e-6)


def test_stack_over_capacity_moves_pins_apart():
    # Two pins (size 2) at 40 and 60, two labels (size 10) wanting 50: the
    # labels need 8 + 12 + 8 = 28 between pin centres, only 20 exist, so the
    # pins are forced apart by 4 each and the tolerance detects it.
    desired = np.array([50.0, 50.0, 40.0, 60.0])
    sizes = np.array([10.0, 10.0, 2.0, 2.0])
    weights = np.array([1.0, 1.0, placement.PIN_WEIGHT, placement.PIN_WEIGHT])
    placed = placement.stack(desired, sizes, 2.0, weights=weights)
    pin_move = np.abs(placed[2:] - desired[2:]).max()
    assert pin_move > placement.PIN_TOLERANCE
    np.testing.assert_allclose(pin_move, 4.0, atol=1e-6)


def test_stack_key_overrides_desired_order():
    # Same desired positions, key puts the second element first.
    desired = np.array([50.0, 50.0])
    sizes = np.array([10.0, 10.0])
    default = placement.stack(desired, sizes, 2.0)
    swapped = placement.stack(desired, sizes, 2.0, key=np.array([1.0, 0.0]))
    np.testing.assert_allclose(default, [44.0, 56.0])
    np.testing.assert_allclose(swapped, [56.0, 44.0])
