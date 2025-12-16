"""Tests for screen capture module."""

import pytest
from unittest.mock import MagicMock, patch, PropertyMock
from PIL import Image
from decksnag.capture import Monitor, ScreenCapture


class TestMonitor:
    """Tests for the Monitor dataclass."""

    def test_monitor_creation(self):
        """Test creating a Monitor with basic attributes."""
        mon = Monitor(id=1, left=0, top=0, width=1920, height=1080, name="Primary")

        assert mon.id == 1
        assert mon.left == 0
        assert mon.top == 0
        assert mon.width == 1920
        assert mon.height == 1080
        assert mon.name == "Primary"

    def test_monitor_right_property(self):
        """Test that right property calculates correctly."""
        mon = Monitor(id=1, left=100, top=0, width=1920, height=1080)
        assert mon.right == 2020  # 100 + 1920

    def test_monitor_bottom_property(self):
        """Test that bottom property calculates correctly."""
        mon = Monitor(id=1, left=0, top=50, width=1920, height=1080)
        assert mon.bottom == 1130  # 50 + 1080

    def test_monitor_region_property(self):
        """Test that region property returns correct tuple."""
        mon = Monitor(id=1, left=100, top=50, width=1920, height=1080)
        assert mon.region == (100, 50, 2020, 1130)

    def test_monitor_str(self):
        """Test string representation of Monitor."""
        mon = Monitor(id=2, left=1920, top=0, width=1920, height=1080)
        result = str(mon)
        assert "Monitor 2" in result
        assert "1920x1080" in result
        assert "(1920, 0)" in result

    def test_monitor_default_name(self):
        """Test that name defaults to empty string."""
        mon = Monitor(id=1, left=0, top=0, width=1920, height=1080)
        assert mon.name == ""

    def test_monitor_negative_coordinates(self):
        """Test monitor with negative coordinates (multi-monitor setups)."""
        mon = Monitor(id=2, left=-1920, top=0, width=1920, height=1080)
        assert mon.left == -1920
        assert mon.right == 0
        assert mon.region == (-1920, 0, 0, 1080)


