"""Tests for presentation module."""

import pytest
from pathlib import Path
from video_to_powerpoint.presentation import PresentationManager


class TestPresentationManager:
    """Tests for the PresentationManager class."""

    def test_create_presentation(self, temp_dir):
        """Test creating a new presentation."""
        manager = PresentationManager()
        manager.create(temp_dir / "test.pptx")

        assert manager.get_slide_count() == 0
        assert not manager.has_slides

    def test_add_slide(self, temp_dir, sample_image):
        """Test adding a slide."""
        manager = PresentationManager()
        manager.create(temp_dir / "test.pptx")

        slide_num = manager.add_slide(sample_image)

        assert slide_num == 1
        assert manager.get_slide_count() == 1
        assert manager.has_slides

    def test_add_multiple_slides(self, temp_dir, sample_image):
        """Test adding multiple slides."""
        manager = PresentationManager()
        manager.create(temp_dir / "test.pptx")

        for i in range(5):
            slide_num = manager.add_slide(sample_image)
            assert slide_num == i + 1

        assert manager.get_slide_count() == 5

    def test_add_slide_without_create_raises(self, sample_image):
        """Test that adding slide without create raises error."""
        manager = PresentationManager()

        with pytest.raises(RuntimeError, match="No presentation created"):
            manager.add_slide(sample_image)

    def test_save_presentation(self, temp_dir, sample_image):
        """Test saving a presentation."""
        manager = PresentationManager()
        output_path = temp_dir / "test.pptx"
        manager.create(output_path)
        manager.add_slide(sample_image)

        saved_path = manager.save()

        assert saved_path.exists()
        assert saved_path.suffix == ".pptx"

    def test_save_adds_extension(self, temp_dir, sample_image):
        """Test that save adds .pptx extension if missing."""
        manager = PresentationManager()
        output_path = temp_dir / "test"  # No extension
        manager.create(output_path)
        manager.add_slide(sample_image)

        saved_path = manager.save()

        assert saved_path.suffix == ".pptx"

    def test_save_without_path_raises(self, sample_image):
        """Test that saving without path raises error."""
        manager = PresentationManager()
        manager.create()  # No path specified
        manager.add_slide(sample_image)

        with pytest.raises(RuntimeError, match="No output path"):
            manager.save()

    def test_save_without_create_raises(self):
        """Test that saving without create raises error."""
        manager = PresentationManager()

        with pytest.raises(RuntimeError, match="No presentation to save"):
            manager.save()

    def test_get_slides(self, temp_dir, sample_image, sample_image_modified):
        """Test getting all slides."""
        manager = PresentationManager()
        manager.create(temp_dir / "test.pptx")
        manager.add_slide(sample_image)
        manager.add_slide(sample_image_modified)

        slides = manager.get_slides()

        assert len(slides) == 2
        # Verify they are copies
        slides[0].putpixel((0, 0), (0, 0, 0))  # Modify copy
        original_slides = manager.get_slides()
        assert original_slides[0].getpixel((0, 0)) != (0, 0, 0)

    def test_get_slide_by_index(self, temp_dir, sample_image):
        """Test getting a slide by index."""
        manager = PresentationManager()
        manager.create(temp_dir / "test.pptx")
        manager.add_slide(sample_image)

        slide = manager.get_slide(0)
        assert slide is not None
        assert slide.size == sample_image.size

    def test_get_slide_invalid_index(self, temp_dir, sample_image):
        """Test that invalid index returns None."""
        manager = PresentationManager()
        manager.create(temp_dir / "test.pptx")
        manager.add_slide(sample_image)

        assert manager.get_slide(5) is None
        assert manager.get_slide(-1) is None

    def test_get_last_slide(self, temp_dir, sample_image, sample_image_modified):
        """Test getting the last slide."""
        manager = PresentationManager()
        manager.create(temp_dir / "test.pptx")
        manager.add_slide(sample_image)
        manager.add_slide(sample_image_modified)

        last = manager.get_last_slide()
        assert last is not None
        # Check it's the blue one (sample_image_modified)
        assert last.getpixel((100, 100)) == sample_image_modified.getpixel((100, 100))

    def test_get_last_slide_empty(self, temp_dir):
        """Test getting last slide when empty returns None."""
        manager = PresentationManager()
        manager.create(temp_dir / "test.pptx")

        assert manager.get_last_slide() is None

    def test_close(self, temp_dir, sample_image):
        """Test closing the presentation."""
        manager = PresentationManager()
        manager.create(temp_dir / "test.pptx")
        manager.add_slide(sample_image)

        manager.close()

        assert manager.get_slide_count() == 0
        assert not manager.has_slides
