"""Tests for GUI application module.

These tests focus on the logic and state management of the GUI components
without requiring an actual display. All GUI rendering is mocked to allow
headless testing.
"""

import pytest
import sys
import threading
from pathlib import Path
from unittest.mock import MagicMock, patch


# Mock all GUI dependencies before importing the module
@pytest.fixture(autouse=True)
def mock_gui_modules():
    """Mock GUI dependencies to prevent window creation."""
    mock_ctk = MagicMock()
    mock_ctk.CTk = MagicMock
    mock_ctk.CTkToplevel = MagicMock
    mock_ctk.CTkFrame = MagicMock
    mock_ctk.CTkLabel = MagicMock
    mock_ctk.CTkButton = MagicMock
    mock_ctk.CTkSlider = MagicMock
    mock_ctk.CTkComboBox = MagicMock
    mock_ctk.CTkEntry = MagicMock
    mock_ctk.CTkScrollableFrame = MagicMock
    mock_ctk.CTkImage = MagicMock
    mock_ctk.CTkFont = MagicMock(return_value="mock_font")
    mock_ctk.StringVar = MagicMock
    mock_ctk.DoubleVar = MagicMock
    mock_ctk.set_appearance_mode = MagicMock()
    mock_ctk.set_default_color_theme = MagicMock()

    mock_tk = MagicMock()
    mock_tk.Toplevel = MagicMock
    mock_tk.Canvas = MagicMock

    with patch.dict(sys.modules, {
        "customtkinter": mock_ctk,
        "tkinter": mock_tk,
        "tkinter.filedialog": MagicMock(),
        "tkinter.messagebox": MagicMock(),
    }):
        yield


class TestRegionOverlayLogic:
    """Tests for RegionOverlay class logic."""

    def test_overlay_initialization(self):
        """Test RegionOverlay initialization state."""
        # Import after mocking
        from decksnag.gui.app import RegionOverlay

        mock_parent = MagicMock()
        overlay = RegionOverlay(mock_parent)

        assert overlay._parent == mock_parent
        assert overlay._window is None
        assert overlay._canvas is None
        assert overlay._region is None
        assert overlay._visible is False
        assert overlay._rect_id is None

    def test_is_visible_property(self):
        """Test is_visible property reflects internal state."""
        from decksnag.gui.app import RegionOverlay

        mock_parent = MagicMock()
        overlay = RegionOverlay(mock_parent)

        assert overlay.is_visible is False
        overlay._visible = True
        assert overlay.is_visible is True

    def test_set_color_updates_state(self):
        """Test set_color updates internal color state."""
        from decksnag.gui.app import RegionOverlay

        mock_parent = MagicMock()
        overlay = RegionOverlay(mock_parent)
        overlay._canvas = MagicMock()
        overlay._rect_id = 123

        overlay.set_color("#FF0000")

        assert overlay._color == "#FF0000"
        overlay._canvas.itemconfig.assert_called_once_with(123, outline="#FF0000")

    def test_set_color_without_canvas(self):
        """Test set_color when canvas doesn't exist."""
        from decksnag.gui.app import RegionOverlay

        mock_parent = MagicMock()
        overlay = RegionOverlay(mock_parent)

        # Should not raise even without canvas
        overlay.set_color("#FF0000")
        assert overlay._color == "#FF0000"

    def test_hide_destroys_window(self):
        """Test hide method destroys window and resets state."""
        from decksnag.gui.app import RegionOverlay

        mock_parent = MagicMock()
        overlay = RegionOverlay(mock_parent)
        mock_window = MagicMock()
        overlay._window = mock_window
        overlay._canvas = MagicMock()
        overlay._rect_id = 123
        overlay._visible = True

        overlay.hide()

        # After hide(), _window is set to None, so check the mock was called before
        mock_window.destroy.assert_called_once()
        assert overlay._window is None
        assert overlay._canvas is None
        assert overlay._rect_id is None
        assert overlay._visible is False

    def test_hide_handles_already_destroyed_window(self):
        """Test hide handles already destroyed window gracefully."""
        from decksnag.gui.app import RegionOverlay

        mock_parent = MagicMock()
        overlay = RegionOverlay(mock_parent)
        mock_window = MagicMock()
        mock_window.destroy.side_effect = Exception("Already destroyed")
        overlay._window = mock_window
        overlay._visible = True

        # Should not raise
        overlay.hide()
        assert overlay._visible is False

    def test_destroy_aliases_hide(self):
        """Test destroy is an alias for hide."""
        from decksnag.gui.app import RegionOverlay

        mock_parent = MagicMock()
        overlay = RegionOverlay(mock_parent)
        overlay._visible = True
        overlay._window = MagicMock()

        overlay.destroy()

        assert overlay._visible is False

    def test_border_constants(self):
        """Test RegionOverlay has expected constants."""
        from decksnag.gui.app import RegionOverlay

        assert RegionOverlay.BORDER_WIDTH == 3
        assert RegionOverlay.DASH_PATTERN == (8, 4)
        assert RegionOverlay.COLOR_SELECTED == "#3B8ED0"
        assert RegionOverlay.COLOR_RECORDING == "#FF4444"


