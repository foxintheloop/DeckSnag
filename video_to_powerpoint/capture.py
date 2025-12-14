"""Screen capture functionality with multi-monitor support."""

import logging
from typing import List, Optional, Tuple, Dict, Any
from dataclasses import dataclass
from PIL import Image
import mss
import mss.tools
from pynput import mouse

logger = logging.getLogger("video_to_powerpoint")


@dataclass
class Monitor:
    """Represents a monitor/display.

    Attributes:
        id: Monitor index (0 = all monitors combined, 1+ = individual monitors).
        left: Left edge x-coordinate.
        top: Top edge y-coordinate.
        width: Monitor width in pixels.
        height: Monitor height in pixels.
        name: Human-readable name.
    """

    id: int
    left: int
    top: int
    width: int
    height: int
    name: str = ""

    @property
    def right(self) -> int:
        """Right edge x-coordinate."""
        return self.left + self.width

    @property
    def bottom(self) -> int:
        """Bottom edge y-coordinate."""
        return self.top + self.height

    @property
    def region(self) -> Tuple[int, int, int, int]:
        """Region as (x1, y1, x2, y2) tuple."""
        return (self.left, self.top, self.right, self.bottom)

    def __str__(self) -> str:
        return f"Monitor {self.id}: {self.width}x{self.height} at ({self.left}, {self.top})"


class ScreenCapture:
    """Handles screen capture with region selection and multi-monitor support."""

    def __init__(self) -> None:
        """Initialize the screen capture handler."""
        self._sct = mss.mss()
        self._monitors: List[Monitor] = []
        self._refresh_monitors()

    def _refresh_monitors(self) -> None:
        """Refresh the list of available monitors."""
        self._monitors = []
        for i, mon in enumerate(self._sct.monitors):
            name = "All Monitors" if i == 0 else f"Monitor {i}"
            self._monitors.append(
                Monitor(
                    id=i,
                    left=mon["left"],
                    top=mon["top"],
                    width=mon["width"],
                    height=mon["height"],
                    name=name,
                )
            )

    def list_monitors(self) -> List[Monitor]:
        """Get list of available monitors.

        Returns:
            List of Monitor objects. Index 0 is all monitors combined.
        """
        self._refresh_monitors()
        return self._monitors.copy()

    def get_monitor(self, monitor_id: int = 1) -> Monitor:
        """Get a specific monitor by ID.

        Args:
            monitor_id: Monitor index (0 = all, 1+ = specific monitor).

        Returns:
            Monitor object.

        Raises:
            ValueError: If monitor_id is invalid.
        """
        self._refresh_monitors()
        if monitor_id < 0 or monitor_id >= len(self._monitors):
            raise ValueError(
                f"Invalid monitor ID: {monitor_id}. "
                f"Available: 0-{len(self._monitors) - 1}"
            )
        return self._monitors[monitor_id]

    def select_region_interactive(self) -> Tuple[int, int, int, int]:
        """Interactively select a screen region using mouse click and drag.

        The user clicks to set the top-left corner and releases to set
        the bottom-right corner.

        Returns:
            Tuple of (x1, y1, x2, y2) representing the selected region.

        Raises:
            RuntimeError: If selection fails or is cancelled.
        """
        logger.info("Click and drag to select the capture region...")
        print("\n" + "=" * 50)
        print("REGION SELECTION")
        print("=" * 50)
        print("Click and hold at the TOP-LEFT corner of the area")
        print("Drag to the BOTTOM-RIGHT corner and release")
        print("=" * 50 + "\n")

        coordinates: Dict[str, Optional[int]] = {
            "x1": None,
            "y1": None,
            "x2": None,
            "y2": None,
        }
        selection_complete = False

        def on_click(x: int, y: int, button: mouse.Button, pressed: bool) -> bool:
            nonlocal selection_complete

            if button == mouse.Button.left:
                if pressed:
                    # Mouse pressed - start of selection
                    coordinates["x1"] = x
                    coordinates["y1"] = y
                    logger.debug(f"Selection start: ({x}, {y})")
                else:
                    # Mouse released - end of selection
                    coordinates["x2"] = x
                    coordinates["y2"] = y
                    logger.debug(f"Selection end: ({x}, {y})")
                    selection_complete = True
                    return False  # Stop listener

            return True  # Continue listening

        # Start listening for mouse events
        with mouse.Listener(on_click=on_click) as listener:
            listener.join()

        # Validate selection
        if not all(v is not None for v in coordinates.values()):
            raise RuntimeError("Region selection was incomplete")

        x1, y1 = coordinates["x1"], coordinates["y1"]
        x2, y2 = coordinates["x2"], coordinates["y2"]

        # Normalize coordinates (ensure x1 < x2 and y1 < y2)
        if x1 > x2:
            x1, x2 = x2, x1
        if y1 > y2:
            y1, y2 = y2, y1

        # Validate region size
        width = x2 - x1
        height = y2 - y1

        if width < 10 or height < 10:
            raise RuntimeError(
                f"Selected region too small: {width}x{height}. "
                "Minimum size is 10x10 pixels."
            )

        region = (x1, y1, x2, y2)
        logger.info(f"Selected region: {region} ({width}x{height} pixels)")
        print(f"\nSelected region: {width}x{height} pixels")

        return region

    def capture_region(self, region: Tuple[int, int, int, int]) -> Image.Image:
        """Capture a screenshot of a specific region.

        Args:
            region: Tuple of (x1, y1, x2, y2) coordinates.

        Returns:
            PIL Image of the captured region.

        Raises:
            ValueError: If region is invalid.
            RuntimeError: If capture fails.
        """
        x1, y1, x2, y2 = region

        # Validate region
        if x2 <= x1 or y2 <= y1:
            raise ValueError(f"Invalid region: {region}")

        # Convert to mss format
        monitor_dict = {
            "left": x1,
            "top": y1,
            "width": x2 - x1,
            "height": y2 - y1,
        }

        try:
            # Capture the screen
            screenshot = self._sct.grab(monitor_dict)

            # Convert to PIL Image
            img = Image.frombytes(
                "RGB",
                (screenshot.width, screenshot.height),
                screenshot.rgb,
            )

            logger.debug(f"Captured region: {region}")
            return img

        except Exception as e:
            raise RuntimeError(f"Failed to capture screenshot: {e}")

    def capture_monitor(self, monitor_id: int = 1) -> Image.Image:
        """Capture a full monitor screenshot.

        Args:
            monitor_id: Monitor index (0 = all, 1+ = specific monitor).

        Returns:
            PIL Image of the monitor.
        """
        monitor = self.get_monitor(monitor_id)
        return self.capture_region(monitor.region)

    def __enter__(self) -> "ScreenCapture":
        """Context manager entry."""
        return self

    def __exit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        """Context manager exit - cleanup resources."""
        self._sct.close()

    def close(self) -> None:
        """Explicitly close resources."""
        self._sct.close()
