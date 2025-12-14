# DeckSnag

[![CI](https://github.com/dplem/Video-to-PowerPoint/actions/workflows/ci.yml/badge.svg)](https://github.com/dplem/Video-to-PowerPoint/actions/workflows/ci.yml)
[![Python 3.9+](https://img.shields.io/badge/python-3.9+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

**Automatically capture video presentations and convert them to PowerPoint slides.**

When watching an online course, webinar, or live presentation where slides aren't provided, DeckSnag automatically detects slide changes and saves them to a PowerPoint file. No more manual screenshots!

## Features

- **Automatic Slide Detection** - Uses image comparison to detect when slides change
- **Multiple Output Formats** - Export to PowerPoint (.pptx), PDF, or image folder
- **Multi-Monitor Support** - Choose which monitor to capture
- **Adjustable Sensitivity** - Fine-tune detection for different presentation styles
- **Customizable Hotkeys** - Choose your preferred key to stop capture
- **Modern GUI** - Clean, intuitive interface built with CustomTkinter
- **Professional CLI** - Full command-line interface for automation
- **Cross-Platform** - Works on Windows, macOS, and Linux
- **AI-Powered Comparison** - CLIP neural network for robust slide detection

## Installation

### From PyPI (Recommended)

```bash
pip install decksnag
```

### From Source

```bash
git clone https://github.com/dplem/Video-to-PowerPoint.git
cd Video-to-PowerPoint
pip install -e .
```

### Development Installation

```bash
pip install -e ".[dev]"
```

## Quick Start

### GUI Mode

Launch the graphical interface:

```bash
decksnag --gui
```

Or use Python module syntax:

```bash
python -m decksnag --gui
```

### CLI Mode

Basic usage with interactive region selection:

```bash
decksnag -o my_presentation.pptx
```

The program will:
1. Ask you to click and drag to select the capture region
2. Start capturing slides (press **END** key to stop)
3. Save the presentation to the specified file

## CLI Reference

```
decksnag [OPTIONS]

Options:
  -o, --output PATH         Output file path (default: ./presentation)
  -f, --format FORMAT       Output format: pptx, pdf, images, all (default: pptx)
  -i, --interval SECONDS    Capture interval in seconds (default: 5)
  -t, --threshold FLOAT     Change sensitivity 0-1 (default: 0.005)
  -s, --sensitivity PRESET  Sensitivity preset: low, medium, high
  -M, --method METHOD       Comparison method: mse, ssim, clip (default: mse)
  -m, --monitor NUMBER      Monitor to capture (default: 0 for primary)
  -r, --region X1,Y1,X2,Y2  Preset capture region (skip selection)
  -k, --hotkey KEY          Stop hotkey (default: end)
  -v, --verbose             Enable verbose logging
  --list-monitors           List available monitors and exit
  --gui                     Launch graphical interface
  -V, --version             Show version and exit
  -h, --help                Show help message
```

### Examples

**Export as PDF:**
```bash
decksnag -o lecture -f pdf
```

**High sensitivity for subtle slide changes:**
```bash
decksnag -s high -i 3
```

**Capture specific region (skip interactive selection):**
```bash
decksnag -r 100,100,1920,1080 -o presentation
```

**Export to all formats:**
```bash
decksnag -f all -o my_slides
```

**Capture from second monitor:**
```bash
decksnag -m 2 -o presentation
```

**Use AI-powered comparison (more accurate):**
```bash
decksnag -M clip -o presentation
```

**List available monitors:**
```bash
decksnag --list-monitors
```

## Configuration

### Sensitivity Presets

| Preset | Threshold | Description |
|--------|-----------|-------------|
| `low` | 0.01 | Only detects major slide changes |
| `medium` | 0.005 | Balanced detection (default) |
| `high` | 0.001 | Catches subtle changes |

Lower threshold values = more sensitive to changes.

### Comparison Methods

| Method | Speed | Accuracy | Best For |
|--------|-------|----------|----------|
| `mse` | Fast | Basic | Clean presentations |
| `ssim` | Fast | Good | Similar to MSE, better perceptual |
| `clip` | Slower | Excellent | Complex videos, animations, presenter overlays |

**MSE (Mean Squared Error)** - Default method. Fast pixel-level comparison. Works well for clean presentations with minimal visual noise.

**SSIM (Structural Similarity Index)** - Similar speed to MSE but better at detecting perceptual differences in image structure.

**CLIP (AI-Powered)** - Uses neural network embeddings to understand image content semantically. More robust to visual noise like animations, mouse cursors, and video player UI.

### Capture Interval

The interval (in seconds) between screenshots. Default is 5 seconds.

- **Faster interval (1-3s)**: Better for fast-paced presentations
- **Slower interval (5-10s)**: Better for slower presentations, less CPU usage

## GUI Features

The graphical interface provides:

- **Region Selection** - Click a button to select capture area visually
- **Monitor Selection** - Dropdown to choose which monitor to capture
- **Settings Panel**:
  - Interval slider (1-30 seconds)
  - Sensitivity dropdown (Low/Medium/High)
  - Comparison method selection (MSE/SSIM/CLIP AI)
  - Output format selection
- **Live Preview** - Thumbnails of captured slides
- **Progress Tracking** - Slide count and elapsed time
- **Start/Stop Controls** - Easy capture management
- **Mini Mode** - Compact floating widget during capture

## How It Works

1. **Region Selection**: You select an area of your screen to monitor
2. **Initial Capture**: Takes a screenshot of the selected region
3. **Continuous Monitoring**: Every N seconds, takes a new screenshot
4. **Change Detection**: Compares new screenshot to previous using selected method (MSE, SSIM, or CLIP)
5. **Slide Addition**: If change exceeds threshold, adds new slide to presentation
6. **Export**: Saves to your chosen format when you stop capture

## API Usage

You can also use DeckSnag as a Python library:

```python
from decksnag import ScreenCapture, ImageComparator, PresentationManager

# Initialize components
capture = ScreenCapture()
comparator = ImageComparator(threshold=0.005)
presentation = PresentationManager()

# Select region interactively
region = capture.select_region_interactive()

# Create presentation
presentation.create("my_slides.pptx")

# Capture and add slides
previous = capture.capture_region(region)
presentation.add_slide(previous)

# ... capture loop ...
current = capture.capture_region(region)
if comparator.is_different(previous, current):
    presentation.add_slide(current)
    previous = current

# Save
presentation.save()
```

## Requirements

- Python 3.9 or higher
- Dependencies (installed automatically):
  - `mss` - Fast multi-monitor screenshots
  - `pynput` - Keyboard/mouse input handling
  - `Pillow` - Image processing
  - `python-pptx` - PowerPoint file creation
  - `scikit-image` - Image comparison (MSE, SSIM)
  - `customtkinter` - Modern GUI framework
  - `img2pdf` - PDF export
  - `sentence-transformers` - CLIP model for AI-powered comparison
  - `torch` - PyTorch for neural network inference

## Building Standalone Executable

Create a standalone executable that doesn't require Python:

```bash
pip install pyinstaller
pyinstaller decksnag.spec
```

The executable will be in the `dist/` folder.

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/AmazingFeature`)
3. Run tests (`pytest`)
4. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
5. Push to the branch (`git push origin feature/AmazingFeature`)
6. Open a Pull Request

### Development

```bash
# Install dev dependencies
pip install -e ".[dev]"

# Run tests
pytest

# Run linting
ruff check decksnag/

# Format code
black decksnag/ tests/
```

## Troubleshooting

### "No slides captured"

- Make sure the capture region covers the entire slide area
- Try increasing sensitivity (use `-s high` or lower threshold)
- Check that the presentation is actually changing slides

### "Too many slides captured"

- Decrease sensitivity (use `-s low` or higher threshold)
- Increase the capture interval (`-i 10`)

### Region selection doesn't work

- Make sure you click and drag (not just click twice)
- Try running with administrator privileges
- On Linux, ensure you have the required X11 libraries

### GUI doesn't start

- Ensure CustomTkinter is installed: `pip install customtkinter`
- On Linux, install Tk: `sudo apt-get install python3-tk`

## Support

- **Issues**: [GitHub Issues](https://github.com/dplem/Video-to-PowerPoint/issues)
- **Email**: plemons.derek@gmail.com

## License

This project is licensed under the MIT License - see the [LICENSE.txt](LICENSE.txt) file for details.

## Acknowledgments

- Original concept and initial implementation by Derek Plemons
- Built with [CustomTkinter](https://github.com/TomSchimansky/CustomTkinter) for the modern GUI
- Uses [python-pptx](https://python-pptx.readthedocs.io/) for PowerPoint generation
