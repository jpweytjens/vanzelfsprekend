"""Paul Tol's qualitative colour schemes, and vanzelfsprekend's inks.

Transcribed from Paul Tol, "Colour Schemes", SRON/EPS/TN/09-002,
issue 3.2, 18 August 2021 (https://sronpersonalpages.nl/~pault/).
Each scheme is ordered by the technote's recommended fixed picking
sequence; `list(SCHEME.values())` is the colour-cycle form. `PALE` and
`DARK` are meant for text backgrounds and text, not for lines or maps.
"""

from matplotlib.colors import get_named_colors_mapping

BRIGHT = {
    "blue": "#4477AA",
    "red": "#EE6677",
    "green": "#228833",
    "yellow": "#CCBB44",
    "cyan": "#66CCEE",
    "purple": "#AA3377",
    "grey": "#BBBBBB",
}
HIGH_CONTRAST = {
    "blue": "#004488",
    "yellow": "#DDAA33",
    "red": "#BB5566",
}
VIBRANT = {
    "orange": "#EE7733",
    "blue": "#0077BB",
    "cyan": "#33BBEE",
    "magenta": "#EE3377",
    "red": "#CC3311",
    "teal": "#009988",
    "grey": "#BBBBBB",
}
MUTED = {
    "rose": "#CC6677",
    "indigo": "#332288",
    "sand": "#DDCC77",
    "green": "#117733",
    "cyan": "#88CCEE",
    "wine": "#882255",
    "teal": "#44AA99",
    "olive": "#999933",
    "purple": "#AA4499",
    "pale_grey": "#DDDDDD",
}
MEDIUM_CONTRAST = {
    "light_blue": "#6699CC",
    "dark_blue": "#004488",
    "light_yellow": "#EECC66",
    "dark_red": "#994455",
    "dark_yellow": "#997700",
    "light_red": "#EE99AA",
}
PALE = {
    "pale_blue": "#BBCCEE",
    "pale_cyan": "#CCEEFF",
    "pale_green": "#CCDDAA",
    "pale_yellow": "#EEEEBB",
    "pale_red": "#FFCCCC",
    "pale_grey": "#DDDDDD",
}
DARK = {
    "dark_blue": "#222255",
    "dark_cyan": "#225555",
    "dark_green": "#225522",
    "dark_yellow": "#666633",
    "dark_red": "#663333",
    "dark_grey": "#555555",
}
LIGHT = {
    "light_blue": "#77AADD",
    "orange": "#EE8866",
    "light_yellow": "#EEDD88",
    "pink": "#FFAABB",
    "light_cyan": "#99DDFF",
    "mint": "#44BB99",
    "pear": "#BBCC33",
    "olive": "#AAAA00",
    "pale_grey": "#DDDDDD",
}

SCHEMES = {
    "bright": BRIGHT,
    "high_contrast": HIGH_CONTRAST,
    "vibrant": VIBRANT,
    "muted": MUTED,
    "medium_contrast": MEDIUM_CONTRAST,
    "pale": PALE,
    "dark": DARK,
    "light": LIGHT,
}

DATA_INK = "#333333"
AXIS_INK = DARK["dark_grey"]
CYCLE = (DATA_INK, *VIBRANT.values())


def _register_named_colors() -> None:
    """Add `tol:` names to matplotlib's named-colour registry.

    Bare names (`tol:orange`) resolve to the vibrant scheme; qualified
    names (`tol:muted.rose`) reach every scheme. Same mechanism as
    matplotlib's own `tab:` and `xkcd:` namespaces.
    """
    mapping = get_named_colors_mapping()
    for scheme_name, scheme in SCHEMES.items():
        for name, hex_colour in scheme.items():
            mapping[f"tol:{scheme_name}.{name}"] = hex_colour
    for name, hex_colour in VIBRANT.items():
        mapping[f"tol:{name}"] = hex_colour


_register_named_colors()
