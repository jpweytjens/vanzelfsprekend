"""Clear, minimal-ink axes for matplotlib."""

from vanzelfsprekend import palettes
from vanzelfsprekend.compose import apply, register, restore, unregister
from vanzelfsprekend.frame import range_frame
from vanzelfsprekend.labels import xlabel, ylabel
from vanzelfsprekend.locator import TalbotLocator
from vanzelfsprekend.mute import mute
from vanzelfsprekend.ticks import tick_direction

__all__ = [
    "TalbotLocator",
    "apply",
    "mute",
    "palettes",
    "range_frame",
    "register",
    "restore",
    "tick_direction",
    "unregister",
    "xlabel",
    "ylabel",
]
