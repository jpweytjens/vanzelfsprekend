import matplotlib as mpl
import inspect
import functools

__all__ = ["tuftify"]


def get_ax(function, *args, **kwargs):
    """
    Get the Matplotlib.axes.Axes object from a function call.

    Usefull when trying to use the Axes in a decorated function.

    Parameters
    ----------
    function : callable
        The function to extract the axis from.
    *args : tuple
        Positional arguments passed to the function.
    **kwargs : dict
        Keyword arguments passed to the function.

    Returns
    -------
    ax : matplotlib.axes.Axes
    """

    try:
        argument_index = inspect.getfullargspec(function).args.index("ax")
        ax = args[argument_index]

    except IndexError:
        ax = kwargs["ax"]

    return ax


def visible(function):
    """
    Returns a decorator that sets the margin of the given function's axis to 0 before
    executing the function to limit the ticks to the visible ones.

    Parameters
    ----------
    function : callable
        The function to be decorated.

    Returns
    -------
    wrapper : callable
        A new function that wraps the original function and sets its margins to 0 before calling it.
    """

    @functools.wraps(function)
    def wrapper(*args, **kwargs):
        ax = get_ax(function, *args, **kwargs)

        # store original margins
        original_margins = ax.margins()
        ax.margins(0)

        # manipulate axis with 0 margins
        result = function(*args, **kwargs)

        # reset margins to original margins
        ax.margins(x=original_margins[0], y=original_margins[1])

        return result

    # ensure the wrapped function still has the signature of the original function
    # such that inspect.getfullargspec still works
    wrapper.__signature__ = inspect.signature(function)

    return wrapper


def draw_figure(function):
    """
    Draw the figure associated with a given matplotlib.Axes in memory.
    This ensures e.g. that all the ticks are set.

    Parameters
    ----------
    function : callable
        The function to wrap and draw.

    Returns
    -------
    wrapper : callable
        A wrapped version of the function that draws the figure.
    """

    @functools.wraps(function)
    def wrapper(*args, **kwargs):
        ax = get_ax(function, *args, **kwargs)
        fig = ax.get_figure()

        # ensure all ticks are set
        fig.canvas.draw()

        result = function(*args, **kwargs)
        return result

    # ensure the wrapped function still has the signature of the original function
    # such that inspect.getfullargspec still works
    wrapper.__signature__ = inspect.signature(function)

    return wrapper


@visible
@draw_figure
def get_visible_ticks(ax):
    """
    Returns the major tick of the x and y axes that are currently visible in the axes, i.e. regardless of the margins of the axes.

    Parameters
    ----------
    ax: matplotlib.axes.Axes
        Matplotlib axes

    Returns
    -------
    Tuple of two lists with the major ticks labels of the x and y axes respectively.

    Notes
    -----
    This function only returns ticks that are currently visible within the plot window.
    If you need to retrieve all ticks regardless of visibility,
    use ``ax.xaxis.get_majorticklabels()`` and ``ax.yaxis.get_majorticklabels()``.
    """
    visible_xticks = ax.xaxis.get_major_ticks()
    visible_yticks = ax.yaxis.get_major_ticks()

    return visible_xticks, visible_yticks


def tuftify(ax, locator, axis=None, set_lim=False):

    if not axis:
        axis = locator.axis

    if axis == "x":
        ax.xaxis.set_major_locator(locator)
        spines = ["top", "bottom"]
        set_axis_lim = ax.set_xlim

    elif axis == "y":
        ax.yaxis.set_major_locator(locator)
        spines = ["left", "right"]
        set_axis_lim = ax.set_ylim

    xticks, yticks = get_visible_ticks(ax)

    if axis == "x":
        ticks = xticks
    elif axis == "y":
        ticks = yticks

    ticks = [tick._loc for tick in ticks]
    lower, upper = ticks[0], ticks[-1]

    if len(ticks) > 0:
        for spine in spines:
            ax.spines[spine].set_bounds(lower, upper)

        if set_lim:
            set_axis_lim(lower, upper)

mpl.axes.Axes.tuftify = tuftify