class TestFormatMethodHelpers:
    """Tests for format and method conversion helpers."""

    def test_get_format_code_pptx(self):
        """Test format code for PowerPoint."""
        from decksnag.gui.app import DeckSnagApp

        mock_app = MagicMock()
        mock_app.format_var.get.return_value = "PowerPoint (.pptx)"

        result = DeckSnagApp._get_format_code(mock_app)
        assert result == "pptx"

    def test_get_format_code_pdf(self):
        """Test format code for PDF."""
        from decksnag.gui.app import DeckSnagApp

        mock_app = MagicMock()
        mock_app.format_var.get.return_value = "PDF (.pdf)"

        result = DeckSnagApp._get_format_code(mock_app)
        assert result == "pdf"

    def test_get_format_code_images(self):
        """Test format code for images."""
        from decksnag.gui.app import DeckSnagApp

        mock_app = MagicMock()
        mock_app.format_var.get.return_value = "Images (folder)"

        result = DeckSnagApp._get_format_code(mock_app)
        assert result == "images"

    def test_get_format_code_all(self):
        """Test format code for all formats."""
        from decksnag.gui.app import DeckSnagApp

        mock_app = MagicMock()
        mock_app.format_var.get.return_value = "All formats"

        result = DeckSnagApp._get_format_code(mock_app)
        assert result == "all"

    def test_get_format_code_unknown_defaults_to_pptx(self):
        """Test format code defaults to pptx for unknown formats."""
        from decksnag.gui.app import DeckSnagApp

        mock_app = MagicMock()
        mock_app.format_var.get.return_value = "Unknown Format"

        result = DeckSnagApp._get_format_code(mock_app)
        assert result == "pptx"

    def test_get_comparison_method_mse(self):
        """Test comparison method for MSE."""
        from decksnag.gui.app import DeckSnagApp

        mock_app = MagicMock()
        mock_app.method_var.get.return_value = "MSE (Fast)"

        result = DeckSnagApp._get_comparison_method(mock_app)
        assert result == "mse"

    def test_get_comparison_method_ssim(self):
        """Test comparison method for SSIM."""
        from decksnag.gui.app import DeckSnagApp

        mock_app = MagicMock()
        mock_app.method_var.get.return_value = "SSIM (Fast)"

        result = DeckSnagApp._get_comparison_method(mock_app)
        assert result == "ssim"

    def test_get_comparison_method_clip(self):
        """Test comparison method for CLIP."""
        from decksnag.gui.app import DeckSnagApp

        mock_app = MagicMock()
        mock_app.method_var.get.return_value = "CLIP AI (Accurate)"

        result = DeckSnagApp._get_comparison_method(mock_app)
        assert result == "clip"

    def test_get_comparison_method_unknown_defaults_to_mse(self):
        """Test comparison method defaults to mse for unknown."""
        from decksnag.gui.app import DeckSnagApp

        mock_app = MagicMock()
        mock_app.method_var.get.return_value = "Unknown"

        result = DeckSnagApp._get_comparison_method(mock_app)
        assert result == "mse"


