"""Clear, minimal-ink axes for matplotlib."""

from vanzelfsprekend.compose import klaar, ontklaar, register, unregister
from vanzelfsprekend.frame import range_frame
from vanzelfsprekend.labels import xlabel, ylabel
from vanzelfsprekend.locator import TalbotLocator

__all__ = [
    "TalbotLocator",
    "klaar",
    "ontklaar",
    "range_frame",
    "register",
    "unregister",
    "xlabel",
    "ylabel",
]
