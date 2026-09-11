"""What vanzelfsprekend does on exotic matplotlib figures.

The contract these pin is documented in docs/explanation/scope.md.
Polar and 3D graceful-decline are covered in tests/test_frame.py.
"""

import io

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pytest

import vanzelfsprekend as vzs
from vanzelfsprekend.hook import get_state


def _draw(fig):
    fig.savefig(io.BytesIO(), format="png")


def test_colorbar_axes_is_framed_without_crashing():
    # A colorbar's own axes is rectilinear, so vzs frames it. That is
    # user error, not vzs's to guess; the contract is only "no crash".
    fig, ax = plt.subplots()
    im = ax.imshow(np.random.default_rng(0).random((10, 10)))
    cbar = fig.colorbar(im)
    vzs.range_frame(cbar.ax)
    _draw(fig)
    plt.close(fig)


def test_secondary_xaxis_warns_via_the_function_scale_skip():
    fig, ax = plt.subplots()
    ax.plot([0, 1, 2], [0, 10, 20])
    sec = ax.secondary_xaxis("top", functions=(lambda x: x * 2, lambda x: x / 2))
    with pytest.warns(UserWarning, match="scale 'function'"):
        vzs.range_frame(sec)
    _draw(fig)
    plt.close(fig)


def test_inset_axes_is_framed_like_any_rectilinear_axes():
    fig, ax = plt.subplots()
    ax.plot([0, 1, 2], [0, 1, 4])
    ins = ax.inset_axes([0.6, 0.1, 0.35, 0.35])
    ins.plot([0, 1, 2], [2, 1, 0])
    vzs.range_frame(ins)
    assert get_state(ins) is not None  # it got a frame
    _draw(fig)
    plt.close(fig)


def test_animation_style_redraw_loop_does_not_crash():
    fig, ax = plt.subplots()
    (line,) = ax.plot([0, 1, 2], [0, 1, 4])
    vzs.range_frame(ax)
    for k in range(3):
        line.set_ydata([0, 1 + k, 4 + k])
        ax.relim()
        ax.autoscale_view()
        _draw(fig)  # hook re-trims each frame
    plt.close(fig)
