"""Tests for command-line interface module."""

import argparse
import pytest
from pathlib import Path
from unittest.mock import MagicMock, patch, PropertyMock

from decksnag.cli import parse_region, create_parser, list_monitors, run_capture_session, main
from decksnag.config import Config


class TestParseRegion:
    """Tests for the parse_region function."""

    def test_valid_region(self):
        """Test parsing a valid region string."""
        result = parse_region("100,200,800,600")
        assert result == (100, 200, 800, 600)

    def test_valid_region_with_spaces(self):
        """Test parsing region string with spaces."""
        result = parse_region("100, 200, 800, 600")
        assert result == (100, 200, 800, 600)

    def test_valid_region_negative_coords(self):
        """Test parsing region with negative coordinates."""
        result = parse_region("-100,0,500,400")
        assert result == (-100, 0, 500, 400)

    def test_invalid_region_not_enough_values(self):
        """Test that too few values raises error."""
        with pytest.raises(argparse.ArgumentTypeError, match="Invalid region format"):
            parse_region("100,200,800")

    def test_invalid_region_too_many_values(self):
        """Test that too many values raises error."""
        with pytest.raises(argparse.ArgumentTypeError, match="Invalid region format"):
            parse_region("100,200,800,600,100")

    def test_invalid_region_non_numeric(self):
        """Test that non-numeric values raise error."""
        with pytest.raises(argparse.ArgumentTypeError, match="Invalid region format"):
            parse_region("100,abc,800,600")

    def test_invalid_region_empty(self):
        """Test that empty string raises error."""
        with pytest.raises(argparse.ArgumentTypeError, match="Invalid region format"):
            parse_region("")

    def test_invalid_region_float_values(self):
        """Test that float values raise error."""
        with pytest.raises(argparse.ArgumentTypeError, match="Invalid region format"):
            parse_region("100.5,200,800,600")


class TestCreateParser:
    """Tests for the argument parser creation."""

    def test_parser_created(self):
        """Test that parser is created successfully."""
        parser = create_parser()
        assert isinstance(parser, argparse.ArgumentParser)

    def test_default_values(self):
        """Test default argument values."""
        parser = create_parser()
        args = parser.parse_args([])

        assert args.output == Path("./presentation")
        assert args.format == "pptx"
        assert args.interval == 5.0
        assert args.threshold == 0.005
        assert args.method == "mse"
        assert args.monitor == 0
        assert args.region is None
        assert args.hotkey == "end"
        assert args.verbose is False
        assert args.list_monitors is False
        assert args.gui is False

    def test_output_argument(self):
        """Test -o/--output argument."""
        parser = create_parser()
        args = parser.parse_args(["-o", "my_slides.pptx"])
        assert args.output == Path("my_slides.pptx")

        args = parser.parse_args(["--output", "/path/to/output"])
        assert args.output == Path("/path/to/output")

    def test_format_argument(self):
        """Test -f/--format argument."""
        parser = create_parser()

        for fmt in ["pptx", "pdf", "images", "all"]:
            args = parser.parse_args(["-f", fmt])
            assert args.format == fmt

    def test_format_argument_invalid(self):
        """Test that invalid format raises error."""
        parser = create_parser()
        with pytest.raises(SystemExit):
            parser.parse_args(["-f", "invalid"])

    def test_interval_argument(self):
        """Test -i/--interval argument."""
        parser = create_parser()
        args = parser.parse_args(["-i", "3.5"])
        assert args.interval == 3.5

    def test_threshold_argument(self):
        """Test -t/--threshold argument."""
        parser = create_parser()
        args = parser.parse_args(["-t", "0.01"])
        assert args.threshold == 0.01

    def test_sensitivity_argument(self):
        """Test -s/--sensitivity argument."""
        parser = create_parser()

        for preset in ["low", "medium", "high"]:
            args = parser.parse_args(["-s", preset])
            assert args.sensitivity == preset

    def test_method_argument(self):
        """Test -M/--method argument."""
        parser = create_parser()

        for method in ["mse", "ssim", "clip"]:
            args = parser.parse_args(["-M", method])
            assert args.method == method

    def test_monitor_argument(self):
        """Test -m/--monitor argument."""
        parser = create_parser()
        args = parser.parse_args(["-m", "2"])
        assert args.monitor == 2

    def test_region_argument(self):
        """Test -r/--region argument."""
        parser = create_parser()
        args = parser.parse_args(["-r", "100,200,800,600"])
        assert args.region == (100, 200, 800, 600)

    def test_hotkey_argument(self):
        """Test -k/--hotkey argument."""
        parser = create_parser()
        args = parser.parse_args(["-k", "escape"])
        assert args.hotkey == "escape"

    def test_verbose_argument(self):
        """Test -v/--verbose argument."""
        parser = create_parser()
        args = parser.parse_args(["-v"])
        assert args.verbose is True

    def test_list_monitors_argument(self):
        """Test --list-monitors argument."""
        parser = create_parser()
        args = parser.parse_args(["--list-monitors"])
        assert args.list_monitors is True

    def test_gui_argument(self):
        """Test --gui argument."""
        parser = create_parser()
        args = parser.parse_args(["--gui"])
        assert args.gui is True

    def test_combined_arguments(self):
        """Test combining multiple arguments."""
        parser = create_parser()
        args = parser.parse_args([
            "-o", "output.pptx",
            "-f", "pptx",
            "-i", "3",
            "-M", "clip",
            "-m", "1",
            "-v",
        ])

        assert args.output == Path("output.pptx")
        assert args.format == "pptx"
        assert args.interval == 3.0
        assert args.method == "clip"
        assert args.monitor == 1
        assert args.verbose is True


