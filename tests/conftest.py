"""Pytest configuration and fixtures."""

import pytest
from pathlib import Path
from PIL import Image
import tempfile
import shutil


@pytest.fixture
def temp_dir():
    """Create a temporary directory for test outputs."""
    tmp = tempfile.mkdtemp()
    yield Path(tmp)
    shutil.rmtree(tmp, ignore_errors=True)


@pytest.fixture
def sample_image():
    """Create a simple test image."""
    img = Image.new("RGB", (800, 600), color="white")
    return img


@pytest.fixture
def sample_image_modified():
    """Create a modified test image (different from sample_image)."""
    img = Image.new("RGB", (800, 600), color="blue")
    return img


@pytest.fixture
def sample_image_similar():
    """Create an image very similar to sample_image (minor changes)."""
    img = Image.new("RGB", (800, 600), color="white")
    # Make a tiny change
    img.putpixel((0, 0), (254, 255, 255))
    return img
