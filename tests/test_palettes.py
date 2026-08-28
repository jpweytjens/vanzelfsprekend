import matplotlib.colors as mcolors
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


def test_inks_and_cycle():
    assert palettes.DATA_INK == "#333333"
    assert palettes.TEXT_INK == palettes.DARK["grey"] == "#555555"
    assert palettes.LINE_INK == "#999999"
    assert palettes.CYCLE[0] == palettes.DATA_INK
    assert palettes.CYCLE[1:] == tuple(palettes.VIBRANT.values())


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
