"""Export functionality for multiple output formats."""

import logging
from pathlib import Path
from typing import List, Literal, Optional
from PIL import Image

logger = logging.getLogger("video_to_powerpoint")

# Type alias for supported formats
ExportFormat = Literal["pptx", "pdf", "images"]


class Exporter:
    """Export slides to various formats (PPTX, PDF, images)."""

    def __init__(self, slides: Optional[List[Image.Image]] = None) -> None:
        """Initialize the exporter.

        Args:
            slides: Optional list of slide images.
        """
        self._slides: List[Image.Image] = slides or []

    def set_slides(self, slides: List[Image.Image]) -> None:
        """Set the slides to export.

        Args:
            slides: List of PIL Images.
        """
        self._slides = [img.copy() for img in slides]

    def add_slide(self, image: Image.Image) -> None:
        """Add a slide to the export queue.

        Args:
            image: PIL Image to add.
        """
        self._slides.append(image.copy())

    def export_pptx(self, output_path: Path) -> Path:
        """Export slides to PowerPoint format.

        Args:
            output_path: Output file path.

        Returns:
            Path where the file was saved.

        Raises:
            RuntimeError: If no slides to export.
        """
        if not self._slides:
            raise RuntimeError("No slides to export")

        from video_to_powerpoint.presentation import PresentationManager

        output_path = Path(output_path)
        if output_path.suffix.lower() != ".pptx":
            output_path = output_path.with_suffix(".pptx")

        manager = PresentationManager()
        manager.create(output_path)

        for slide in self._slides:
            manager.add_slide(slide)

        saved_path = manager.save()
        logger.info(f"Exported {len(self._slides)} slides to PowerPoint: {saved_path}")

        return saved_path

    def export_images(self, output_dir: Path, format: str = "png") -> List[Path]:
        """Export slides as individual image files.

        Args:
            output_dir: Directory to save images.
            format: Image format ('png', 'jpg', 'jpeg').

        Returns:
            List of paths where images were saved.

        Raises:
            RuntimeError: If no slides to export.
        """
        if not self._slides:
            raise RuntimeError("No slides to export")

        output_dir = Path(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)

        saved_paths = []
        format = format.lower()

        for i, slide in enumerate(self._slides, 1):
            filename = f"slide_{i:03d}.{format}"
            file_path = output_dir / filename

            # Convert to RGB for JPEG
            if format in ("jpg", "jpeg"):
                slide = slide.convert("RGB")

            slide.save(file_path)
            saved_paths.append(file_path)
            logger.debug(f"Saved slide {i}: {file_path}")

        logger.info(f"Exported {len(self._slides)} slides to: {output_dir}")
        return saved_paths

    def export_pdf(self, output_path: Path) -> Path:
        """Export slides to PDF format.

        Args:
            output_path: Output file path.

        Returns:
            Path where the PDF was saved.

        Raises:
            RuntimeError: If no slides to export.
        """
        if not self._slides:
            raise RuntimeError("No slides to export")

        try:
            import img2pdf
        except ImportError:
            raise RuntimeError(
                "img2pdf is required for PDF export. Install with: pip install img2pdf"
            )

        output_path = Path(output_path)
        if output_path.suffix.lower() != ".pdf":
            output_path = output_path.with_suffix(".pdf")

        output_path.parent.mkdir(parents=True, exist_ok=True)

        # Convert slides to bytes for img2pdf
        import io

        image_bytes_list = []
        for slide in self._slides:
            # Convert to RGB (img2pdf doesn't support RGBA)
            rgb_slide = slide.convert("RGB")
            img_bytes = io.BytesIO()
            rgb_slide.save(img_bytes, format="PNG")
            image_bytes_list.append(img_bytes.getvalue())

        # Create PDF
        pdf_bytes = img2pdf.convert(image_bytes_list)

        with open(output_path, "wb") as f:
            f.write(pdf_bytes)

        logger.info(f"Exported {len(self._slides)} slides to PDF: {output_path}")
        return output_path

    def export_all(
        self, base_path: Path, formats: Optional[List[ExportFormat]] = None
    ) -> dict[str, Path | List[Path]]:
        """Export slides to multiple formats.

        Args:
            base_path: Base path for output files (extensions will be added).
            formats: List of formats to export. Defaults to all formats.

        Returns:
            Dictionary mapping format names to output paths.
        """
        if formats is None:
            formats = ["pptx", "pdf", "images"]

        base_path = Path(base_path)
        results: dict[str, Path | List[Path]] = {}

        for fmt in formats:
            if fmt == "pptx":
                results["pptx"] = self.export_pptx(base_path.with_suffix(".pptx"))
            elif fmt == "pdf":
                results["pdf"] = self.export_pdf(base_path.with_suffix(".pdf"))
            elif fmt == "images":
                images_dir = base_path.parent / f"{base_path.stem}_images"
                results["images"] = self.export_images(images_dir)

        return results

    def get_slide_count(self) -> int:
        """Get the number of slides queued for export."""
        return len(self._slides)

    def clear(self) -> None:
        """Clear all queued slides."""
        self._slides = []
