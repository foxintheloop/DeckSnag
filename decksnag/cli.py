"""Command-line interface for DeckSnag."""

import argparse
import sys
import time
import logging
from pathlib import Path
from typing import Optional, Tuple
from pynput import keyboard

from decksnag import __version__
from decksnag.config import Config
from decksnag.capture import ScreenCapture
from decksnag.comparison import ImageComparator
from decksnag.presentation import PresentationManager
from decksnag.exporter import Exporter
from decksnag.utils import setup_logging, format_duration

logger = logging.getLogger("decksnag")


def parse_region(region_str: str) -> Tuple[int, int, int, int]:
    """Parse a region string like 'x1,y1,x2,y2' into a tuple.

    Args:
        region_str: Region string in format 'x1,y1,x2,y2'.

    Returns:
        Tuple of (x1, y1, x2, y2).

    Raises:
        argparse.ArgumentTypeError: If format is invalid.
    """
    try:
        parts = [int(p.strip()) for p in region_str.split(",")]
        if len(parts) != 4:
            raise ValueError("Need exactly 4 values")
        return tuple(parts)  # type: ignore
    except ValueError as e:
        raise argparse.ArgumentTypeError(
            f"Invalid region format: '{region_str}'. "
            f"Use: x1,y1,x2,y2 (e.g., 100,100,800,600). Error: {e}"
        )


