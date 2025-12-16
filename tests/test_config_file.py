"""Tests for configuration file module."""

import os
import pytest
from pathlib import Path
from unittest.mock import patch

from decksnag.config_file import (
    get_user_config_dir,
    get_user_data_dir,
    get_default_config_path,
    ensure_config_dir,
    ensure_data_dir,
    load_config_file,
    save_config_file,
    load_env_config,
    merge_configs,
    config_dict_to_config,
    create_default_config_file,
)


class TestGetUserConfigDir:
    """Tests for get_user_config_dir function."""

    def test_windows_config_dir(self):
        """Test config dir on Windows."""
        with patch("os.name", "nt"):
            with patch.dict(os.environ, {"APPDATA": "C:\\Users\\Test\\AppData\\Roaming"}):
                result = get_user_config_dir()
                assert result == Path("C:\\Users\\Test\\AppData\\Roaming\\DeckSnag")

    def test_linux_config_dir(self):
        """Test config dir logic on Linux-like systems."""
        # Just verify the function handles posix case without actual Path creation
        # Can't fully test on Windows due to PosixPath instantiation issues
        if os.name == "nt":
            pytest.skip("Cannot test Linux paths on Windows")

        result = get_user_config_dir()
        assert "decksnag" in str(result).lower()


class TestGetUserDataDir:
    """Tests for get_user_data_dir function."""

    def test_windows_data_dir(self):
        """Test data dir on Windows."""
        with patch("os.name", "nt"):
            with patch.dict(os.environ, {"LOCALAPPDATA": "C:\\Users\\Test\\AppData\\Local"}):
                result = get_user_data_dir()
                assert result == Path("C:\\Users\\Test\\AppData\\Local\\DeckSnag")


class TestLoadConfigFile:
    """Tests for load_config_file function."""

    def test_load_nonexistent_file(self):
        """Test loading from nonexistent file returns empty dict."""
        result = load_config_file(Path("/nonexistent/config.toml"))
        assert result == {}

    def test_load_valid_config(self, temp_dir):
        """Test loading valid TOML config."""
        config_path = temp_dir / "config.toml"
        config_path.write_text('''
output_path = "./slides"
interval = 3.0
threshold = 0.01
method = "ssim"
verbose = true
''')

        result = load_config_file(config_path)

        assert result["output_path"] == "./slides"
        assert result["interval"] == 3.0
        assert result["threshold"] == 0.01
        assert result["method"] == "ssim"
        assert result["verbose"] is True

    def test_load_invalid_toml(self, temp_dir):
        """Test loading invalid TOML returns empty dict."""
        config_path = temp_dir / "config.toml"
        config_path.write_text("invalid toml [[[")

        result = load_config_file(config_path)
        assert result == {}


class TestSaveConfigFile:
    """Tests for save_config_file function."""

    def test_save_basic_config(self, temp_dir):
        """Test saving basic configuration."""
        config = {
            "output_path": "./presentation",
            "interval": 5.0,
            "threshold": 0.005,
            "verbose": False,
        }

        path = save_config_file(config, temp_dir / "config.toml")

        assert path.exists()
        content = path.read_text()
        assert "output_path" in content
        assert "interval" in content

    def test_save_and_load_roundtrip(self, temp_dir):
        """Test that saved config can be loaded back."""
        original = {
            "output_path": "./test",
            "interval": 3.5,
            "method": "clip",
            "verbose": True,
        }

        path = save_config_file(original, temp_dir / "config.toml")
        loaded = load_config_file(path)

        assert loaded["output_path"] == original["output_path"]
        assert loaded["interval"] == original["interval"]
        assert loaded["method"] == original["method"]
        assert loaded["verbose"] == original["verbose"]

    def test_save_with_region_tuple(self, temp_dir):
        """Test saving config with region tuple."""
        config = {
            "region": (100, 200, 800, 600),
        }

        path = save_config_file(config, temp_dir / "config.toml")
        content = path.read_text()
        assert "region = [100, 200, 800, 600]" in content

    def test_save_skips_none_values(self, temp_dir):
        """Test that None values are not saved."""
        config = {
            "output_path": "./test",
            "region": None,
        }

        path = save_config_file(config, temp_dir / "config.toml")
        content = path.read_text()
        assert "region" not in content


