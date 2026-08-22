"""End-of-spine axis labels for a range frame."""

from vanzelfsprekend.frame import _frame_span
from vanzelfsprekend.hook import add_applier, ensure_state, get_state, run_appliers


def xlabel(ax, text, labelpad=None):
    """Set an x-label that sits below the right end of the bottom spine.

    Call after `range_frame`.

    Parameters
    ----------
    ax : matplotlib.axes.Axes
        A range-framed axes.
    text : str
        The label text.
    labelpad : float, optional
        Gap in points between the label and the tick-label column, whose
        edge is set by the *widest* tick label (matplotlib's own per-draw
        computation). `None` keeps matplotlib's default (rcParam
        `axes.labelpad`, 4.0).

    Returns
    -------
    matplotlib.text.Text
        The label artist.
    """
    _labels_state(ax)
    ax.set_xlabel(text, labelpad=labelpad)
    ax.xaxis.label.set_horizontalalignment("right")
    add_applier(ax, "labels", _apply_labels)
    run_appliers(ax)
    return ax.xaxis.label


def ylabel(ax, text, flush=False, labelpad=None):
    """Set a horizontal y-label at the top of the left spine.

    Call after `range_frame`.

    Parameters
    ----------
    ax : matplotlib.axes.Axes
        A range-framed axes.
    text : str
        The label text.
    flush : bool
        If True, anchor the label at the topmost tick with
        `va='center_baseline'`, so it sits flush with the top tick label.
        If False, place it above the spine's top end.
    labelpad : float, optional
        Gap in points between the label and the tick-label column, whose
        edge is set by the *widest* tick label. `None` keeps matplotlib's
        default (rcParam `axes.labelpad`, 4.0).

    Returns
    -------
    matplotlib.text.Text
        The label artist.
    """
    _labels_state(ax)["ylabel_flush"] = flush
    ax.set_ylabel(text, rotation=0, labelpad=labelpad)
    ax.yaxis.label.set_verticalalignment("center_baseline" if flush else "bottom")
    ax.yaxis.label.set_horizontalalignment("right")
    add_applier(ax, "labels", _apply_labels)
    run_appliers(ax)
    return ax.yaxis.label


def _labels_state(ax):
    state = ensure_state(ax)
    ls = state.get("labels")
    if ls is None:
        ls = {
            "ylabel_flush": False,
            "snapshot": {
                "x": _label_props(ax.xaxis.label),
                "y": _label_props(ax.yaxis.label),
            },
        }
        state["labels"] = ls
    return ls


def _label_props(label):
    return {
        "ha": label.get_horizontalalignment(),
        "va": label.get_verticalalignment(),
        "rotation": label.get_rotation(),
        "position": label.get_position(),
    }


def _apply_labels(ax):
    state = get_state(ax)
    if state is None or "frame" not in state:
        return False
    frame_state = state["frame"]
    mode = frame_state["mode"]
    active = frame_state["active"]
    ls = state.get("labels", {})
    changed = False
    if "x" in active and ax.get_xlabel():
        span = _frame_span(ax.xaxis, mode)
        if span is not None:
            vmin, vmax = ax.get_xlim()
            frac = (span[1] - vmin) / (vmax - vmin)
            pos = ax.xaxis.label.get_position()
            if pos[0] != frac:
                ax.xaxis.label.set_position((frac, pos[1]))
                changed = True
    if "y" in active and ax.get_ylabel():
        span = _frame_span(ax.yaxis, mode)
        if span is not None:
            anchor = span[1]
            if ls.get("ylabel_flush"):
                locs = ax.yaxis.get_majorticklocs()
                if len(locs):
                    anchor = max(locs)
            vmin, vmax = ax.get_ylim()
            frac = (anchor - vmin) / (vmax - vmin)
            pos = ax.yaxis.label.get_position()
            if pos[1] != frac:
                ax.yaxis.label.set_position((pos[0], frac))
                changed = True
    return changed
