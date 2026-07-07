from matplotlib.ticker import Locator
import functools
import numpy as np

class TufteLocator(Locator):
    """
    Class for generating Tufte-style locators for matplotlib plots.

    Parameters
    ----------
    measures: list of callables, default=``[np.min, partial(np.quantile, q=0.25), np.median, partial(np.quantile, q=0.75), np.max]``
        A list of functions to be applied to the data on the specified axis.
        Ticks will only be displayed for these calculated values
    axis: str, default="x"
        The axis to use for the locator. Can be either ``x`` or ``y``.

    Methods
    -------
    tick_values(lines):
        Return the locations of the ticks for the desired ``measures``.
    __call__():
        Return the tick values for the current axis.
    """

    def __init__(
        self,
        measures=[
            np.min,
            functools.partial(np.quantile, q=0.25),
            np.median,
            functools.partial(np.quantile, q=0.75),
            np.max,
        ],
        axis="x",
    ):
        self.measures = measures
        self.tufte_axis = axis
        self.axis = axis

    def tick_values(self, lines):
        if self.tufte_axis == "x":
            data = lines[0].get_xdata()
        elif self.tufte_axis == "y":
            data = lines[0].get_ydata()
        else:
            raise NotImplementedError("Only supported option for axis are 'x' and 'y'.")

        return [measure(data) for measure in self.measures]

    def __call__(self):
        lines = self.axis.axes.get_lines()

        return self.tick_values(lines)
