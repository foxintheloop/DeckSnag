"""Image comparison functionality for detecting slide changes."""

import logging
from typing import Tuple
import numpy as np
from PIL import Image
from skimage.metrics import mean_squared_error, structural_similarity

logger = logging.getLogger("video_to_powerpoint")


class ImageComparator:
    """Compare images to detect significant changes between slides."""

    def __init__(self, threshold: float = 0.005) -> None:
        """Initialize the comparator.

        Args:
            threshold: MSE threshold for detecting changes.
                      Lower values = more sensitive to changes.
                      Default 0.005 is a good balance.
        """
        if not 0 < threshold < 1:
            raise ValueError("Threshold must be between 0 and 1")
        self.threshold = threshold

    def _to_grayscale_array(self, image: Image.Image) -> np.ndarray:
        """Convert PIL Image to grayscale numpy array normalized to 0-1.

        Args:
            image: PIL Image to convert.

        Returns:
            Grayscale numpy array with values in [0, 1].
        """
        # Convert to grayscale
        gray = image.convert("L")
        # Convert to numpy array and normalize to 0-1
        return np.array(gray, dtype=np.float64) / 255.0

    def _resize_to_match(
        self, img1: Image.Image, img2: Image.Image
    ) -> Tuple[Image.Image, Image.Image]:
        """Resize images to match dimensions if needed.

        Args:
            img1: First image.
            img2: Second image.

        Returns:
            Tuple of (img1, img2) with matching dimensions.
        """
        if img1.size == img2.size:
            return img1, img2

        # Use the smaller dimensions
        width = min(img1.width, img2.width)
        height = min(img1.height, img2.height)

        logger.debug(
            f"Resizing images to match: {img1.size} and {img2.size} -> ({width}, {height})"
        )

        img1_resized = img1.resize((width, height), Image.Resampling.LANCZOS)
        img2_resized = img2.resize((width, height), Image.Resampling.LANCZOS)

        return img1_resized, img2_resized

    def compute_mse(self, img1: Image.Image, img2: Image.Image) -> float:
        """Compute Mean Squared Error between two images.

        Args:
            img1: First image.
            img2: Second image.

        Returns:
            MSE value (0 = identical, higher = more different).
        """
        # Resize if needed
        img1, img2 = self._resize_to_match(img1, img2)

        # Convert to grayscale arrays
        arr1 = self._to_grayscale_array(img1)
        arr2 = self._to_grayscale_array(img2)

        # Compute MSE
        mse = mean_squared_error(arr1, arr2)

        logger.debug(f"MSE: {mse:.6f} (threshold: {self.threshold})")
        return float(mse)

    def compute_ssim(self, img1: Image.Image, img2: Image.Image) -> float:
        """Compute Structural Similarity Index between two images.

        SSIM is often better at detecting perceptual differences than MSE.

        Args:
            img1: First image.
            img2: Second image.

        Returns:
            SSIM value (1 = identical, lower = more different).
        """
        # Resize if needed
        img1, img2 = self._resize_to_match(img1, img2)

        # Convert to grayscale arrays
        arr1 = self._to_grayscale_array(img1)
        arr2 = self._to_grayscale_array(img2)

        # Compute SSIM
        # data_range is 1.0 since we normalized to 0-1
        ssim = structural_similarity(arr1, arr2, data_range=1.0)

        logger.debug(f"SSIM: {ssim:.6f}")
        return float(ssim)

    def is_different(self, img1: Image.Image, img2: Image.Image) -> bool:
        """Check if two images are significantly different.

        Args:
            img1: First image (e.g., previous screenshot).
            img2: Second image (e.g., current screenshot).

        Returns:
            True if images are different enough to be considered
            a new slide, False otherwise.
        """
        mse = self.compute_mse(img1, img2)
        is_diff = mse > self.threshold

        if is_diff:
            logger.info(f"Change detected (MSE: {mse:.6f} > {self.threshold})")
        else:
            logger.debug(f"No significant change (MSE: {mse:.6f} <= {self.threshold})")

        return is_diff

    def set_threshold(self, threshold: float) -> None:
        """Update the comparison threshold.

        Args:
            threshold: New threshold value (0 < threshold < 1).
        """
        if not 0 < threshold < 1:
            raise ValueError("Threshold must be between 0 and 1")
        self.threshold = threshold
        logger.debug(f"Threshold updated to: {threshold}")

    @staticmethod
    def threshold_from_sensitivity(sensitivity: str) -> float:
        """Convert a sensitivity preset to a threshold value.

        Args:
            sensitivity: One of 'low', 'medium', 'high'.

        Returns:
            Corresponding threshold value.
        """
        presets = {
            "low": 0.01,      # Less sensitive
            "medium": 0.005,  # Default
            "high": 0.001,    # More sensitive
        }

        if sensitivity not in presets:
            raise ValueError(
                f"Unknown sensitivity: {sensitivity}. "
                f"Use one of: {list(presets.keys())}"
            )

        return presets[sensitivity]
