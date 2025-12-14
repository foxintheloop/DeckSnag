"""Tests for image comparison module."""

import pytest
from PIL import Image
from video_to_powerpoint.comparison import ImageComparator


class TestImageComparator:
    """Tests for the ImageComparator class."""

    def test_init_default_threshold(self):
        """Test default threshold initialization."""
        comparator = ImageComparator()
        assert comparator.threshold == 0.005

    def test_init_custom_threshold(self):
        """Test custom threshold initialization."""
        comparator = ImageComparator(threshold=0.01)
        assert comparator.threshold == 0.01

    def test_init_invalid_threshold(self):
        """Test that invalid threshold raises error."""
        with pytest.raises(ValueError):
            ImageComparator(threshold=0)

        with pytest.raises(ValueError):
            ImageComparator(threshold=1)

    def test_identical_images(self, sample_image):
        """Test that identical images have MSE of 0."""
        comparator = ImageComparator()
        mse = comparator.compute_mse(sample_image, sample_image)
        assert mse == 0.0

    def test_identical_images_not_different(self, sample_image):
        """Test that identical images are not marked as different."""
        comparator = ImageComparator()
        assert not comparator.is_different(sample_image, sample_image)

    def test_different_images(self, sample_image, sample_image_modified):
        """Test that different images have high MSE."""
        comparator = ImageComparator()
        mse = comparator.compute_mse(sample_image, sample_image_modified)
        assert mse > 0.1  # White vs blue should be very different

    def test_different_images_marked_different(self, sample_image, sample_image_modified):
        """Test that different images are marked as different."""
        comparator = ImageComparator()
        assert comparator.is_different(sample_image, sample_image_modified)

    def test_similar_images_low_sensitivity(self, sample_image, sample_image_similar):
        """Test that similar images are not different with low sensitivity."""
        comparator = ImageComparator(threshold=0.01)  # Low sensitivity
        assert not comparator.is_different(sample_image, sample_image_similar)

    def test_ssim_identical(self, sample_image):
        """Test SSIM is 1.0 for identical images."""
        comparator = ImageComparator()
        ssim = comparator.compute_ssim(sample_image, sample_image)
        assert ssim == pytest.approx(1.0, abs=0.001)

    def test_ssim_different(self, sample_image, sample_image_modified):
        """Test SSIM is low for different images."""
        comparator = ImageComparator()
        ssim = comparator.compute_ssim(sample_image, sample_image_modified)
        assert ssim < 0.5

    def test_set_threshold(self):
        """Test updating threshold."""
        comparator = ImageComparator(threshold=0.005)
        comparator.set_threshold(0.01)
        assert comparator.threshold == 0.01

    def test_set_threshold_invalid(self):
        """Test that setting invalid threshold raises error."""
        comparator = ImageComparator()
        with pytest.raises(ValueError):
            comparator.set_threshold(0)

    def test_threshold_from_sensitivity(self):
        """Test converting sensitivity presets to thresholds."""
        assert ImageComparator.threshold_from_sensitivity("low") == 0.01
        assert ImageComparator.threshold_from_sensitivity("medium") == 0.005
        assert ImageComparator.threshold_from_sensitivity("high") == 0.001

    def test_threshold_from_sensitivity_invalid(self):
        """Test that invalid sensitivity raises error."""
        with pytest.raises(ValueError, match="Unknown sensitivity"):
            ImageComparator.threshold_from_sensitivity("invalid")

    def test_different_size_images(self):
        """Test comparison of different size images."""
        img1 = Image.new("RGB", (800, 600), color="white")
        img2 = Image.new("RGB", (1024, 768), color="white")

        comparator = ImageComparator()
        # Should not raise error - images are resized internally
        mse = comparator.compute_mse(img1, img2)
        assert mse == pytest.approx(0.0, abs=0.001)

    def test_grayscale_image(self):
        """Test comparison works with grayscale images."""
        img1 = Image.new("L", (800, 600), color=255)  # White
        img2 = Image.new("L", (800, 600), color=0)    # Black

        comparator = ImageComparator()
        mse = comparator.compute_mse(img1, img2)
        assert mse > 0.9  # Should be nearly 1.0 (max difference)
