import matplotlib.pyplot as plt
import numpy as np

import klaarte


def test_register_adds_working_method_and_is_reentrant():
    klaarte.register()
    klaarte.register()
    fig, ax = plt.subplots()
    ax.plot([1, 2, 3], [3, 1, 2])
    nice = [1, 2.5, 5]
    result = ax.klaar(frame="data", offset=5, nice_numbers=nice)
    assert result is ax
    assert not ax.spines["top"].get_visible()
    assert ax.spines["bottom"].get_position() == ("outward", 5)
    fig.canvas.draw()
    assert ax.spines["bottom"].get_bounds() == tuple(ax.xaxis.get_data_interval())
    expected = klaarte.TalbotLocator(nice_numbers=nice).tick_values(
        *ax.xaxis.get_data_interval()
    )
    np.testing.assert_allclose(ax.xaxis.get_majorticklocs(), expected)
    plt.close(fig)


def test_klaar_matches_range_frame_bounds():
    fig, ax = plt.subplots()
    rng = np.random.default_rng(0)
    x, y = rng.uniform(0.3, 9.7, 50), rng.uniform(-3.2, 4.1, 50)
    ax.scatter(x, y)
    klaarte.klaar(ax)
    fig.canvas.draw()
    bottom = ax.spines["bottom"].get_bounds()

    fig2, ax2 = plt.subplots()
    ax2.scatter(x, y)
    klaarte.range_frame(ax2)
    fig2.canvas.draw()
    assert bottom == ax2.spines["bottom"].get_bounds()
    plt.close(fig)
    plt.close(fig2)