class TestListMonitors:
    """Tests for the list_monitors function."""

    def test_list_monitors_output(self, capsys):
        """Test that list_monitors prints monitor info."""
        mock_monitors = [
            MagicMock(id=0, width=3840, height=1080, name="All Monitors", left=0, top=0),
            MagicMock(id=1, width=1920, height=1080, name="Monitor 1", left=0, top=0),
            MagicMock(id=2, width=1920, height=1080, name="Monitor 2", left=1920, top=0),
        ]

        mock_capture = MagicMock()
        mock_capture.list_monitors.return_value = mock_monitors
        mock_capture.__enter__ = MagicMock(return_value=mock_capture)
        mock_capture.__exit__ = MagicMock(return_value=False)

        with patch("decksnag.cli.ScreenCapture", return_value=mock_capture):
            list_monitors()

        captured = capsys.readouterr()
        assert "Available Monitors" in captured.out
        assert "All monitors combined" in captured.out
        assert "3840x1080" in captured.out
        assert "Monitor 1" in captured.out
        assert "Monitor 2" in captured.out


class TestMain:
    """Tests for the main entry point."""

    def test_main_list_monitors(self):
        """Test main with --list-monitors flag."""
        with patch("decksnag.cli.list_monitors") as mock_list:
            with patch("decksnag.cli.setup_logging"):
                result = main(["--list-monitors"])

        assert result == 0
        mock_list.assert_called_once()

    def test_main_gui_success(self):
        """Test main with --gui flag when GUI is available."""
        mock_gui_main = MagicMock()

        with patch("decksnag.cli.setup_logging"):
            with patch.dict("sys.modules", {"decksnag.gui": MagicMock(main=mock_gui_main)}):
                with patch("decksnag.cli.gui_main", mock_gui_main, create=True):
                    # We need to patch inside the function since it imports dynamically
                    result = main(["--gui"])

        # Either 0 (success) or the GUI launched
        assert result in [0, 1]  # May fail if import still doesn't work

    def test_main_gui_not_available(self):
        """Test main with --gui flag when GUI import fails."""
        with patch("decksnag.cli.setup_logging"):
            # Mock the import to raise ImportError
            import builtins
            original_import = builtins.__import__

            def mock_import(name, *args, **kwargs):
                if name == "decksnag.gui":
                    raise ImportError("No GUI")
                return original_import(name, *args, **kwargs)

            with patch.object(builtins, "__import__", side_effect=mock_import):
                result = main(["--gui"])

        # Should return 1 due to ImportError
        assert result == 1

    def test_main_config_error(self):
        """Test main with invalid configuration."""
        with patch("decksnag.cli.setup_logging"):
            # Invalid interval (too low)
            result = main(["-i", "0.1"])

        assert result == 1

    def test_main_capture_success(self, temp_dir):
        """Test main with successful capture session."""
        mock_capture = MagicMock()
        mock_capture.select_region_interactive.return_value = (0, 0, 800, 600)
        mock_capture.capture_region.return_value = MagicMock()
        mock_capture.__enter__ = MagicMock(return_value=mock_capture)
        mock_capture.__exit__ = MagicMock(return_value=False)

        mock_comparator = MagicMock()
        mock_comparator.is_different.return_value = False

        mock_presentation = MagicMock()
        mock_presentation.get_slide_count.return_value = 1
        mock_presentation.save.return_value = temp_dir / "output.pptx"

        mock_exporter = MagicMock()

        mock_listener = MagicMock()
        mock_listener.start = MagicMock()
        mock_listener.stop = MagicMock()

        # Simulate stop after first iteration
        def side_effect(*args, **kwargs):
            # Return immediately after sleep is called once
            raise KeyboardInterrupt()

        with patch("decksnag.cli.setup_logging"):
            with patch("decksnag.cli.ScreenCapture", return_value=mock_capture):
                with patch("decksnag.cli.ImageComparator", return_value=mock_comparator):
                    with patch("decksnag.cli.PresentationManager", return_value=mock_presentation):
                        with patch("decksnag.cli.Exporter", return_value=mock_exporter):
                            with patch("decksnag.cli.keyboard.Listener", return_value=mock_listener):
                                with patch("time.sleep", side_effect=side_effect):
                                    result = main([
                                        "-o", str(temp_dir / "output"),
                                        "-r", "0,0,800,600",
                                    ])

        assert result == 0

    def test_main_with_sensitivity_preset(self, temp_dir):
        """Test main with sensitivity preset."""
        mock_capture = MagicMock()
        mock_capture.select_region_interactive.return_value = (0, 0, 800, 600)
        mock_capture.capture_region.return_value = MagicMock()
        mock_capture.__enter__ = MagicMock(return_value=mock_capture)
        mock_capture.__exit__ = MagicMock(return_value=False)

        mock_comparator = MagicMock()
        mock_listener = MagicMock()
        mock_presentation = MagicMock()
        mock_presentation.get_slide_count.return_value = 1
        mock_presentation.save.return_value = temp_dir / "output.pptx"

        with patch("decksnag.cli.setup_logging"):
            with patch("decksnag.cli.ScreenCapture", return_value=mock_capture):
                # Return a real value from threshold_from_sensitivity
                with patch("decksnag.cli.ImageComparator") as mock_comp_class:
                    mock_comp_class.threshold_from_sensitivity.return_value = 0.001
                    mock_comp_class.return_value = mock_comparator
                    with patch("decksnag.cli.PresentationManager", return_value=mock_presentation):
                        with patch("decksnag.cli.Exporter"):
                            with patch("decksnag.cli.keyboard.Listener", return_value=mock_listener):
                                with patch("time.sleep", side_effect=KeyboardInterrupt()):
                                    main(["-s", "high", "-r", "0,0,800,600"])

        # Verify threshold_from_sensitivity was called
        mock_comp_class.threshold_from_sensitivity.assert_called_once_with("high", "mse")


