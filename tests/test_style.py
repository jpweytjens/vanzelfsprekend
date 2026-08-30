import matplotlib as mpl
import matplotlib.pyplot as plt

import vanzelfsprekend  # noqa: F401  (import registers the style)


def test_style_is_registered():
    assert "vanzelfsprekend" in plt.style.available


def test_style_lightens_the_marks_and_titles():
    with plt.style.context("vanzelfsprekend"):
        assert mpl.rcParams["lines.linewidth"] == 1.2
        assert mpl.rcParams["lines.markersize"] == 4
        assert mpl.rcParams["axes.titlesize"] == 10
        assert mpl.rcParams["lines.solid_capstyle"].value == "round"


def test_style_leaves_colour_and_frame_alone():
    """The geometry knob stays out of the colour and frame lanes."""
    with plt.style.context("vanzelfsprekend"):
        assert mpl.rcParams["axes.prop_cycle"] == mpl.rcParamsDefault["axes.prop_cycle"]
        assert mpl.rcParams["axes.spines.top"] == mpl.rcParamsDefault["axes.spines.top"]
        assert mpl.rcParams["axes.grid"] == mpl.rcParamsDefault["axes.grid"]


def test_style_restores_on_exit():
    before = mpl.rcParams["lines.linewidth"]
    with plt.style.context("vanzelfsprekend"):
        pass
    assert mpl.rcParams["lines.linewidth"] == before
