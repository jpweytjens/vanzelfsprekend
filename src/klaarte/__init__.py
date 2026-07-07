"""Clear, minimal-ink axes for matplotlib."""

from klaarte.compose import klaar, register
from klaarte.frame import range_frame
from klaarte.labels import xlabel, ylabel
from klaarte.locator import TalbotLocator

__all__ = ["TalbotLocator", "klaar", "range_frame", "register", "xlabel", "ylabel"]
