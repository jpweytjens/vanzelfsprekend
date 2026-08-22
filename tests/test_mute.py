import matplotlib.pyplot as plt
from matplotlib.colors import to_rgba

import vanzelfsprekend as vfs
from vanzelfsprekend import palettes


def test_mute_greys_axis_furniture():
    fig, ax = plt.subplots()
    ax.plot([0, 1], [0, 1])
    ax.set_xlabel("x")
    vfs.mute(ax)
    line_ink = to_rgba(palettes.LINE_INK)
    text_ink = to_rgba(palettes.TEXT_INK)
    assert ax.spines["left"].get_edgecolor() == line_ink
    assert ax.spines["left"].get_linewidth() == 0.7
    tick = ax.xaxis.get_major_ticks()[0]
    assert to_rgba(tick.tick1line.get_color()) == line_ink
    assert tick.tick1line.get_markeredgewidth() == 0.7
    assert to_rgba(tick.label1.get_color()) == text_ink
    assert to_rgba(ax.xaxis.label.get_color()) == text_ink
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
    before_width = ax.spines["left"].get_linewidth()
    before_label = to_rgba(ax.xaxis.label.get_color())
    before_tick = to_rgba(ax.xaxis.get_major_ticks()[0].tick1line.get_color())
    vfs.mute(ax)
    vfs.restore(ax)
    assert ax.spines["left"].get_edgecolor() == before_spine
    assert ax.spines["left"].get_linewidth() == before_width
    assert to_rgba(ax.xaxis.label.get_color()) == before_label
    after_tick = to_rgba(ax.xaxis.get_major_ticks()[0].tick1line.get_color())
    assert after_tick == before_tick
    plt.close(fig)


def test_restore_resets_tick_ink_on_tickless_axes():
    fig, ax = plt.subplots()
    ax.plot([0, 1], [0, 1])
    ax.set_xticks([])
    ax.set_yticks([])
    vfs.mute(ax)
    vfs.restore(ax)
    ax.set_xticks([0.5])
    tick = ax.xaxis.get_major_ticks()[0]
    assert to_rgba(tick.tick1line.get_color()) == to_rgba(plt.rcParams["xtick.color"])
    plt.close(fig)