class TestScreenCapture:
    """Tests for the ScreenCapture class."""

    @pytest.fixture
    def mock_mss(self):
        """Create a mock mss instance."""
        mock_sct = MagicMock()
        mock_sct.monitors = [
            {"left": 0, "top": 0, "width": 3840, "height": 1080},  # All monitors
            {"left": 0, "top": 0, "width": 1920, "height": 1080},  # Monitor 1
            {"left": 1920, "top": 0, "width": 1920, "height": 1080},  # Monitor 2
        ]
        return mock_sct

    @pytest.fixture
    def mock_screenshot(self):
        """Create a mock screenshot result."""
        mock_shot = MagicMock()
        mock_shot.width = 800
        mock_shot.height = 600
        # Create actual RGB bytes for an 800x600 white image
        mock_shot.rgb = bytes([255, 255, 255] * 800 * 600)
        return mock_shot

    def test_init_creates_monitors(self, mock_mss):
        """Test that initialization populates monitor list."""
        with patch("decksnag.capture.mss.mss", return_value=mock_mss):
            capture = ScreenCapture()
            monitors = capture.list_monitors()

            assert len(monitors) == 3
            assert monitors[0].name == "All Monitors"
            assert monitors[1].name == "Monitor 1"
            assert monitors[2].name == "Monitor 2"

    def test_list_monitors(self, mock_mss):
        """Test listing all available monitors."""
        with patch("decksnag.capture.mss.mss", return_value=mock_mss):
            capture = ScreenCapture()
            monitors = capture.list_monitors()

            assert len(monitors) == 3
            # Monitor 0 is all monitors combined
            assert monitors[0].width == 3840
            assert monitors[0].height == 1080
            # Monitor 1
            assert monitors[1].left == 0
            assert monitors[1].width == 1920
            # Monitor 2
            assert monitors[2].left == 1920
            assert monitors[2].width == 1920

    def test_list_monitors_returns_copy(self, mock_mss):
        """Test that list_monitors returns a copy, not the internal list."""
        with patch("decksnag.capture.mss.mss", return_value=mock_mss):
            capture = ScreenCapture()
            monitors1 = capture.list_monitors()
            monitors2 = capture.list_monitors()

            assert monitors1 is not monitors2

    def test_get_monitor_valid(self, mock_mss):
        """Test getting a valid monitor by ID."""
        with patch("decksnag.capture.mss.mss", return_value=mock_mss):
            capture = ScreenCapture()

            mon0 = capture.get_monitor(0)
            assert mon0.id == 0
            assert mon0.name == "All Monitors"

            mon1 = capture.get_monitor(1)
            assert mon1.id == 1
            assert mon1.width == 1920

    def test_get_monitor_invalid_negative(self, mock_mss):
        """Test that negative monitor ID raises error."""
        with patch("decksnag.capture.mss.mss", return_value=mock_mss):
            capture = ScreenCapture()

            with pytest.raises(ValueError, match="Invalid monitor ID"):
                capture.get_monitor(-1)

    def test_get_monitor_invalid_too_high(self, mock_mss):
        """Test that monitor ID beyond range raises error."""
        with patch("decksnag.capture.mss.mss", return_value=mock_mss):
            capture = ScreenCapture()

            with pytest.raises(ValueError, match="Invalid monitor ID"):
                capture.get_monitor(5)

    def test_capture_region_valid(self, mock_mss, mock_screenshot):
        """Test capturing a valid screen region."""
        mock_mss.grab.return_value = mock_screenshot

        with patch("decksnag.capture.mss.mss", return_value=mock_mss):
            capture = ScreenCapture()
            region = (100, 100, 900, 700)
            img = capture.capture_region(region)

            assert isinstance(img, Image.Image)
            assert img.size == (800, 600)
            mock_mss.grab.assert_called_once()

    def test_capture_region_invalid_x_bounds(self, mock_mss):
        """Test that invalid x bounds raise error."""
        with patch("decksnag.capture.mss.mss", return_value=mock_mss):
            capture = ScreenCapture()

            with pytest.raises(ValueError, match="Invalid region"):
                capture.capture_region((800, 100, 100, 600))  # x2 <= x1

    def test_capture_region_invalid_y_bounds(self, mock_mss):
        """Test that invalid y bounds raise error."""
        with patch("decksnag.capture.mss.mss", return_value=mock_mss):
            capture = ScreenCapture()

            with pytest.raises(ValueError, match="Invalid region"):
                capture.capture_region((100, 600, 800, 100))  # y2 <= y1

    def test_capture_region_equal_bounds(self, mock_mss):
        """Test that equal bounds raise error."""
        with patch("decksnag.capture.mss.mss", return_value=mock_mss):
            capture = ScreenCapture()

            with pytest.raises(ValueError, match="Invalid region"):
                capture.capture_region((100, 100, 100, 600))  # x1 == x2

    def test_capture_region_grab_failure(self, mock_mss):
        """Test that capture failure raises RuntimeError."""
        mock_mss.grab.side_effect = Exception("Capture failed")

        with patch("decksnag.capture.mss.mss", return_value=mock_mss):
            capture = ScreenCapture()

            with pytest.raises(RuntimeError, match="Failed to capture screenshot"):
                capture.capture_region((100, 100, 900, 700))

    def test_capture_monitor(self, mock_mss, mock_screenshot):
        """Test capturing a full monitor."""
        mock_mss.grab.return_value = mock_screenshot

        with patch("decksnag.capture.mss.mss", return_value=mock_mss):
            capture = ScreenCapture()
            img = capture.capture_monitor(1)

            assert isinstance(img, Image.Image)
            # Verify grab was called with the monitor's region
            call_args = mock_mss.grab.call_args[0][0]
            assert call_args["left"] == 0
            assert call_args["top"] == 0
            assert call_args["width"] == 1920
            assert call_args["height"] == 1080

    def test_capture_monitor_invalid(self, mock_mss):
        """Test that invalid monitor ID raises error."""
        with patch("decksnag.capture.mss.mss", return_value=mock_mss):
            capture = ScreenCapture()

            with pytest.raises(ValueError, match="Invalid monitor ID"):
                capture.capture_monitor(10)

    def test_context_manager_enter(self, mock_mss):
        """Test context manager __enter__ returns self."""
        with patch("decksnag.capture.mss.mss", return_value=mock_mss):
            capture = ScreenCapture()
            result = capture.__enter__()
            assert result is capture

    def test_context_manager_exit_closes(self, mock_mss):
        """Test context manager __exit__ closes resources."""
        with patch("decksnag.capture.mss.mss", return_value=mock_mss):
            capture = ScreenCapture()
            capture.__exit__(None, None, None)
            mock_mss.close.assert_called_once()

    def test_context_manager_usage(self, mock_mss, mock_screenshot):
        """Test using ScreenCapture as context manager."""
        mock_mss.grab.return_value = mock_screenshot

        with patch("decksnag.capture.mss.mss", return_value=mock_mss):
            with ScreenCapture() as capture:
                img = capture.capture_region((0, 0, 800, 600))
                assert isinstance(img, Image.Image)

            mock_mss.close.assert_called_once()

    def test_close_method(self, mock_mss):
        """Test explicit close method."""
        with patch("decksnag.capture.mss.mss", return_value=mock_mss):
            capture = ScreenCapture()
            capture.close()
            mock_mss.close.assert_called_once()


