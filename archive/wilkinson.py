from matplotlib.ticker import Locator
import numpy as np


def wilkinson(
    d_min,
    d_max,
    n_tick_labels,
    Q=[1, 5, 2, 2.5, 3, 4, 1.5, 7, 6, 8, 9],
    min_coverage=0.8,
    m_range=None,
):
    """
    Find a 'nice' scale for graph axis labels using Wilkinson's algorithm.

    Parameters
    ----------
    d_min : float
        The minimum data value.
    d_max : float
        The maximum data value.
    n_tick_labels : float
        The target number of ticks.
    Q : list, optional
        A list of acceptable increments.
    min_coverage : float, optional
        The minimum coverage of the data range by the axis range.
    m_range : range, optional
        The range of multiples of `m` to consider for the number of intervals.

    Returns
    -------
    sequence : ndarray
        An array from best 'l_min' to 'l_max' with a step of 'l_step'.

    Notes
    -----
    This function is adapted from Wilkinson's original Java implementation with
    some modifications. The `m_range` has been adjusted to provide more flexibility
    with the number of ticks, and the algorithm has been adapted to handle negative
    scores, potentially leading to better labelings.

    If no solution is found, an empty list is returned, suggesting that the search
    range may need to be increased.
    """

    if not m_range:
        m_range = range(
            max(int(np.floor(n_tick_labels / 2)), 2),
            int(np.ceil(6 * n_tick_labels)) + 1,
        )

    best = None
    best_score = -np.inf

    for k in m_range:
        result = _wilkinson_nice_scale(d_min, d_max, k, Q, min_coverage, n_tick_labels)
        if result:
            _, _, _, score = result
            if score > best_score:
                best = result
                best_score = score

    if best:
        l_min, l_max, l_step, _ = best
        return np.arange(l_min, l_max + l_step, l_step)
    else:
        # Return an empty list if no solution is found
        return []


def _wilkinson_nice_scale(d_min, d_max, k, Q, min_coverage, n_tick_labels):
    """
    Helper function for wilkinson to compute the best 'nice' scale for an axis.

    Parameters
    ----------
    min : float
        The minimum axis value.
    max : float
        The maximum axis value.
    k : int
        The number of intervals.
    Q : list
        A list of acceptable increments.
    min_coverage : float
        The minimum coverage of the data range by the axis range.
    n_tick_labels : float
        The target number of ticks.

    Returns
    -------
    best : dict or None
        A dictionary with keys 'l_min', 'l_max', 'l_step', and 'score' if a suitable
        scale is found; otherwise, `None`.

    Notes
    -----
    This function performs the core computation of Wilkinson's algorithm, taking
    into account the desired granularity and coverage of the axis ticks.
    """

    Q = [10] + Q
    range_ = d_max - d_min
    intervals = k - 1
    granularity = 1 - np.abs(k - n_tick_labels) / n_tick_labels

    delta = range_ / intervals
    base = np.floor(np.log10(delta))
    d_base = 10**base

    best = None
    best_score = -np.inf  # Start with negative infinity

    for i, q in enumerate(Q):
        t_delta = q * d_base
        t_min = np.floor(d_min / t_delta) * t_delta
        t_max = t_min + intervals * t_delta

        if t_min <= d_min and t_max >= d_max:
            roundness = 1 - (i - (1 if t_min <= 0 and t_max >= 0 else 0)) / len(Q)
            coverage = (d_max - d_min) / (t_max - t_min)
            if coverage >= min_coverage:
                t_nice = granularity + roundness + coverage

                if t_nice > best_score:
                    best = (t_min, t_max, t_delta, t_nice)
                    best_score = t_nice

    return best


class WilkinsonLocator(Locator):
    def __init__(self, n_tick_labels, min_coverage):
        self.n_tick_labels = n_tick_labels
        self.min_coverage = min_coverage

    def __call__(self):
        d_min, d_max = self.axis.get_view_interval()
        if d_max < d_min:
            d_min, d_max = d_max, d_min

        return wilkinson(
            d_min, d_max, self.n_tick_labels, min_coverage=self.min_coverage
        )
