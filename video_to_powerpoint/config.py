"""Configuration management for Video to PowerPoint."""

from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional, Tuple, Literal


@dataclass
class Config:
    """Configuration settings for the capture session.

    Attributes:
        output_path: Path for the output file (without extension for multi-format).
        output_format: Output format(s) - 'pptx', 'pdf', 'images', or 'all'.
        interval: Time between captures in seconds.
        threshold: MSE threshold for detecting slide changes (lower = more sensitive).
        stop_hotkey: Keyboard key to stop capture.
        monitor: Monitor index to capture from (0 = primary).
        region: Capture region as (x1, y1, x2, y2) or None for interactive selection.
        verbose: Enable verbose logging output.
    """

    output_path: Path = field(default_factory=lambda: Path("./presentation"))
    output_format: Literal["pptx", "pdf", "images", "all"] = "pptx"
    interval: float = 5.0
    threshold: float = 0.005
    stop_hotkey: str = "end"
    monitor: int = 0
    region: Optional[Tuple[int, int, int, int]] = None
    verbose: bool = False

    # Sensitivity presets for user-friendly configuration
    SENSITIVITY_PRESETS = {
        "low": 0.01,      # Less sensitive - only major changes
        "medium": 0.005,  # Default - balanced
        "high": 0.001,    # More sensitive - catches subtle changes
    }

    def __post_init__(self) -> None:
        """Validate configuration after initialization."""
        if isinstance(self.output_path, str):
            self.output_path = Path(self.output_path)

        if self.interval < 0.5:
            raise ValueError("Interval must be at least 0.5 seconds")

        if self.interval > 60:
            raise ValueError("Interval must be at most 60 seconds")

        if not 0 < self.threshold < 1:
            raise ValueError("Threshold must be between 0 and 1")

        if self.monitor < 0:
            raise ValueError("Monitor index must be non-negative")

        if self.region is not None:
            if len(self.region) != 4:
                raise ValueError("Region must be a tuple of 4 integers (x1, y1, x2, y2)")
            x1, y1, x2, y2 = self.region
            if x2 <= x1 or y2 <= y1:
                raise ValueError("Invalid region: x2 must be > x1 and y2 must be > y1")

    @classmethod
    def from_sensitivity_preset(cls, preset: str, **kwargs) -> "Config":
        """Create config with a sensitivity preset.

        Args:
            preset: One of 'low', 'medium', 'high'.
            **kwargs: Other configuration options.

        Returns:
            Config instance with the preset threshold.
        """
        if preset not in cls.SENSITIVITY_PRESETS:
            raise ValueError(f"Unknown preset: {preset}. Use: {list(cls.SENSITIVITY_PRESETS.keys())}")

        kwargs["threshold"] = cls.SENSITIVITY_PRESETS[preset]
        return cls(**kwargs)

    def get_output_path_with_extension(self, format_type: str = None) -> Path:
        """Get the output path with the appropriate extension.

        Args:
            format_type: Override the output format for the extension.

        Returns:
            Path with the correct extension.
        """
        fmt = format_type or self.output_format

        if fmt == "images":
            return self.output_path  # Directory, no extension
        elif fmt == "all":
            return self.output_path  # Base path, extensions added per format
        else:
            # Remove any existing extension and add the correct one
            stem = self.output_path.stem if self.output_path.suffix else self.output_path.name
            return self.output_path.parent / f"{stem}.{fmt}"