class TestLoadEnvConfig:
    """Tests for load_env_config function."""

    def test_load_string_env_vars(self):
        """Test loading string environment variables."""
        with patch.dict(os.environ, {
            "DECKSNAG_OUTPUT_PATH": "./env_output",
            "DECKSNAG_METHOD": "ssim",
        }):
            result = load_env_config()

        assert result["output_path"] == "./env_output"
        assert result["method"] == "ssim"

    def test_load_numeric_env_vars(self):
        """Test loading numeric environment variables."""
        with patch.dict(os.environ, {
            "DECKSNAG_INTERVAL": "3.5",
            "DECKSNAG_THRESHOLD": "0.01",
            "DECKSNAG_MONITOR": "2",
        }):
            result = load_env_config()

        assert result["interval"] == 3.5
        assert result["threshold"] == 0.01
        assert result["monitor"] == 2

    def test_load_boolean_env_vars(self):
        """Test loading boolean environment variables."""
        with patch.dict(os.environ, {"DECKSNAG_VERBOSE": "true"}):
            result = load_env_config()
            assert result["verbose"] is True

        with patch.dict(os.environ, {"DECKSNAG_VERBOSE": "false"}):
            result = load_env_config()
            assert result["verbose"] is False

        with patch.dict(os.environ, {"DECKSNAG_VERBOSE": "1"}):
            result = load_env_config()
            assert result["verbose"] is True

    def test_load_region_env_var(self):
        """Test loading region environment variable."""
        with patch.dict(os.environ, {"DECKSNAG_REGION": "100,200,800,600"}):
            result = load_env_config()

        assert result["region"] == (100, 200, 800, 600)

    def test_invalid_region_env_var(self):
        """Test invalid region format is handled."""
        with patch.dict(os.environ, {"DECKSNAG_REGION": "100,200"}):
            result = load_env_config()

        assert "region" not in result

    def test_invalid_numeric_env_var(self):
        """Test invalid numeric values are handled."""
        with patch.dict(os.environ, {"DECKSNAG_INTERVAL": "not_a_number"}):
            result = load_env_config()

        assert "interval" not in result

    def test_empty_env(self):
        """Test loading with no environment variables set."""
        with patch.dict(os.environ, {}, clear=True):
            result = load_env_config()
        # Result should be empty or only contain values from actual env
        assert isinstance(result, dict)


class TestMergeConfigs:
    """Tests for merge_configs function."""

    def test_merge_empty_configs(self):
        """Test merging empty configs."""
        result = merge_configs({}, {})
        assert result == {}

    def test_merge_single_config(self):
        """Test merging single config."""
        config = {"interval": 5.0, "method": "mse"}
        result = merge_configs(config)
        assert result == config

    def test_merge_multiple_configs(self):
        """Test that later configs override earlier ones."""
        config1 = {"interval": 5.0, "method": "mse"}
        config2 = {"interval": 3.0, "threshold": 0.01}
        config3 = {"method": "ssim"}

        result = merge_configs(config1, config2, config3)

        assert result["interval"] == 3.0  # From config2
        assert result["method"] == "ssim"  # From config3
        assert result["threshold"] == 0.01  # From config2

    def test_merge_skips_none_values(self):
        """Test that None values don't override."""
        config1 = {"interval": 5.0}
        config2 = {"interval": None}

        result = merge_configs(config1, config2)

        assert result["interval"] == 5.0


class TestConfigDictToConfig:
    """Tests for config_dict_to_config function."""

    def test_converts_string_path(self):
        """Test that string paths are converted to Path objects."""
        config = {"output_path": "./test/output"}
        result = config_dict_to_config(config)

        assert isinstance(result["output_path"], Path)
        assert result["output_path"] == Path("./test/output")

    def test_converts_region_list(self):
        """Test that region list is converted to tuple."""
        config = {"region": [100, 200, 800, 600]}
        result = config_dict_to_config(config)

        assert isinstance(result["region"], tuple)
        assert result["region"] == (100, 200, 800, 600)

    def test_preserves_other_values(self):
        """Test that other values are preserved unchanged."""
        config = {
            "interval": 5.0,
            "method": "mse",
            "verbose": True,
        }
        result = config_dict_to_config(config)

        assert result["interval"] == 5.0
        assert result["method"] == "mse"
        assert result["verbose"] is True


class TestEnsureDirectories:
    """Tests for ensure_config_dir and ensure_data_dir functions."""

    def test_ensure_config_dir_creates(self, temp_dir):
        """Test that ensure_config_dir creates directory."""
        with patch("decksnag.config_file.get_user_config_dir", return_value=temp_dir / "config"):
            result = ensure_config_dir()
            assert result.exists()

    def test_ensure_data_dir_creates(self, temp_dir):
        """Test that ensure_data_dir creates directory."""
        with patch("decksnag.config_file.get_user_data_dir", return_value=temp_dir / "data"):
            result = ensure_data_dir()
            assert result.exists()


class TestCreateDefaultConfigFile:
    """Tests for create_default_config_file function."""

    def test_creates_config_file(self, temp_dir):
        """Test that default config file is created."""
        with patch("decksnag.config_file.get_user_config_dir", return_value=temp_dir):
            with patch("decksnag.config_file.get_default_config_path", return_value=temp_dir / "config.toml"):
                path = create_default_config_file()

        assert path.exists()
        content = path.read_text()
        assert "DeckSnag Configuration" in content
        assert "output_path" in content
        assert "interval" in content
