"""The klaar composer and axes-method registration."""

from klaarte.frame import range_frame


def klaar(ax, frame="nice", n=5, offset=None, nice_numbers=None, weights=None):
    """Apply klaarte's default treatment to `ax`.

    The top-level entry point. Today it applies `range_frame` with good
    defaults; it is the seam where later styling and mark helpers will be
    bundled. Takes the same arguments as `range_frame`.

    Returns
    -------
    matplotlib.axes.Axes
        The same axes, for chaining.
    """
    return range_frame(
        ax, frame=frame, n=n, offset=offset, nice_numbers=nice_numbers, weights=weights
    )


def register():
    """Add a `klaar` method to `matplotlib.axes.Axes`.

    Opt-in monkeypatching: after calling this once, `ax.klaar(...)`
    delegates to `klaar(ax, ...)`. Calling it again is a no-op.
    """
    from matplotlib.axes import Axes

    if getattr(Axes, "klaar", None) is not None:
        return

    def _klaar_method(self, frame="nice", n=5, offset=None, nice_numbers=None, weights=None):
        return klaar(
            self, frame=frame, n=n, offset=offset, nice_numbers=nice_numbers, weights=weights
        )

    Axes.klaar = _klaar_method
