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
    assert palettes.AXIS_INK == palettes.DARK["dark_grey"] == "#555555"
    assert palettes.CYCLE[0] == palettes.DATA_INK
    assert palettes.CYCLE[1:] == tuple(palettes.VIBRANT.values())
