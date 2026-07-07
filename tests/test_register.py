import matplotlib.pyplot as plt

import tufty


def test_register_adds_working_method_and_is_reentrant():
    tufty.register()
    tufty.register()
    fig, ax = plt.subplots()
    ax.plot([1, 2, 3], [3, 1, 2])
    result = ax.tuftify(frame="data")
    assert result is ax
    assert not ax.spines["top"].get_visible()
    fig.canvas.draw()
    assert ax.spines["bottom"].get_bounds() == tuple(ax.xaxis.get_data_interval())
    plt.close(fig)
