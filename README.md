# Wallpaper Scaler

A Python utility that scales images to fit specific output dimensions while maintaining aspect ratio. Perfect for creating wallpapers or fitting images to specific screen resolutions.

## Features

- Scales input image to match output height (100% of target height)
- Maintains original aspect ratio
- Centers the scaled image horizontally
- Customizable background color
- Supports multiple image formats (JPEG, PNG, WEBP, BMP)
- Command-line interface for easy automation

## Installation

1. Ensure you have Python 3.12 or higher installed
2. Install dependencies:

```bash
pip install pillow
```

Or if using uv:

```bash
uv pip install -e .
```

## Usage

### Basic Usage

```bash
python main.py input.jpg --width 3840 --height 1080
```

This will create `input_scaled.jpg` with dimensions 3840x1080.

### Specify Output File and Format

```bash
python main.py input.jpg -w 3840 -h 1080 -o wallpaper.png -f png
```

### Custom Background Color

```bash
# Using color name
python main.py input.jpg -w 5120 -h 1440 --background white

# Using hex code
python main.py input.jpg -w 3840 -h 1080 --background "#1a1a1a"
```

### Auto-Extract Background from Image

```bash
# Use dominant color from image
python main.py input.jpg -w 3840 --height 1080 --background auto

# Use average color
python main.py input.jpg -w 3840 --height 1080 --background auto:average

# Sample from image edges
python main.py input.jpg -w 3840 --height 1080 --background auto:edge:all

# Sample from corners only
python main.py input.jpg -w 3840 --height 1080 --background auto:edge:corners
```

#### Available Extraction Methods

- **dominant** (default): Extracts the most common color in the image
- **average**: Calculates the mean RGB value across all pixels
- **edge**: Samples colors from the image borders
  - **edge:all**: Sample from all four edges
  - **edge:corners**: Sample from corner regions only

### Complete Example

```bash
python main.py photo.jpg \
  --width 3840 \
  --height 1080 \
  --output my_wallpaper.png \
  --format png \
  --background "#000000"
```

## Command-Line Options

| Option | Short | Description | Required |
|--------|-------|-------------|----------|
| `input` | | Path to input image file | Yes |
| `--width` | `-w` | Output width in pixels | Yes |
| `--height` | `-h` | Output height in pixels | Yes |
| `--output` | `-o` | Output file path (default: input_scaled.ext) | No |
| `--format` | `-f` | Output format: jpg, jpeg, png, webp, bmp | No |
| `--background` | `-b` | Background color (name, hex, or auto extraction) | No |

## How It Works

1. **Load Input Image**: Opens the specified input image file
2. **Extract Background Color** (optional): If auto-extraction is enabled, analyzes the image to determine background color
3. **Calculate Scaling**: Scales the image to match 100% of the output height while maintaining aspect ratio
4. **Create Canvas**: Creates a new canvas with the specified output dimensions and background color
5. **Position Image**: Centers the scaled image horizontally on the canvas
6. **Save Output**: Saves the final image in the specified format

## Examples

### Example 1: 4:3 Image on 32:9 Display

```bash
python main.py photo_4_3.jpg --width 5120 --height 1440
```

Input: 1600x1200 (4:3 ratio)
Output: 5120x1440 (32:9 ratio)
Result: Image scaled to 1920x1440, centered with black bars on left and right

### Example 2: 16:9 Image on 21:9 Display

```bash
python main.py wallpaper_16_9.jpg -w 3440 -h 1440 -o ultrawide.png
```

Input: 1920x1080 (16:9 ratio)
Output: 3440x1440 (21:9 ratio)
Result: Image scaled to 2560x1440, centered with black bars on sides

### Example 3: Portrait Image on Landscape Display

```bash
python main.py portrait.jpg -w 1920 -h 1080
```

Input: 1080x1920 (9:16 ratio)
Output: 1920x1080 (16:9 ratio)
Result: Image scaled to 607x1080, centered with black bars on sides

## Supported Image Formats

- **Input**: Any format supported by Pillow (JPEG, PNG, WEBP, BMP, GIF, TIFF, etc.)
- **Output**: JPEG, PNG, WEBP, BMP

## Notes

- Images are always upscaled or downscaled to match the output height exactly
- The aspect ratio of the input image is always preserved
- For formats that don't support transparency (JPEG, BMP), RGBA images are converted to RGB with the specified background color
- High-quality Lanczos resampling is used for scaling to maintain image quality

## License

MIT License - feel free to use this utility for any purpose.