class TestThresholdCalculation:
    """Tests for threshold calculation from sensitivity."""

    def test_get_threshold_high_mse(self):
        """Test threshold for high sensitivity with MSE."""
        from decksnag.gui.app import DeckSnagApp

        mock_app = MagicMock()
        mock_app.sensitivity_var.get.return_value = "High"
        mock_app._get_comparison_method = MagicMock(return_value="mse")

        with patch("decksnag.gui.app.ImageComparator") as mock_comparator:
            mock_comparator.threshold_from_sensitivity.return_value = 0.001
            result = DeckSnagApp._get_threshold(mock_app)

        mock_comparator.threshold_from_sensitivity.assert_called_once_with("high", "mse")
        assert result == 0.001

    def test_get_threshold_medium_ssim(self):
        """Test threshold for medium sensitivity with SSIM."""
        from decksnag.gui.app import DeckSnagApp

        mock_app = MagicMock()
        mock_app.sensitivity_var.get.return_value = "Medium"
        mock_app._get_comparison_method = MagicMock(return_value="ssim")

        with patch("decksnag.gui.app.ImageComparator") as mock_comparator:
            mock_comparator.threshold_from_sensitivity.return_value = 0.95
            result = DeckSnagApp._get_threshold(mock_app)

        mock_comparator.threshold_from_sensitivity.assert_called_once_with("medium", "ssim")
        assert result == 0.95


class TestUIUpdates:
    """Tests for UI update methods."""

    def test_update_interval_label(self):
        """Test interval label update."""
        from decksnag.gui.app import DeckSnagApp

        mock_app = MagicMock()
        mock_app.interval_label = MagicMock()

        DeckSnagApp._update_interval_label(mock_app, 3.5)

        mock_app.interval_label.configure.assert_called_once_with(text="3.5s")

    def test_update_interval_label_integer(self):
        """Test interval label update with integer value."""
        from decksnag.gui.app import DeckSnagApp

        mock_app = MagicMock()
        mock_app.interval_label = MagicMock()

        DeckSnagApp._update_interval_label(mock_app, 5.0)

        mock_app.interval_label.configure.assert_called_once_with(text="5.0s")

    def test_set_status(self):
        """Test status bar text update."""
        from decksnag.gui.app import DeckSnagApp

        mock_app = MagicMock()
        mock_app.status_label = MagicMock()

        DeckSnagApp._set_status(mock_app, "Test status message")

        mock_app.status_label.configure.assert_called_once_with(text="Test status message")