class TestSelectRegionInteractive:
    """Tests for interactive region selection."""

    @pytest.fixture
    def mock_mss(self):
        """Create a mock mss instance."""
        mock_sct = MagicMock()
        mock_sct.monitors = [
            {"left": 0, "top": 0, "width": 1920, "height": 1080},
        ]
        return mock_sct

    def test_select_region_valid(self, mock_mss):
        """Test valid region selection with mocked mouse events."""
        from pynput import mouse

        def mock_listener_context(on_click):
            # Simulate mouse press at (100, 100)
            on_click(100, 100, mouse.Button.left, True)
            # Simulate mouse release at (500, 400)
            on_click(500, 400, mouse.Button.left, False)

            mock_context = MagicMock()
            mock_context.__enter__ = MagicMock(return_value=mock_context)
            mock_context.__exit__ = MagicMock(return_value=False)
            mock_context.join = MagicMock()
            return mock_context

        with patch("decksnag.capture.mss.mss", return_value=mock_mss):
            with patch("decksnag.capture.mouse.Listener") as mock_listener:
                mock_listener.side_effect = lambda on_click: mock_listener_context(on_click)

                capture = ScreenCapture()
                region = capture.select_region_interactive()

                assert region == (100, 100, 500, 400)

    def test_select_region_normalizes_coordinates(self, mock_mss):
        """Test that coordinates are normalized (x1 < x2, y1 < y2)."""
        from pynput import mouse

        def mock_listener_context(on_click):
            # Simulate selecting from bottom-right to top-left
            on_click(500, 400, mouse.Button.left, True)
            on_click(100, 100, mouse.Button.left, False)

            mock_context = MagicMock()
            mock_context.__enter__ = MagicMock(return_value=mock_context)
            mock_context.__exit__ = MagicMock(return_value=False)
            mock_context.join = MagicMock()
            return mock_context

        with patch("decksnag.capture.mss.mss", return_value=mock_mss):
            with patch("decksnag.capture.mouse.Listener") as mock_listener:
                mock_listener.side_effect = lambda on_click: mock_listener_context(on_click)

                capture = ScreenCapture()
                region = capture.select_region_interactive()

                # Should be normalized
                assert region == (100, 100, 500, 400)

    def test_select_region_too_small(self, mock_mss):
        """Test that region smaller than 10x10 raises error."""
        from pynput import mouse

        def mock_listener_context(on_click):
            # Simulate selecting a 5x5 region
            on_click(100, 100, mouse.Button.left, True)
            on_click(105, 105, mouse.Button.left, False)

            mock_context = MagicMock()
            mock_context.__enter__ = MagicMock(return_value=mock_context)
            mock_context.__exit__ = MagicMock(return_value=False)
            mock_context.join = MagicMock()
            return mock_context

        with patch("decksnag.capture.mss.mss", return_value=mock_mss):
            with patch("decksnag.capture.mouse.Listener") as mock_listener:
                mock_listener.side_effect = lambda on_click: mock_listener_context(on_click)

                capture = ScreenCapture()

                with pytest.raises(RuntimeError, match="too small"):
                    capture.select_region_interactive()

    def test_select_region_ignores_right_click(self, mock_mss):
        """Test that right clicks are ignored during selection."""
        from pynput import mouse

        call_count = [0]

        def mock_listener_context(on_click):
            # Simulate right click (should be ignored)
            result = on_click(50, 50, mouse.Button.right, True)
            assert result is True  # Should continue listening

            # Simulate valid left click selection
            on_click(100, 100, mouse.Button.left, True)
            on_click(500, 400, mouse.Button.left, False)

            mock_context = MagicMock()
            mock_context.__enter__ = MagicMock(return_value=mock_context)
            mock_context.__exit__ = MagicMock(return_value=False)
            mock_context.join = MagicMock()
            return mock_context

        with patch("decksnag.capture.mss.mss", return_value=mock_mss):
            with patch("decksnag.capture.mouse.Listener") as mock_listener:
                mock_listener.side_effect = lambda on_click: mock_listener_context(on_click)

                capture = ScreenCapture()
                region = capture.select_region_interactive()

                assert region == (100, 100, 500, 400)