def create_parser() -> argparse.ArgumentParser:
    """Create the argument parser."""
    parser = argparse.ArgumentParser(
        prog="decksnag",
        description="Capture video presentations and convert them to PowerPoint slides.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  decksnag                            # Interactive mode with defaults
  decksnag -o slides.pptx             # Specify output file
  decksnag -i 3 -t 0.01               # 3 second interval, less sensitive
  decksnag -f pdf -o presentation     # Export as PDF
  decksnag --list-monitors            # Show available monitors
  decksnag -m 2                       # Capture from monitor 2
  decksnag -M clip                    # Use AI-powered comparison
  decksnag --gui                      # Launch graphical interface

Sensitivity presets:
  low     - Only major slide changes
  medium  - Balanced (default)
  high    - Catches subtle changes

Comparison methods:
  mse   - Mean Squared Error (fast, default)
  ssim  - Structural Similarity Index (fast, better perceptual)
  clip  - CLIP AI embeddings (accurate, uses neural network)
        """,
    )

    parser.add_argument(
        "-V", "--version",
        action="version",
        version=f"%(prog)s {__version__}",
    )

    parser.add_argument(
        "-o", "--output",
        type=Path,
        default=Path("./presentation"),
        metavar="PATH",
        help="Output file path (default: ./presentation)",
    )

    parser.add_argument(
        "-f", "--format",
        choices=["pptx", "pdf", "images", "all"],
        default="pptx",
        help="Output format (default: pptx)",
    )

    parser.add_argument(
        "-i", "--interval",
        type=float,
        default=5.0,
        metavar="SECONDS",
        help="Capture interval in seconds (default: 5)",
    )

    parser.add_argument(
        "-t", "--threshold",
        type=float,
        default=0.005,
        metavar="FLOAT",
        help="Change sensitivity threshold 0-1 (default: 0.005, lower=more sensitive)",
    )

    parser.add_argument(
        "-s", "--sensitivity",
        choices=["low", "medium", "high"],
        metavar="PRESET",
        help="Sensitivity preset (overrides --threshold)",
    )

    parser.add_argument(
        "-M", "--method",
        choices=["mse", "ssim", "clip"],
        default="mse",
        metavar="METHOD",
        help="Comparison method: mse (fast), ssim (fast), clip (AI-accurate)",
    )

    parser.add_argument(
        "-m", "--monitor",
        type=int,
        default=0,
        metavar="NUMBER",
        help="Monitor to capture (0=primary, default: 0)",
    )

    parser.add_argument(
        "-r", "--region",
        type=parse_region,
        metavar="X1,Y1,X2,Y2",
        help="Preset capture region (skip interactive selection)",
    )

    parser.add_argument(
        "-k", "--hotkey",
        default="end",
        metavar="KEY",
        help="Key to stop capture (default: end)",
    )

    parser.add_argument(
        "-v", "--verbose",
        action="store_true",
        help="Enable verbose logging",
    )

    parser.add_argument(
        "--list-monitors",
        action="store_true",
        help="List available monitors and exit",
    )

    parser.add_argument(
        "--gui",
        action="store_true",
        help="Launch graphical user interface",
    )

    return parser


def list_monitors() -> None:
    """Print available monitors and exit."""
    with ScreenCapture() as capture:
        monitors = capture.list_monitors()

    print("\nAvailable Monitors:")
    print("-" * 50)
    for mon in monitors:
        if mon.id == 0:
            print(f"  {mon.id}: All monitors combined ({mon.width}x{mon.height})")
        else:
            print(f"  {mon.id}: {mon.name} - {mon.width}x{mon.height} at ({mon.left}, {mon.top})")
    print()


def run_capture_session(config: Config) -> None:
    """Run the main capture session.

    Args:
        config: Configuration for the session.
    """
    stop_capture = False

    def on_key_press(key: keyboard.Key | keyboard.KeyCode) -> Optional[bool]:
        nonlocal stop_capture
        try:
            # Check if it's a special key
            if hasattr(key, "name") and key.name == config.stop_hotkey:
                logger.info(f"Stop key ({config.stop_hotkey}) pressed")
                stop_capture = True
                return False  # Stop listener
        except AttributeError:
            pass
        return None

    # Initialize components
    with ScreenCapture() as capture:
        comparator = ImageComparator(threshold=config.threshold, method=config.method)
        presentation = PresentationManager()
        exporter = Exporter()

        # Select capture region
        if config.region:
            region = config.region
            logger.info(f"Using preset region: {region}")
        else:
            region = capture.select_region_interactive()

        # Create presentation
        output_path = config.get_output_path_with_extension()
        presentation.create(output_path)

        # Capture first screenshot
        print("\n" + "=" * 50)
        print("CAPTURE STARTED")
        print("=" * 50)
        print(f"Press '{config.stop_hotkey.upper()}' key to stop capture")
        print(f"Interval: {config.interval} seconds")
        print(f"Method: {config.method.upper()}")
        print(f"Threshold: {config.threshold}")
        print(f"Output: {output_path}")
        print("=" * 50 + "\n")

        previous_image = capture.capture_region(region)
        presentation.add_slide(previous_image)
        exporter.add_slide(previous_image)

        # Start keyboard listener
        listener = keyboard.Listener(on_press=on_key_press)
        listener.start()

        start_time = time.time()

        try:
            while not stop_capture:
                time.sleep(config.interval)

                if stop_capture:
                    break

                # Capture current screenshot
                current_image = capture.capture_region(region)

                # Compare with previous
                if comparator.is_different(previous_image, current_image):
                    slide_num = presentation.add_slide(current_image)
                    exporter.add_slide(current_image)
                    elapsed = format_duration(time.time() - start_time)
                    print(f"[{elapsed}] Slide {slide_num} captured")
                    previous_image = current_image

        except KeyboardInterrupt:
            logger.info("Capture interrupted by user")

        finally:
            listener.stop()

        # Save results
        elapsed_total = format_duration(time.time() - start_time)
        slide_count = presentation.get_slide_count()

        print("\n" + "=" * 50)
        print("CAPTURE COMPLETE")
        print("=" * 50)
        print(f"Duration: {elapsed_total}")
        print(f"Slides captured: {slide_count}")

        # Export based on format
        if config.output_format == "all":
            results = exporter.export_all(config.output_path)
            print("Exported to:")
            for fmt, path in results.items():
                if isinstance(path, list):
                    print(f"  {fmt}: {path[0].parent}/")
                else:
                    print(f"  {fmt}: {path}")
        elif config.output_format == "images":
            images_dir = config.output_path.parent / f"{config.output_path.stem}_images"
            paths = exporter.export_images(images_dir)
            print(f"Saved to: {images_dir}/ ({len(paths)} images)")
        elif config.output_format == "pdf":
            path = exporter.export_pdf(config.output_path)
            print(f"Saved to: {path}")
        else:  # pptx
            path = presentation.save()
            print(f"Saved to: {path}")

        print("=" * 50 + "\n")


def main(args: Optional[list[str]] = None) -> int:
    """Main entry point for the CLI.

    Args:
        args: Command-line arguments (uses sys.argv if None).

    Returns:
        Exit code (0 for success).
    """
    parser = create_parser()
    parsed = parser.parse_args(args)

    # Setup logging
    setup_logging(verbose=parsed.verbose)

    # Handle special commands
    if parsed.list_monitors:
        list_monitors()
        return 0

    if parsed.gui:
        try:
            from decksnag.gui import main as gui_main
            gui_main()
            return 0
        except ImportError as e:
            logger.error(f"GUI not available: {e}")
            print("Error: GUI dependencies not installed.")
            print("Install with: pip install decksnag")
            return 1

    # Build configuration
    method = parsed.method
    threshold = parsed.threshold

    # If sensitivity preset is used, get appropriate threshold for the method
    if parsed.sensitivity:
        threshold = ImageComparator.threshold_from_sensitivity(parsed.sensitivity, method)
    elif method != "mse":
        # Use default threshold for the method if not explicitly set
        threshold = ImageComparator.DEFAULT_THRESHOLDS.get(method, threshold)

    try:
        config = Config(
            output_path=parsed.output,
            output_format=parsed.format,
            interval=parsed.interval,
            threshold=threshold,
            method=method,
            stop_hotkey=parsed.hotkey,
            monitor=parsed.monitor,
            region=parsed.region,
            verbose=parsed.verbose,
        )
    except ValueError as e:
        logger.error(f"Configuration error: {e}")
        return 1

    # Run capture session
    try:
        run_capture_session(config)
        return 0
    except Exception as e:
        logger.error(f"Error during capture: {e}")
        if parsed.verbose:
            import traceback
            traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
