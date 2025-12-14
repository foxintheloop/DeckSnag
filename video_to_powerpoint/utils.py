"""Utility functions for Video to PowerPoint."""

import logging
import sys
from pathlib import Path
from typing import Optional


def setup_logging(verbose: bool = False, log_file: Optional[Path] = None) -> logging.Logger:
    """Configure logging for the application.

    Args:
        verbose: If True, set level to DEBUG; otherwise INFO.
        log_file: Optional path to write logs to file.

    Returns:
        Configured logger instance.
    """
    logger = logging.getLogger("video_to_powerpoint")
    logger.setLevel(logging.DEBUG if verbose else logging.INFO)

    # Clear any existing handlers
    logger.handlers.clear()

    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.DEBUG if verbose else logging.INFO)
    console_format = logging.Formatter(
        "%(asctime)s - %(levelname)s - %(message)s",
        datefmt="%H:%M:%S"
    )
    console_handler.setFormatter(console_format)
    logger.addHandler(console_handler)

    # File handler (if specified)
    if log_file:
        file_handler = logging.FileHandler(log_file)
        file_handler.setLevel(logging.DEBUG)
        file_format = logging.Formatter(
            "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
        )
        file_handler.setFormatter(file_format)
        logger.addHandler(file_handler)

    return logger


def ensure_directory(path: Path) -> Path:
    """Ensure a directory exists, creating it if necessary.

    Args:
        path: Directory path to ensure exists.

    Returns:
        The path that was created/verified.

    Raises:
        PermissionError: If directory cannot be created due to permissions.
        OSError: If directory creation fails for other reasons.
    """
    path = Path(path)
    try:
        path.mkdir(parents=True, exist_ok=True)
        return path
    except PermissionError:
        raise PermissionError(f"Cannot create directory '{path}': Permission denied")
    except OSError as e:
        raise OSError(f"Cannot create directory '{path}': {e}")


def validate_file_path(path: Path, must_exist: bool = False) -> Path:
    """Validate a file path.

    Args:
        path: Path to validate.
        must_exist: If True, raise error if file doesn't exist.

    Returns:
        Validated Path object.

    Raises:
        FileNotFoundError: If must_exist=True and file doesn't exist.
        ValueError: If path is invalid.
    """
    path = Path(path)

    if must_exist and not path.exists():
        raise FileNotFoundError(f"File not found: {path}")

    # Check parent directory exists or can be created
    if not path.parent.exists():
        try:
            path.parent.mkdir(parents=True, exist_ok=True)
        except (PermissionError, OSError) as e:
            raise ValueError(f"Cannot access parent directory of '{path}': {e}")

    return path


def format_duration(seconds: float) -> str:
    """Format a duration in seconds to a human-readable string.

    Args:
        seconds: Duration in seconds.

    Returns:
        Formatted string like "1h 23m 45s" or "5m 30s".
    """
    hours, remainder = divmod(int(seconds), 3600)
    minutes, secs = divmod(remainder, 60)

    parts = []
    if hours:
        parts.append(f"{hours}h")
    if minutes:
        parts.append(f"{minutes}m")
    if secs or not parts:
        parts.append(f"{secs}s")

    return " ".join(parts)


def get_unique_path(path: Path) -> Path:
    """Get a unique file path by appending a number if the path exists.

    Args:
        path: Original path.

    Returns:
        Unique path that doesn't exist yet.
    """
    if not path.exists():
        return path

    stem = path.stem
    suffix = path.suffix
    parent = path.parent

    counter = 1
    while True:
        new_path = parent / f"{stem}_{counter}{suffix}"
        if not new_path.exists():
            return new_path
        counter += 1
