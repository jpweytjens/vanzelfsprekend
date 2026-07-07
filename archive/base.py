from matplotlib.ticker import Locator
import numpy as np


class FixedLocator(Locator):

    def __init__(self, locations):
        self.locations = np.asarray(locations)

    def __call__(self):
        return self.tick_values(None, None)

    def tick_values(self, vmin, vmax):
        """
        Return the locations of the ticks.

        .. note::

            Because the values are fixed, vmin and vmax are not used in this
            method.

        """
        
        return self.locations
            
        

class IndexLocator(Locator):
    """
    Place a tick on every multiple of some base number of points
    plotted, e.g., on every 5th point.  It is assumed that you are doing
    index plotting; i.e., the axis is 0, len(data).  This is mainly
    useful for x ticks.
    """
    def __init__(self, base, offset):
        """Place ticks every *base* data point, starting at *offset*."""
        self._base = base
        self.offset = offset

    def set_params(self, base=None, offset=None):
        """Set parameters within this locator"""
        if base is not None:
            self._base = base
        if offset is not None:
            self.offset = offset

    def __call__(self):
        """Return the locations of the ticks"""
        dmin, dmax = self.axis.get_data_interval()
        return self.tick_values(dmin, dmax)

    def tick_values(self, vmin, vmax):
        return self.raise_if_exceeds(
            np.arange(vmin + self.offset, vmax + 1, self._base))
