"""DeckSnag - Capture presentations and convert to slides automatically."""

__version__ = "2.0.0"
__author__ = "Derek Plemons"
__email__ = "plemons.derek@gmail.com"

from decksnag.config import Config
from decksnag.capture import ScreenCapture
from decksnag.comparison import ImageComparator
from decksnag.presentation import PresentationManager
from decksnag.exporter import Exporter

__all__ = [
    "Config",
    "ScreenCapture",
    "ImageComparator",
    "PresentationManager",
    "Exporter",
    "__version__",
]
