__all__ = ["heckbert_nicenum", "heckbert", "HeckbertLocator"]


from matplotlib.ticker import Locator
import numpy as np


def heckbert_nicenum(x, round):
    """
    Calculate a 'nice' number for graph labels that is close to x. Rounds the number if `round` is True.
    This function is part of Heckbert's algorithm as described in "Nice Numbers for Graph Labels," Graphics Gems I.

    Parameters
    ----------
    x : float
        The input number to be converted into a 'nice' number.
    round : bool
        A flag indicating whether the output should be rounded or not.

    Returns
    -------
    float
        A 'nice' number close to x. Rounded if `round` is True, otherwise not rounded.

    Examples
    --------
    >>> heckbert_nicenum(0.3, True)
    0.2
    """
    e = np.floor(np.log10(x))
    f = x / 10**e
    if round:
        if f < 1.5:
            nf = 1
        elif f < 3:
            nf = 2
        elif f < 7:
            nf = 5
        else:
            nf = 10
    else:
        if f <= 1:
            nf = 1
        elif f <= 2:
            nf = 2
        elif f <= 5:
            nf = 5
        else:
            nf = 10
    return nf * 10**e


def heckbert(d_min, d_max, n_tick_labels):
    """
    Generate a sequence of 'nice' numbers over the specified range using Heckbert's algorithm.
    The algorithm is designed to choose label locations for graph axes that are easy to read.
    It is described in "Nice Numbers for Graph Labels," Graphics Gems I.

    Parameters
    ----------
    d_min : float
        The minimum value of the data range for which 'nice' numbers are generated.
    d_max : float
        The maximum value of the data range for which 'nice' numbers are generated.
    n_tick_labels : int
        The target number of tick label locations. It is not the number of intervals.

    Returns
    -------
    numpy.ndarray
        An array of 'nice' numbers that span the range from dmin to dmax.
    """
    range_ = heckbert_nicenum(d_max - d_min, False)
    l_step = heckbert_nicenum(range_ / (n_tick_labels - 1), True)
    l_min = np.floor(d_min / l_step) * l_step
    l_max = np.ceil(d_max / l_step) * l_step

    return np.arange(l_min, l_max + l_step, l_step)


class HeckbertLocator(Locator):
    def __init__(self, n_tick_labels):
        self.n_tick_labels = n_tick_labels

    def __call__(self):
        d_min, d_max = self.axis.get_view_interval()
        if d_max < d_min:
            d_min, d_max = d_max, d_min

        return heckbert(d_min, d_max, self.n_tick_labels)
