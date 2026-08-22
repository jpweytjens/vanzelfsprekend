import matplotlib.pyplot as plt
import pytest

import vanzelfsprekend as vfs


def test_direction_in_points_ticks_inward():
    fig, ax = plt.subplots()
    ax.plot([0, 1], [0, 1])
    vfs.tick_direction(ax, "in")
    assert ax.xaxis.get_tick_params()["direction"] == "in"
    assert ax.yaxis.get_tick_params()["direction"] == "in"
    plt.close(fig)


def test_none_removes_marks_keeps_labels():
    fig, ax = plt.subplots()
    ax.plot([0, 1], [0, 1])
    vfs.tick_direction(ax, "none")
    tick = ax.xaxis.get_major_ticks()[0]
    assert tick.tick1line.get_markersize() == 0
    assert tick.label1.get_visible()
    plt.close(fig)


def test_none_then_out_restores_length():
    fig, ax = plt.subplots()
    ax.plot([0, 1], [0, 1])
    vfs.tick_direction(ax, "none")
    vfs.tick_direction(ax, "out")
    tick = ax.xaxis.get_major_ticks()[0]
    assert tick.tick1line.get_markersize() == plt.rcParams["xtick.major.size"]
    plt.close(fig)


def test_restore_reverts_direction():
    fig, ax = plt.subplots()
    ax.plot([0, 1], [0, 1])
    vfs.tick_direction(ax, "in")
    vfs.restore(ax)
    params = ax.xaxis.get_tick_params()
    direction = params.get("direction", plt.rcParams["xtick.direction"])
    assert direction == "out"
    plt.close(fig)


def test_invalid_direction_raises():
    fig, ax = plt.subplots()
    with pytest.raises(ValueError, match="direction"):
        vfs.tick_direction(ax, "sideways")
    plt.close(fig)
