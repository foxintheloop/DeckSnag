"""Tests for configuration module."""

import pytest
from pathlib import Path
from video_to_powerpoint.config import Config


class TestConfig:
    """Tests for the Config class."""

    def test_default_values(self):
        """Test that default values are set correctly."""
        config = Config()

        assert config.output_format == "pptx"
        assert config.interval == 5.0
        assert config.threshold == 0.005
        assert config.stop_hotkey == "end"
        assert config.monitor == 0
        assert config.region is None
        assert config.verbose is False

    def test_custom_values(self, temp_dir):
        """Test configuration with custom values."""
        config = Config(
            output_path=temp_dir / "test",
            output_format="pdf",
            interval=3.0,
            threshold=0.01,
            stop_hotkey="escape",
            monitor=1,
            region=(100, 100, 800, 600),
            verbose=True,
        )

        assert config.output_path == temp_dir / "test"
        assert config.output_format == "pdf"
        assert config.interval == 3.0
        assert config.threshold == 0.01
        assert config.stop_hotkey == "escape"
        assert config.monitor == 1
        assert config.region == (100, 100, 800, 600)
        assert config.verbose is True

    def test_string_path_conversion(self):
        """Test that string paths are converted to Path objects."""
        config = Config(output_path="./output/test")
        assert isinstance(config.output_path, Path)

    def test_interval_validation_too_low(self):
        """Test that interval below 0.5 raises error."""
        with pytest.raises(ValueError, match="at least 0.5"):
            Config(interval=0.1)

    def test_interval_validation_too_high(self):
        """Test that interval above 60 raises error."""
        with pytest.raises(ValueError, match="at most 60"):
            Config(interval=120)

    def test_threshold_validation(self):
        """Test that invalid threshold raises error."""
        with pytest.raises(ValueError, match="between 0 and 1"):
            Config(threshold=0)

        with pytest.raises(ValueError, match="between 0 and 1"):
            Config(threshold=1)

        with pytest.raises(ValueError, match="between 0 and 1"):
            Config(threshold=-0.1)

    def test_monitor_validation(self):
        """Test that negative monitor raises error."""
        with pytest.raises(ValueError, match="non-negative"):
            Config(monitor=-1)

    def test_region_validation_wrong_length(self):
        """Test that region with wrong length raises error."""
        with pytest.raises(ValueError, match="4 integers"):
            Config(region=(100, 100, 800))

    def test_region_validation_invalid_bounds(self):
        """Test that invalid region bounds raise error."""
        with pytest.raises(ValueError, match="x2 must be > x1"):
            Config(region=(800, 100, 100, 600))

    def test_sensitivity_preset(self):
        """Test creating config from sensitivity preset."""
        config_low = Config.from_sensitivity_preset("low")
        config_medium = Config.from_sensitivity_preset("medium")
        config_high = Config.from_sensitivity_preset("high")

        assert config_low.threshold == 0.01
        assert config_medium.threshold == 0.005
        assert config_high.threshold == 0.001

    def test_sensitivity_preset_invalid(self):
        """Test that invalid preset raises error."""
        with pytest.raises(ValueError, match="Unknown preset"):
            Config.from_sensitivity_preset("invalid")

    def test_output_path_with_extension_pptx(self, temp_dir):
        """Test getting output path with pptx extension."""
        config = Config(output_path=temp_dir / "test", output_format="pptx")
        path = config.get_output_path_with_extension()
        assert path.suffix == ".pptx"

    def test_output_path_with_extension_pdf(self, temp_dir):
        """Test getting output path with pdf extension."""
        config = Config(output_path=temp_dir / "test", output_format="pdf")
        path = config.get_output_path_with_extension()
        assert path.suffix == ".pdf"

    def test_output_path_with_extension_images(self, temp_dir):
        """Test that images format returns directory path."""
        config = Config(output_path=temp_dir / "slides", output_format="images")
        path = config.get_output_path_with_extension()
        # Images format should return the directory path without extension
        assert path == temp_dir / "slides"