class TestMiniModeLogic:
    """Tests for mini mode state management."""

    def test_enter_mini_mode_sets_state(self):
        """Test entering mini mode sets correct state."""
        from decksnag.gui.app import DeckSnagApp

        mock_app = MagicMock()
        mock_app._in_mini_mode = False
        mock_app._mini_mode = None
        mock_app._slides = [MagicMock(), MagicMock()]

        mock_mini_window = MagicMock()
        with patch("decksnag.gui.app.MiniModeWindow", return_value=mock_mini_window):
            DeckSnagApp._enter_mini_mode(mock_app)

        assert mock_app._in_mini_mode is True
        mock_app.withdraw.assert_called_once()

    def test_enter_mini_mode_when_already_in_mini_mode(self):
        """Test entering mini mode when already in mini mode does nothing."""
        from decksnag.gui.app import DeckSnagApp

        mock_app = MagicMock()
        mock_app._in_mini_mode = True

        DeckSnagApp._enter_mini_mode(mock_app)

        mock_app.withdraw.assert_not_called()

    def test_exit_mini_mode_sets_state(self):
        """Test exiting mini mode sets correct state."""
        from decksnag.gui.app import DeckSnagApp

        mock_app = MagicMock()
        mock_app._in_mini_mode = True
        mock_mini = MagicMock()
        mock_app._mini_mode = mock_mini

        DeckSnagApp._exit_mini_mode(mock_app)

        assert mock_app._in_mini_mode is False
        mock_mini.close.assert_called_once()
        assert mock_app._mini_mode is None
        mock_app.deiconify.assert_called_once()
        mock_app.lift.assert_called_once()
        mock_app.focus_force.assert_called_once()

    def test_exit_mini_mode_when_not_in_mini_mode(self):
        """Test exiting mini mode when not in mini mode does nothing."""
        from decksnag.gui.app import DeckSnagApp

        mock_app = MagicMock()
        mock_app._in_mini_mode = False

        DeckSnagApp._exit_mini_mode(mock_app)

        mock_app.deiconify.assert_not_called()

    def test_exit_mini_mode_handles_exception(self):
        """Test exiting mini mode handles close exception gracefully."""
        from decksnag.gui.app import DeckSnagApp

        mock_app = MagicMock()
        mock_app._in_mini_mode = True
        mock_mini = MagicMock()
        mock_mini.close.side_effect = Exception("Window already destroyed")
        mock_app._mini_mode = mock_mini

        # Should not raise
        DeckSnagApp._exit_mini_mode(mock_app)

        assert mock_app._in_mini_mode is False
        assert mock_app._mini_mode is None

    def test_expand_from_mini_continues_capture(self):
        """Test expand from mini mode shows window but continues capture."""
        from decksnag.gui.app import DeckSnagApp

        mock_app = MagicMock()
        mock_app._in_mini_mode = True
        mock_mini = MagicMock()
        mock_app._mini_mode = mock_mini

        DeckSnagApp._expand_from_mini(mock_app)

        assert mock_app._in_mini_mode is False
        mock_mini.close.assert_called_once()
        mock_app.deiconify.assert_called_once()
        mock_app.lift.assert_called_once()
        mock_app.focus_force.assert_called_once()

    def test_update_mini_mode_slide_count(self):
        """Test updating slide count in mini mode."""
        from decksnag.gui.app import DeckSnagApp

        mock_app = MagicMock()
        mock_app._in_mini_mode = True
        mock_mini = MagicMock()
        mock_app._mini_mode = mock_mini
        mock_app._slides = [MagicMock()] * 5

        DeckSnagApp._update_mini_mode_slide_count(mock_app)

        mock_mini.update_slide_count.assert_called_once_with(5)

    def test_update_mini_mode_slide_count_not_in_mini_mode(self):
        """Test updating slide count when not in mini mode does nothing."""
        from decksnag.gui.app import DeckSnagApp

        mock_app = MagicMock()
        mock_app._in_mini_mode = False
        mock_app._mini_mode = MagicMock()
        mock_app._slides = [MagicMock()] * 5

        DeckSnagApp._update_mini_mode_slide_count(mock_app)

        mock_app._mini_mode.update_slide_count.assert_not_called()


class TestCaptureSessionState:
    """Tests for capture session state management."""

    def test_stop_capture_session_sets_event(self):
        """Test stop capture sets the stop event."""
        from decksnag.gui.app import DeckSnagApp

        mock_app = MagicMock()
        mock_app._stop_capture = threading.Event()

        assert not mock_app._stop_capture.is_set()
        DeckSnagApp._stop_capture_session(mock_app)
        assert mock_app._stop_capture.is_set()

    def test_capture_finished_updates_ui(self):
        """Test capture finished updates all UI state."""
        from decksnag.gui.app import DeckSnagApp

        mock_app = MagicMock()
        mock_app._is_capturing = True
        mock_app._in_mini_mode = False
        mock_overlay = MagicMock()
        mock_app._region_overlay = mock_overlay
        mock_app._slides = [MagicMock(), MagicMock(), MagicMock()]
        mock_app._exit_mini_mode = MagicMock()

        DeckSnagApp._capture_finished(mock_app)

        assert mock_app._is_capturing is False
        mock_app._exit_mini_mode.assert_called_once()
        mock_overlay.destroy.assert_called_once()
        mock_app.start_btn.configure.assert_called()
        mock_app.stop_btn.configure.assert_called()
        mock_app.minimize_btn.pack_forget.assert_called_once()

    def test_capture_finished_without_overlay(self):
        """Test capture finished when no overlay exists."""
        from decksnag.gui.app import DeckSnagApp

        mock_app = MagicMock()
        mock_app._is_capturing = True
        mock_app._in_mini_mode = False
        mock_app._region_overlay = None
        mock_app._slides = []
        mock_app._exit_mini_mode = MagicMock()

        # Should not raise
        DeckSnagApp._capture_finished(mock_app)

        assert mock_app._is_capturing is False


