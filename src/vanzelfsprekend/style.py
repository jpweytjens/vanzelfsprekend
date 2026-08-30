"""vanzelfsprekend's opinionated drawing defaults, as a matplotlib style.

Registers the `vanzelfsprekend` style so `plt.style.use("vanzelfsprekend")`
and `plt.style.context("vanzelfsprekend")` reach it, the same import-time
registration as the `tol:` colour names. It is the geometry knob of the
provision lane: lighter lines and smaller marks, quieter titles. It stays
out of the other two lanes -- colour is `palettes.cycle`, the frame is
`distill` -- so it sets no colour cycle and no spine or grid property.
Draw, `distill` and save inside the context, since matplotlib reads these
params when it renders, not when you call `plot`.
"""

import matplotlib.style

_STYLE = {
    "lines.linewidth": 1.2,
    "lines.markersize": 4,
    "lines.solid_capstyle": "round",
    "axes.titlesize": 10,
}


def _register_style() -> None:
    """Add the `vanzelfsprekend` style to matplotlib's style library."""
    matplotlib.style.library["vanzelfsprekend"] = matplotlib.RcParams(_STYLE)
    matplotlib.style.available[:] = sorted(matplotlib.style.library.keys())


_register_style()
