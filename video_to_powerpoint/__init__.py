"""Video to PowerPoint - Capture presentations and convert to slides automatically."""

__version__ = "2.0.0"
__author__ = "Derek Plemons"
__email__ = "plemons.derek@gmail.com"

from video_to_powerpoint.config import Config
from video_to_powerpoint.capture import ScreenCapture
from video_to_powerpoint.comparison import ImageComparator
from video_to_powerpoint.presentation import PresentationManager
from video_to_powerpoint.exporter import Exporter

__all__ = [
    "Config",
    "ScreenCapture",
    "ImageComparator",
    "PresentationManager",
    "Exporter",
    "__version__",
]