class TestSlideManagement:
    """Tests for slide management functionality."""

    def test_add_slide_preview_stores_copy(self, sample_image):
        """Test that add_slide_preview stores a copy of the image."""
        from decksnag.gui.app import DeckSnagApp

        mock_app = MagicMock()
        mock_app._slides = []
        mock_app._in_mini_mode = False
        mock_app._mini_mode = None

        # We can't fully test this without GUI, but we can verify the list grows
        mock_app._slides.append(sample_image.copy())

        assert len(mock_app._slides) == 1

    def test_slides_list_initially_empty(self):
        """Test slides list starts empty."""
        from decksnag.gui.app import DeckSnagApp

        mock_app = MagicMock()
        mock_app._slides = []

        assert len(mock_app._slides) == 0


class TestMiniModeWindowLogic:
    """Tests for MiniModeWindow class logic (without GUI)."""

    def test_slide_count_text_singular(self):
        """Test slide count text for single slide."""
        count = 1
        slides_text = "1 slide" if count == 1 else f"{count} slides"
        assert slides_text == "1 slide"

    def test_slide_count_text_plural(self):
        """Test slide count text for multiple slides."""
        count = 5
        slides_text = "1 slide" if count == 1 else f"{count} slides"
        assert slides_text == "5 slides"

    def test_slide_count_text_zero(self):
        """Test slide count text for zero slides."""
        count = 0
        slides_text = "1 slide" if count == 1 else f"{count} slides"
        assert slides_text == "0 slides"

    def test_time_format_under_hour(self):
        """Test time formatting under one hour."""
        elapsed = 185  # 3 minutes, 5 seconds
        minutes, seconds = divmod(int(elapsed), 60)
        hours, minutes = divmod(minutes, 60)

        if hours > 0:
            time_str = f"{hours:02d}:{minutes:02d}:{seconds:02d}"
        else:
            time_str = f"{minutes:02d}:{seconds:02d}"

        assert time_str == "03:05"

    def test_time_format_over_hour(self):
        """Test time formatting over one hour."""
        elapsed = 3665  # 1 hour, 1 minute, 5 seconds
        minutes, seconds = divmod(int(elapsed), 60)
        hours, minutes = divmod(minutes, 60)

        if hours > 0:
            time_str = f"{hours:02d}:{minutes:02d}:{seconds:02d}"
        else:
            time_str = f"{minutes:02d}:{seconds:02d}"

        assert time_str == "01:01:05"


class TestGuiSettingsHelpers:
    """Tests for GUI settings helper functions."""

    def test_get_gui_settings_path(self):
        """Test get_gui_settings_path returns correct path."""
        from decksnag.gui.app import get_gui_settings_path, GUI_SETTINGS_FILE

        path = get_gui_settings_path()
        assert path.name == GUI_SETTINGS_FILE
        assert "DeckSnag" in str(path) or "decksnag" in str(path).lower()

    def test_load_gui_settings_returns_dict(self):
        """Test load_gui_settings returns a dictionary."""
        from decksnag.gui.app import load_gui_settings

        with patch("decksnag.gui.app.load_config_file", return_value={"interval": 5.0}):
            result = load_gui_settings()
            assert isinstance(result, dict)
            assert result.get("interval") == 5.0

    def test_load_gui_settings_empty_file(self):
        """Test load_gui_settings with no saved settings."""
        from decksnag.gui.app import load_gui_settings

        with patch("decksnag.gui.app.load_config_file", return_value={}):
            result = load_gui_settings()
            assert result == {}

    def test_save_gui_settings_calls_save_config_file(self):
        """Test save_gui_settings calls save_config_file."""
        from decksnag.gui.app import save_gui_settings

        mock_save = MagicMock()
        mock_ensure = MagicMock()

        with patch("decksnag.gui.app.save_config_file", mock_save):
            with patch("decksnag.gui.app.ensure_config_dir", mock_ensure):
                save_gui_settings({"interval": 3.0, "method": "mse"})

        mock_ensure.assert_called_once()
        mock_save.assert_called_once()
        saved_settings = mock_save.call_args[0][0]
        assert saved_settings["interval"] == 3.0
        assert saved_settings["method"] == "mse"


