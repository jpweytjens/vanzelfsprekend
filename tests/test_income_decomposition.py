"""The labour-income example's decomposition contract.

The permanent component is recovered by penalized median segmentation, so
it must come back as a clean piecewise-constant step: one jump, at the
raise, of the raise's size -- and the recurrent June/December bumps, which
are larger than the raise, must not split it (that is what the *median*
cost buys over a least-squares one).
"""

import importlib.util
from pathlib import Path

import numpy as np

_PATH = Path(__file__).parents[1] / "examples" / "tutorial_income.py"
_spec = importlib.util.spec_from_file_location("tutorial_income", _PATH)
assert _spec is not None
assert _spec.loader is not None
income_example = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(income_example)


def test_permanent_component_is_a_single_clean_step():
    _, income = income_example.data()
    perm, _nu, _sigma, dperm = income_example.decompose(income)

    # Fully defined (no smoothing-window edge gaps) and exactly two levels.
    assert np.isfinite(perm).all()
    assert np.unique(perm).size == 2

    # Exactly one jump, at the raise, of the raise's size.
    change_idx = np.flatnonzero(np.abs(dperm) > income_example.EPS_PERM)
    assert change_idx.size == 1
    assert abs(int(change_idx[0]) - income_example.RAISE_AT) <= 1
    assert abs(dperm[change_idx[0]] - income_example.RAISE) < 0.05
