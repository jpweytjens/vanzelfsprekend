import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pytest

import vanzelfsprekend as vzs
from vanzelfsprekend.hook import add_applier, get_state


def _boom(ax):
    raise RuntimeError("boom")


def test_draw_time_failure_warns_once_and_does_not_propagate():
    fig, ax = plt.subplots()
    ax.plot([0, 1, 2], [0, 1, 4])
    vzs.range_frame(ax)
    add_applier(ax, "boom", _boom)  # a concern whose applier fails on draw

    with pytest.warns(UserWarning, match="draw-time") as record:  # noqa: PT031
        fig.canvas.draw()  # first draw: warns, does not raise
        fig.canvas.draw()  # second draw: silent

    assert len(record) == 1
    assert get_state(ax)["draw_warned"] is True
    plt.close(fig)
