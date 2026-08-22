"""Clear, minimal-ink axes for matplotlib."""

from vanzelfsprekend import palettes
from vanzelfsprekend.compose import apply, register, restore, unregister
from vanzelfsprekend.frame import range_frame
from vanzelfsprekend.labels import xlabel, ylabel
from vanzelfsprekend.locator import TalbotLocator

__all__ = [
    "TalbotLocator",
    "apply",
    "palettes",
    "range_frame",
    "register",
    "restore",
    "unregister",
    "xlabel",
    "ylabel",
]
