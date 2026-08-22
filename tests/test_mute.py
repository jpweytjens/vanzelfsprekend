import matplotlib.pyplot as plt
from matplotlib.colors import to_rgba

import vanzelfsprekend as vfs
from vanzelfsprekend import palettes


def test_mute_greys_axis_furniture():
    fig, ax = plt.subplots()
    ax.plot([0, 1], [0, 1])
    ax.set_xlabel("x")
    vfs.mute(ax)
    ink = to_rgba(palettes.AXIS_INK)
    assert ax.spines["left"].get_edgecolor() == ink
    tick = ax.xaxis.get_major_ticks()[0]
    assert to_rgba(tick.tick1line.get_color()) == ink
    assert to_rgba(tick.label1.get_color()) == ink
    assert to_rgba(ax.xaxis.label.get_color()) == ink
    plt.close(fig)


def test_mute_leaves_data_artists_alone():
    fig, ax = plt.subplots()
    (line,) = ax.plot([0, 1], [0, 1], color="#0077BB")
    vfs.mute(ax)
    assert line.get_color() == "#0077BB"
    plt.close(fig)


def test_restore_reverts_mute():
    fig, ax = plt.subplots()
    ax.plot([0, 1], [0, 1])
    ax.set_xlabel("x")
    before_spine = ax.spines["left"].get_edgecolor()
    before_label = to_rgba(ax.xaxis.label.get_color())
    before_tick = to_rgba(ax.xaxis.get_major_ticks()[0].tick1line.get_color())
    vfs.mute(ax)
    vfs.restore(ax)
    assert ax.spines["left"].get_edgecolor() == before_spine
    assert to_rgba(ax.xaxis.label.get_color()) == before_label
    after_tick = to_rgba(ax.xaxis.get_major_ticks()[0].tick1line.get_color())
    assert after_tick == before_tick
    plt.close(fig)
