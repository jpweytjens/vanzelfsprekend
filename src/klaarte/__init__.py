"""Clear, minimal-ink axes for matplotlib."""

from klaarte.compose import klaar, ontklaar, register, unregister
from klaarte.frame import range_frame
from klaarte.labels import xlabel, ylabel
from klaarte.locator import TalbotLocator

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
