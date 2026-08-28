"""Clear, minimal-ink axes for matplotlib."""

from importlib.metadata import version

from vanzelfsprekend import palettes
from vanzelfsprekend.compose import apply, register, restore, unregister
from vanzelfsprekend.frame import range_frame
from vanzelfsprekend.labels import xlabel, ylabel
from vanzelfsprekend.lines import line_labels
from vanzelfsprekend.locator import (
    DateBreaksLocator,
    FeatureLocator,
    LogBreaksLocator,
    QuartileLocator,
    SummaryLocator,
    TalbotLocator,
)
from vanzelfsprekend.multiples import small_multiples
from vanzelfsprekend.mute import mute
from vanzelfsprekend.ticks import tick_direction

__version__ = version("vanzelfsprekend")

# Install the `ax.vzs` accessor on import, like pandas and xarray accessors.
# `unregister()` removes it; `register()` puts it back.
register()

__all__ = [
    "DateBreaksLocator",
    "FeatureLocator",
    "LogBreaksLocator",
    "QuartileLocator",
    "SummaryLocator",
    "TalbotLocator",
    "apply",
    "line_labels",
    "mute",
    "palettes",
    "range_frame",
    "register",
    "restore",
    "small_multiples",
    "tick_direction",
    "unregister",
    "xlabel",
    "ylabel",
]