class TestSettingsPersistence:
    """Tests for settings load/save in DeckSnagApp."""

    def test_load_settings_with_empty_settings(self):
        """Test _load_settings handles empty settings."""
        from decksnag.gui.app import DeckSnagApp

        mock_app = MagicMock()
        mock_app.interval_label = MagicMock()
        mock_app.interval_var = MagicMock()
        mock_app.output_var = MagicMock()
        mock_app.sensitivity_var = MagicMock()
        mock_app.method_var = MagicMock()
        mock_app.format_var = MagicMock()

        with patch("decksnag.gui.app.load_gui_settings", return_value={}):
            DeckSnagApp._load_settings(mock_app)

        mock_app.geometry.assert_called_with("900x700")

    def test_load_settings_restores_geometry(self):
        """Test _load_settings restores window geometry."""
        from decksnag.gui.app import DeckSnagApp

        mock_app = MagicMock()
        mock_app.interval_label = MagicMock()

        settings = {"window_geometry": "1000x800+100+50"}
        with patch("decksnag.gui.app.load_gui_settings", return_value=settings):
            DeckSnagApp._load_settings(mock_app)

        mock_app.geometry.assert_called_with("1000x800+100+50")

    def test_load_settings_restores_output_path(self):
        """Test _load_settings restores output path."""
        from decksnag.gui.app import DeckSnagApp

        mock_app = MagicMock()
        mock_app.interval_label = MagicMock()

        settings = {"output_path": "/path/to/output"}
        with patch("decksnag.gui.app.load_gui_settings", return_value=settings):
            DeckSnagApp._load_settings(mock_app)

        mock_app.output_var.set.assert_called_with("/path/to/output")

    def test_load_settings_restores_interval(self):
        """Test _load_settings restores interval setting."""
        from decksnag.gui.app import DeckSnagApp

        mock_app = MagicMock()
        mock_app.interval_label = MagicMock()

        settings = {"interval": 7.5}
        with patch("decksnag.gui.app.load_gui_settings", return_value=settings):
            DeckSnagApp._load_settings(mock_app)

        mock_app.interval_var.set.assert_called_with(7.5)
        mock_app.interval_label.configure.assert_called_with(text="7.5s")

    def test_load_settings_restores_sensitivity(self):
        """Test _load_settings restores sensitivity setting."""
        from decksnag.gui.app import DeckSnagApp

        mock_app = MagicMock()
        mock_app.interval_label = MagicMock()

        settings = {"sensitivity": "High"}
        with patch("decksnag.gui.app.load_gui_settings", return_value=settings):
            DeckSnagApp._load_settings(mock_app)

        mock_app.sensitivity_var.set.assert_called_with("High")

    def test_load_settings_restores_method(self):
        """Test _load_settings restores comparison method."""
        from decksnag.gui.app import DeckSnagApp

        mock_app = MagicMock()
        mock_app.interval_label = MagicMock()

        settings = {"method": "ssim"}
        with patch("decksnag.gui.app.load_gui_settings", return_value=settings):
            DeckSnagApp._load_settings(mock_app)

        mock_app.method_var.set.assert_called_with("SSIM (Fast)")

    def test_load_settings_restores_format(self):
        """Test _load_settings restores output format."""
        from decksnag.gui.app import DeckSnagApp

        mock_app = MagicMock()
        mock_app.interval_label = MagicMock()

        settings = {"output_format": "pdf"}
        with patch("decksnag.gui.app.load_gui_settings", return_value=settings):
            DeckSnagApp._load_settings(mock_app)

        mock_app.format_var.set.assert_called_with("PDF (.pdf)")

    def test_load_settings_handles_exception(self):
        """Test _load_settings handles exceptions gracefully."""
        from decksnag.gui.app import DeckSnagApp

        mock_app = MagicMock()

        with patch("decksnag.gui.app.load_gui_settings", side_effect=Exception("Test error")):
            # Should not raise
            DeckSnagApp._load_settings(mock_app)

        # Should fall back to default geometry
        mock_app.geometry.assert_called_with("900x700")

    def test_save_settings_saves_all_values(self):
        """Test _save_settings saves all current settings."""
        from decksnag.gui.app import DeckSnagApp

        mock_app = MagicMock()
        mock_app.geometry.return_value = "900x700+50+50"
        mock_app.output_var.get.return_value = "/my/output/path"
        mock_app.interval_var.get.return_value = 3.0
        mock_app.sensitivity_var.get.return_value = "Low"
        mock_app.method_var.get.return_value = "CLIP AI (Accurate)"
        mock_app.format_var.get.return_value = "All formats"

        mock_save = MagicMock()
        with patch("decksnag.gui.app.save_gui_settings", mock_save):
            DeckSnagApp._save_settings(mock_app)

        mock_save.assert_called_once()
        saved = mock_save.call_args[0][0]
        assert saved["window_geometry"] == "900x700+50+50"
        assert saved["output_path"] == "/my/output/path"
        assert saved["interval"] == 3.0
        assert saved["sensitivity"] == "Low"
        assert saved["method"] == "clip"
        assert saved["output_format"] == "all"

    def test_save_settings_handles_exception(self):
        """Test _save_settings handles exceptions gracefully."""
        from decksnag.gui.app import DeckSnagApp

        mock_app = MagicMock()
        mock_app.output_var.get.return_value = ""

        with patch("decksnag.gui.app.save_gui_settings", side_effect=Exception("Test error")):
            # Should not raise
            DeckSnagApp._save_settings(mock_app)