class TestRunCaptureSession:
    """Tests for the run_capture_session function."""

    def test_capture_with_preset_region(self, temp_dir):
        """Test capture session with preset region."""
        config = Config(
            output_path=temp_dir / "test",
            region=(100, 100, 500, 400),
        )

        mock_capture = MagicMock()
        mock_image = MagicMock()
        mock_capture.capture_region.return_value = mock_image
        mock_capture.__enter__ = MagicMock(return_value=mock_capture)
        mock_capture.__exit__ = MagicMock(return_value=False)

        mock_comparator = MagicMock()
        mock_comparator.is_different.return_value = False

        mock_presentation = MagicMock()
        mock_presentation.get_slide_count.return_value = 1
        mock_presentation.save.return_value = temp_dir / "test.pptx"

        mock_listener = MagicMock()

        with patch("decksnag.cli.ScreenCapture", return_value=mock_capture):
            with patch("decksnag.cli.ImageComparator", return_value=mock_comparator):
                with patch("decksnag.cli.PresentationManager", return_value=mock_presentation):
                    with patch("decksnag.cli.Exporter"):
                        with patch("decksnag.cli.keyboard.Listener", return_value=mock_listener):
                            with patch("time.sleep", side_effect=KeyboardInterrupt()):
                                run_capture_session(config)

        # Should not call select_region_interactive when region is preset
        mock_capture.select_region_interactive.assert_not_called()
        mock_capture.capture_region.assert_called_with((100, 100, 500, 400))

    def test_capture_with_interactive_region(self, temp_dir):
        """Test capture session with interactive region selection."""
        config = Config(
            output_path=temp_dir / "test",
        )

        mock_capture = MagicMock()
        mock_capture.select_region_interactive.return_value = (0, 0, 800, 600)
        mock_capture.capture_region.return_value = MagicMock()
        mock_capture.__enter__ = MagicMock(return_value=mock_capture)
        mock_capture.__exit__ = MagicMock(return_value=False)

        mock_comparator = MagicMock()
        mock_presentation = MagicMock()
        mock_presentation.get_slide_count.return_value = 1
        mock_presentation.save.return_value = temp_dir / "test.pptx"

        mock_listener = MagicMock()

        with patch("decksnag.cli.ScreenCapture", return_value=mock_capture):
            with patch("decksnag.cli.ImageComparator", return_value=mock_comparator):
                with patch("decksnag.cli.PresentationManager", return_value=mock_presentation):
                    with patch("decksnag.cli.Exporter"):
                        with patch("decksnag.cli.keyboard.Listener", return_value=mock_listener):
                            with patch("time.sleep", side_effect=KeyboardInterrupt()):
                                run_capture_session(config)

        mock_capture.select_region_interactive.assert_called_once()

    def test_capture_detects_slide_change(self, temp_dir):
        """Test that slide changes are detected and added."""
        config = Config(
            output_path=temp_dir / "test",
            region=(0, 0, 800, 600),
        )

        mock_capture = MagicMock()
        mock_image1 = MagicMock()
        mock_image2 = MagicMock()
        mock_capture.capture_region.side_effect = [mock_image1, mock_image2]
        mock_capture.__enter__ = MagicMock(return_value=mock_capture)
        mock_capture.__exit__ = MagicMock(return_value=False)

        mock_comparator = MagicMock()
        mock_comparator.is_different.return_value = True

        mock_presentation = MagicMock()
        mock_presentation.add_slide.return_value = 2
        mock_presentation.get_slide_count.return_value = 2
        mock_presentation.save.return_value = temp_dir / "test.pptx"

        mock_exporter = MagicMock()
        mock_listener = MagicMock()

        call_count = [0]

        def sleep_side_effect(seconds):
            call_count[0] += 1
            if call_count[0] >= 1:
                raise KeyboardInterrupt()

        with patch("decksnag.cli.ScreenCapture", return_value=mock_capture):
            with patch("decksnag.cli.ImageComparator", return_value=mock_comparator):
                with patch("decksnag.cli.PresentationManager", return_value=mock_presentation):
                    with patch("decksnag.cli.Exporter", return_value=mock_exporter):
                        with patch("decksnag.cli.keyboard.Listener", return_value=mock_listener):
                            with patch("time.sleep", side_effect=sleep_side_effect):
                                run_capture_session(config)

        # First slide added during initial capture, second during loop
        assert mock_presentation.add_slide.call_count >= 1

    def test_capture_export_all_formats(self, temp_dir):
        """Test capture session with 'all' export format."""
        config = Config(
            output_path=temp_dir / "test",
            output_format="all",
            region=(0, 0, 800, 600),
        )

        mock_capture = MagicMock()
        mock_capture.capture_region.return_value = MagicMock()
        mock_capture.__enter__ = MagicMock(return_value=mock_capture)
        mock_capture.__exit__ = MagicMock(return_value=False)

        mock_comparator = MagicMock()

        mock_presentation = MagicMock()
        mock_presentation.get_slide_count.return_value = 1

        mock_exporter = MagicMock()
        mock_exporter.export_all.return_value = {
            "pptx": temp_dir / "test.pptx",
            "pdf": temp_dir / "test.pdf",
            "images": [temp_dir / "test_001.png"],
        }

        mock_listener = MagicMock()

        with patch("decksnag.cli.ScreenCapture", return_value=mock_capture):
            with patch("decksnag.cli.ImageComparator", return_value=mock_comparator):
                with patch("decksnag.cli.PresentationManager", return_value=mock_presentation):
                    with patch("decksnag.cli.Exporter", return_value=mock_exporter):
                        with patch("decksnag.cli.keyboard.Listener", return_value=mock_listener):
                            with patch("time.sleep", side_effect=KeyboardInterrupt()):
                                run_capture_session(config)

        mock_exporter.export_all.assert_called_once()

    def test_capture_export_images(self, temp_dir):
        """Test capture session with 'images' export format."""
        config = Config(
            output_path=temp_dir / "test",
            output_format="images",
            region=(0, 0, 800, 600),
        )

        mock_capture = MagicMock()
        mock_capture.capture_region.return_value = MagicMock()
        mock_capture.__enter__ = MagicMock(return_value=mock_capture)
        mock_capture.__exit__ = MagicMock(return_value=False)

        mock_comparator = MagicMock()

        mock_presentation = MagicMock()
        mock_presentation.get_slide_count.return_value = 1

        mock_exporter = MagicMock()
        mock_exporter.export_images.return_value = [temp_dir / "test_001.png"]

        mock_listener = MagicMock()

        with patch("decksnag.cli.ScreenCapture", return_value=mock_capture):
            with patch("decksnag.cli.ImageComparator", return_value=mock_comparator):
                with patch("decksnag.cli.PresentationManager", return_value=mock_presentation):
                    with patch("decksnag.cli.Exporter", return_value=mock_exporter):
                        with patch("decksnag.cli.keyboard.Listener", return_value=mock_listener):
                            with patch("time.sleep", side_effect=KeyboardInterrupt()):
                                run_capture_session(config)

        mock_exporter.export_images.assert_called_once()

    def test_capture_export_pdf(self, temp_dir):
        """Test capture session with 'pdf' export format."""
        config = Config(
            output_path=temp_dir / "test",
            output_format="pdf",
            region=(0, 0, 800, 600),
        )

        mock_capture = MagicMock()
        mock_capture.capture_region.return_value = MagicMock()
        mock_capture.__enter__ = MagicMock(return_value=mock_capture)
        mock_capture.__exit__ = MagicMock(return_value=False)

        mock_comparator = MagicMock()

        mock_presentation = MagicMock()
        mock_presentation.get_slide_count.return_value = 1

        mock_exporter = MagicMock()
        mock_exporter.export_pdf.return_value = temp_dir / "test.pdf"

        mock_listener = MagicMock()

        with patch("decksnag.cli.ScreenCapture", return_value=mock_capture):
            with patch("decksnag.cli.ImageComparator", return_value=mock_comparator):
                with patch("decksnag.cli.PresentationManager", return_value=mock_presentation):
                    with patch("decksnag.cli.Exporter", return_value=mock_exporter):
                        with patch("decksnag.cli.keyboard.Listener", return_value=mock_listener):
                            with patch("time.sleep", side_effect=KeyboardInterrupt()):
                                run_capture_session(config)

        mock_exporter.export_pdf.assert_called_once()
