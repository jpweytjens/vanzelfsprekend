import matplotlib as mpl
import matplotlib.colors as mcolors
import matplotlib.pyplot as plt
import pytest

from vanzelfsprekend import palettes


def test_scheme_shapes_pin_the_technote():
    assert len(palettes.BRIGHT) == 7
    assert len(palettes.HIGH_CONTRAST) == 3
    assert len(palettes.VIBRANT) == 7
    assert len(palettes.MUTED) == 10
    assert len(palettes.MEDIUM_CONTRAST) == 6
    assert len(palettes.PALE) == 6
    assert len(palettes.DARK) == 6
    assert len(palettes.LIGHT) == 9
    assert next(iter(palettes.BRIGHT.values())) == "#4477AA"
    assert next(iter(palettes.VIBRANT.values())) == "#EE7733"
    assert next(iter(palettes.MUTED.values())) == "#CC6677"
    assert palettes.SCHEMES["vibrant"] is palettes.VIBRANT


def test_inks():
    assert palettes.DATA_INK == "#333333"
    assert palettes.TEXT_INK == palettes.DARK["grey"] == "#555555"
    assert palettes.LINE_INK == "#999999"


def test_cycle_defaults_to_ink():
    cycle = palettes.cycle()
    assert [entry["color"] for entry in cycle] == [palettes.DATA_INK]
    assert palettes.cycle("ink") == cycle


def test_cycle_of_scheme_drops_the_bad_data_grey():
    cycle = palettes.cycle("muted")
    colours = [entry["color"] for entry in cycle]
    assert colours == [
        hex_colour for name, hex_colour in palettes.MUTED.items() if name != "pale_grey"
    ]
    assert palettes.MUTED["pale_grey"] not in colours


def test_cycle_of_unknown_scheme_raises():
    with pytest.raises(ValueError, match="mauve"):
        palettes.cycle("mauve")


def test_bare_tol_names_resolve_to_vibrant():
    assert mcolors.to_hex("tol:orange").upper() == "#EE7733"
    assert mcolors.to_hex("tol:grey").upper() == "#BBBBBB"


def test_qualified_names_resolve_for_every_scheme():
    for scheme_name, scheme in palettes.SCHEMES.items():
        for name, hex_colour in scheme.items():
            resolved = mcolors.to_hex(f"tol:{scheme_name}.{name}")
            assert resolved.upper() == hex_colour


def test_unregistered_tol_name_still_raises():
    with pytest.raises(ValueError, match="tol:mauve"):
        mcolors.to_rgba("tol:mauve")


def test_axes_cycle_reads_the_cycle_on_this_matplotlib():
    # Pins the private attribute the reader relies on: a matplotlib
    # release that moves it fails here, not silently in distill.
    fig, ax = plt.subplots()
    assert palettes.axes_cycle(ax) == list(mpl.rcParams["axes.prop_cycle"])
    ax.plot([0, 1], [0, 1])  # a consumed entry does not change the cycle
    assert palettes.axes_cycle(ax) == list(mpl.rcParams["axes.prop_cycle"])
    ax.set_prop_cycle(color=["#4477AA", "#EE6677"])
    assert palettes.axes_cycle(ax) == [{"color": "#4477AA"}, {"color": "#EE6677"}]
    plt.close(fig)
