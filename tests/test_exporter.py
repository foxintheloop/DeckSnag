"""Tests for exporter module."""

import pytest
from pathlib import Path
from video_to_powerpoint.exporter import Exporter


class TestExporter:
    """Tests for the Exporter class."""

    def test_init_empty(self):
        """Test initializing without slides."""
        exporter = Exporter()
        assert exporter.get_slide_count() == 0

    def test_init_with_slides(self, sample_image):
        """Test initializing with slides."""
        exporter = Exporter(slides=[sample_image, sample_image])
        assert exporter.get_slide_count() == 2

    def test_set_slides(self, sample_image):
        """Test setting slides."""
        exporter = Exporter()
        exporter.set_slides([sample_image, sample_image, sample_image])
        assert exporter.get_slide_count() == 3

    def test_add_slide(self, sample_image):
        """Test adding individual slides."""
        exporter = Exporter()
        exporter.add_slide(sample_image)
        exporter.add_slide(sample_image)
        assert exporter.get_slide_count() == 2

    def test_clear(self, sample_image):
        """Test clearing slides."""
        exporter = Exporter(slides=[sample_image])
        exporter.clear()
        assert exporter.get_slide_count() == 0

    def test_export_pptx(self, temp_dir, sample_image):
        """Test exporting to PowerPoint."""
        exporter = Exporter(slides=[sample_image, sample_image])
        output_path = temp_dir / "test.pptx"

        saved_path = exporter.export_pptx(output_path)

        assert saved_path.exists()
        assert saved_path.suffix == ".pptx"

    def test_export_pptx_adds_extension(self, temp_dir, sample_image):
        """Test that export adds .pptx extension."""
        exporter = Exporter(slides=[sample_image])
        output_path = temp_dir / "test"  # No extension

        saved_path = exporter.export_pptx(output_path)

        assert saved_path.suffix == ".pptx"

    def test_export_pptx_empty_raises(self, temp_dir):
        """Test that exporting empty slides raises error."""
        exporter = Exporter()

        with pytest.raises(RuntimeError, match="No slides to export"):
            exporter.export_pptx(temp_dir / "test.pptx")

    def test_export_images(self, temp_dir, sample_image):
        """Test exporting to images."""
        exporter = Exporter(slides=[sample_image, sample_image, sample_image])
        output_dir = temp_dir / "slides"

        paths = exporter.export_images(output_dir)

        assert len(paths) == 3
        assert all(p.exists() for p in paths)
        assert all(p.suffix == ".png" for p in paths)

    def test_export_images_jpg(self, temp_dir, sample_image):
        """Test exporting to JPEG format."""
        exporter = Exporter(slides=[sample_image])
        output_dir = temp_dir / "slides"

        paths = exporter.export_images(output_dir, format="jpg")

        assert paths[0].suffix == ".jpg"

    def test_export_images_creates_dir(self, temp_dir, sample_image):
        """Test that export creates output directory."""
        exporter = Exporter(slides=[sample_image])
        output_dir = temp_dir / "nested" / "slides"

        exporter.export_images(output_dir)

        assert output_dir.exists()

    def test_export_images_empty_raises(self, temp_dir):
        """Test that exporting empty slides raises error."""
        exporter = Exporter()

        with pytest.raises(RuntimeError, match="No slides to export"):
            exporter.export_images(temp_dir / "slides")

    def test_export_pdf(self, temp_dir, sample_image):
        """Test exporting to PDF."""
        exporter = Exporter(slides=[sample_image, sample_image])
        output_path = temp_dir / "test.pdf"

        saved_path = exporter.export_pdf(output_path)

        assert saved_path.exists()
        assert saved_path.suffix == ".pdf"

    def test_export_pdf_adds_extension(self, temp_dir, sample_image):
        """Test that export adds .pdf extension."""
        exporter = Exporter(slides=[sample_image])
        output_path = temp_dir / "test"  # No extension

        saved_path = exporter.export_pdf(output_path)

        assert saved_path.suffix == ".pdf"

    def test_export_pdf_empty_raises(self, temp_dir):
        """Test that exporting empty slides raises error."""
        exporter = Exporter()

        with pytest.raises(RuntimeError, match="No slides to export"):
            exporter.export_pdf(temp_dir / "test.pdf")

    def test_export_all(self, temp_dir, sample_image):
        """Test exporting to all formats."""
        exporter = Exporter(slides=[sample_image])
        base_path = temp_dir / "presentation"

        results = exporter.export_all(base_path)

        assert "pptx" in results
        assert "pdf" in results
        assert "images" in results
        assert results["pptx"].exists()
        assert results["pdf"].exists()
        assert isinstance(results["images"], list)
        assert all(p.exists() for p in results["images"])

    def test_export_all_specific_formats(self, temp_dir, sample_image):
        """Test exporting to specific formats only."""
        exporter = Exporter(slides=[sample_image])
        base_path = temp_dir / "presentation"

        results = exporter.export_all(base_path, formats=["pptx", "pdf"])

        assert "pptx" in results
        assert "pdf" in results
        assert "images" not in results
