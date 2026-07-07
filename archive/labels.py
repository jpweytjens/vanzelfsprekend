import matplotlib as mpl
import matplotlib.pyplot as plt

__all__ = ["hor_ylabel", "hor_xlabel", "get_visible_ticks"]

def remove_hor_xlabel(ax):

    for child in ax.get_children():
        if isinstance(child, mpl.text.Annotation) and child.xy[0] == 1:
            child.remove()


def remove_hor_ylabel(ax):

    for child in ax.get_children():
        if isinstance(child, mpl.text.Annotation) and child.xy[1] == 1:
            child.remove()


def hor_ylabel(ax, label, offset=1.5, fontsize=8):
    ax.set_ylabel("")
    remove_hor_ylabel(ax)
    data_to_axis = ax.transAxes.inverted()

    top_spine = ax.spines["top"].get_window_extent()
    bottom_spine = ax.spines["bottom"].get_window_extent()
    xticklabel = ax.get_xticklabels()[0].get_window_extent()
    ticklabel_separation = (
        bottom_spine.transformed(data_to_axis).y0
        - xticklabel.transformed(data_to_axis).y0
    )
    ticklabel_separation

    pos_x = 0
    pos_y = top_spine.transformed(data_to_axis).y0 + offset * ticklabel_separation

    ax.annotate(
        label,
        (pos_x, pos_y),
        xycoords="axes fraction",
        horizontalalignment="center",
        multialignment="left",
        rotation=0,
        verticalalignment="top",
        fontsize=fontsize,
        color="#4B4B4B",
    )


def hor_xlabel(ax, label, offset=1.5, fontsize=8, xtick_index=-1):
    ax.set_xlabel("")
    remove_hor_xlabel(ax)
    data_to_axis = ax.transAxes.inverted()

    bottom_spine = ax.spines["bottom"].get_window_extent()
    xticklabel = ax.get_xticklabels()[0].get_window_extent()
    ticklabel_separation = (
        bottom_spine.transformed(data_to_axis).y0
        - xticklabel.transformed(data_to_axis).y0
    )

    # last_xtick = ax.xaxis.get_major_ticks()[-1].get_window_extent()
    last_xtick = ax.get_xticklabels()[xtick_index].get_window_extent()

    pos_x = last_xtick.transformed(data_to_axis).x1
    pos_y = bottom_spine.transformed(data_to_axis).y0 - offset * ticklabel_separation

    ax.annotate(
        label,
        (pos_x, pos_y),
        xycoords="axes fraction",
        horizontalalignment="center",
        multialignment="center",
        rotation=0,
        verticalalignment="top",
        fontsize=fontsize,
        color="#4B4B4B",
    )

mpl.axes.Axes.hor_xlabel = hor_xlabel
mpl.axes.Axes.hor_ylabel = hor_ylabel