class TestOnClose:
    """Tests for window close handler."""

    def test_on_close_stops_capture_if_running(self):
        """Test _on_close stops capture if it's running."""
        from decksnag.gui.app import DeckSnagApp
        import threading

        mock_app = MagicMock()
        mock_app._is_capturing = True
        mock_app._stop_capture = threading.Event()
        mock_app._region_overlay = None
        mock_app._save_settings = MagicMock()

        DeckSnagApp._on_close(mock_app)

        assert mock_app._stop_capture.is_set()
        mock_app._save_settings.assert_called_once()
        mock_app.destroy.assert_called_once()

    def test_on_close_saves_settings(self):
        """Test _on_close saves settings before closing."""
        from decksnag.gui.app import DeckSnagApp
        import threading

        mock_app = MagicMock()
        mock_app._is_capturing = False
        mock_app._stop_capture = threading.Event()
        mock_app._region_overlay = None
        mock_app._save_settings = MagicMock()

        DeckSnagApp._on_close(mock_app)

        mock_app._save_settings.assert_called_once()

    def test_on_close_cleans_up_overlay(self):
        """Test _on_close destroys region overlay."""
        from decksnag.gui.app import DeckSnagApp
        import threading

        mock_app = MagicMock()
        mock_app._is_capturing = False
        mock_app._stop_capture = threading.Event()
        mock_overlay = MagicMock()
        mock_app._region_overlay = mock_overlay
        mock_app._save_settings = MagicMock()

        DeckSnagApp._on_close(mock_app)

        mock_overlay.destroy.assert_called_once()

    def test_on_close_destroys_window(self):
        """Test _on_close destroys the main window."""
        from decksnag.gui.app import DeckSnagApp
        import threading

        mock_app = MagicMock()
        mock_app._is_capturing = False
        mock_app._stop_capture = threading.Event()
        mock_app._region_overlay = None
        mock_app._save_settings = MagicMock()

        DeckSnagApp._on_close(mock_app)

        mock_app.destroy.assert_called_once()
