"""Per-axes state and the shared draw-hook backbone.

One draw hook per Axes dispatches to a registry of appliers, each a
callable ``applier(ax) -> bool`` returning whether it changed anything
this call. Concerns (the range frame, the labels, later marks) register
their applier by name; the hook ORs the results and requests a single
redraw when anything changed. This module knows nothing about frames or
labels.
"""

_STATE_ATTR = "_klaarte_state"


def get_state(ax):
    """Return the klaarte state dict for `ax`, or `None`."""
    return getattr(ax, _STATE_ATTR, None)


def ensure_state(ax):
    """Return `ax`'s klaarte state, creating it and the draw hook once."""
    state = getattr(ax, _STATE_ATTR, None)
    if state is None:
        cid = ax.figure.canvas.mpl_connect("draw_event", _make_on_draw(ax))
        state = {"cid": cid, "appliers": {}}
        setattr(ax, _STATE_ATTR, state)
    return state


def add_applier(ax, name, fn):
    """Register (or replace) the applier stored under `name`."""
    ensure_state(ax)["appliers"][name] = fn


def run_appliers(ax):
    """Run every registered applier once now.

    Returns whether any applier reported a change. Does not swallow
    exceptions: errors surface on the enabling call so bugs are visible.
    """
    state = get_state(ax)
    if state is None:
        return False
    changed = False
    for fn in list(state["appliers"].values()):
        changed = fn(ax) or changed
    return changed


def _make_on_draw(ax):
    def _on_draw(event):
        try:
            changed = run_appliers(ax)
        except Exception:
            return
        if changed:
            event.canvas.draw_idle()

    return _on_draw


def disconnect(ax):
    """Disconnect `ax`'s draw hook."""
    state = get_state(ax)
    if state is not None:
        ax.figure.canvas.mpl_disconnect(state["cid"])


def clear_state(ax):
    """Delete `ax`'s klaarte state attribute if present."""
    if hasattr(ax, _STATE_ATTR):
        delattr(ax, _STATE_ATTR)
