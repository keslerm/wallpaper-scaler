# Background Color Extraction Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Add automatic background color extraction from input images with multiple extraction methods (dominant, average, edge sampling).

**Architecture:** Extend existing `--background` flag to accept `auto:method:region` syntax. Add color extraction functions using pure Pillow. Maintain backwards compatibility with manual color specifications.

**Tech Stack:** Python 3.12+, Pillow (PIL)

---

## Task 1: Implement Color Extraction Functions

**Files:**
- Modify: `main.py` (add functions after line 28)

**Step 1: Add extract_dominant_color function**

Add this function after the `parse_color()` function:

```python
def extract_dominant_color(img):
    """
    Extract the dominant (most common) color from an image.
    
    Args:
        img: PIL Image object
    
    Returns:
        RGB tuple (r, g, b)
    """
    # Convert to RGB if needed
    if img.mode != 'RGB':
        img = img.convert('RGB')
    
    # Use quantization to find dominant color
    # Reduce image to 1 color (the most dominant)
    quantized = img.quantize(colors=1)
    
    # Get the palette and extract the single color
    palette = quantized.getpalette()
    # Palette is a flat list [r1, g1, b1, r2, g2, b2, ...]
    # We want the first color
    dominant_color = (palette[0], palette[1], palette[2])
    
    return dominant_color
```

**Step 2: Add extract_average_color function**

```python
def extract_average_color(img):
    """
    Extract the average color from an image.
    
    Args:
        img: PIL Image object
    
    Returns:
        RGB tuple (r, g, b)
    """
    # Convert to RGB if needed
    if img.mode != 'RGB':
        img = img.convert('RGB')
    
    # For large images, downsample for performance
    width, height = img.size
    if width * height > 2_000_000:  # > 2 megapixels
        # Downsample to ~1MP
        scale_factor = (1_000_000 / (width * height)) ** 0.5
        new_size = (int(width * scale_factor), int(height * scale_factor))
        img = img.resize(new_size, Image.Resampling.LANCZOS)
    
    # Get all pixels
    pixels = list(img.getdata())
    
    # Calculate average RGB
    total_r = sum(p[0] for p in pixels)
    total_g = sum(p[1] for p in pixels)
    total_b = sum(p[2] for p in pixels)
    
    num_pixels = len(pixels)
    avg_color = (
        total_r // num_pixels,
        total_g // num_pixels,
        total_b // num_pixels
    )
    
    return avg_color
```

**Step 3: Add extract_edge_color function**

```python
def extract_edge_color(img, region='all'):
    """
    Extract color by sampling from image edges.
    
    Args:
        img: PIL Image object
        region: 'all' for all edges, 'corners' for corner regions only
    
    Returns:
        RGB tuple (r, g, b)
    """
    # Convert to RGB if needed
    if img.mode != 'RGB':
        img = img.convert('RGB')
    
    width, height = img.size
    pixels = []
    
    if region == 'corners':
        # Sample 10x10 regions from each corner
        corner_size = min(10, width // 4, height // 4)
        
        # Top-left
        for y in range(corner_size):
            for x in range(corner_size):
                pixels.append(img.getpixel((x, y)))
        
        # Top-right
        for y in range(corner_size):
            for x in range(width - corner_size, width):
                pixels.append(img.getpixel((x, y)))
        
        # Bottom-left
        for y in range(height - corner_size, height):
            for x in range(corner_size):
                pixels.append(img.getpixel((x, y)))
        
        # Bottom-right
        for y in range(height - corner_size, height):
            for x in range(width - corner_size, width):
                pixels.append(img.getpixel((x, y)))
    
    else:  # region == 'all'
        # Sample all edge pixels
        # Top edge
        for x in range(width):
            pixels.append(img.getpixel((x, 0)))
        
        # Bottom edge
        for x in range(width):
            pixels.append(img.getpixel((x, height - 1)))
        
        # Left edge (excluding corners already sampled)
        for y in range(1, height - 1):
            pixels.append(img.getpixel((0, y)))
        
        # Right edge (excluding corners already sampled)
        for y in range(1, height - 1):
            pixels.append(img.getpixel((width - 1, y)))
    
    # Calculate average of sampled pixels
    total_r = sum(p[0] for p in pixels)
    total_g = sum(p[1] for p in pixels)
    total_b = sum(p[2] for p in pixels)
    
    num_pixels = len(pixels)
    avg_color = (
        total_r // num_pixels,
        total_g // num_pixels,
        total_b // num_pixels
    )
    
    return avg_color
```

**Step 4: Add extract_background_color dispatcher function**

```python
def extract_background_color(img, method='dominant', sampling_region='all'):
    """
    Extract background color from an image using specified method.
    
    Args:
        img: PIL Image object
        method: 'dominant', 'average', or 'edge'
        sampling_region: 'all' or 'corners' (used for edge method)
    
    Returns:
        RGB tuple (r, g, b)
    
    Raises:
        ValueError: If method is invalid
    """
    if method == 'dominant':
        return extract_dominant_color(img)
    elif method == 'average':
        return extract_average_color(img)
    elif method == 'edge':
        return extract_edge_color(img, region=sampling_region)
    else:
        raise ValueError(
            f"Invalid extraction method: {method}. "
            f"Valid methods: dominant, average, edge"
        )
```

**Step 5: Verify functions compile**

Run: `python -m py_compile main.py`
Expected: No output (successful compilation)

**Step 6: Commit**

```bash
git add main.py
git commit -m "feat: add color extraction functions (dominant, average, edge)"
```

---

## Task 2: Update Background Argument Parser

**Files:**
- Modify: `main.py:15-28` (replace `parse_color` function)

**Step 1: Replace parse_color with parse_background_arg**

Replace the existing `parse_color()` function with:

```python
def parse_background_arg(background_string):
    """
    Parse a background argument into either an RGB tuple or extraction spec.
    
    Args:
        background_string: Color name, hex code, or auto extraction spec
                          Examples: 'black', '#FF0000', 'auto', 'auto:average',
                                   'auto:edge:corners'
    
    Returns:
        Either:
        - RGB tuple (r, g, b) for manual colors
        - Dict with extraction spec: {'auto': True, 'method': str, 'region': str}
    
    Raises:
        argparse.ArgumentTypeError: If format is invalid
    """
    # Check if it's an auto-extraction spec
    if background_string.startswith('auto'):
        parts = background_string.split(':')
        
        # Default values
        method = 'dominant'
        region = 'all'
        
        # Parse method
        if len(parts) >= 2:
            method = parts[1]
            if method not in ['dominant', 'average', 'edge']:
                raise argparse.ArgumentTypeError(
                    f"Invalid extraction method: {method}. "
                    f"Valid methods: dominant, average, edge"
                )
        
        # Parse region (only for edge method)
        if len(parts) >= 3:
            region = parts[2]
            if region not in ['all', 'corners']:
                raise argparse.ArgumentTypeError(
                    f"Invalid sampling region: {region}. "
                    f"Valid regions: all, corners"
                )
        
        return {
            'auto': True,
            'method': method,
            'region': region
        }
    
    # Otherwise, parse as a color
    try:
        return ImageColor.getrgb(background_string)
    except ValueError:
        raise argparse.ArgumentTypeError(
            f"Invalid color or auto spec: {background_string}"
        )
```

**Step 2: Update argument parser in main()**

Find the `--background` argument definition (around line 170) and update it:

```python
parser.add_argument(
    '-b', '--background',
    type=parse_background_arg,
    default='black',
    help='Background color (name, hex code, or auto extraction: auto[:method[:region]])'
)
```

**Step 3: Update help epilog with auto examples**

Find the epilog section in `main()` and update it to:

```python
epilog="""
Examples:
  %(prog)s input.jpg --width 3840 --height 1080
  %(prog)s input.jpg -w 3840 -h 1080 -o wallpaper.png -f png
  %(prog)s input.jpg -w 5120 -h 1440 --background "#1a1a1a"
  %(prog)s input.jpg -w 3840 -h 1080 --background auto
  %(prog)s input.jpg -w 3840 -h 1080 --background auto:average
  %(prog)s input.jpg -w 3840 -h 1080 --background auto:edge:corners
        """
```

**Step 4: Test argument parsing**

Run: `python main.py --help`
Expected: Help text displays with auto extraction examples

Run: `python main.py test.jpg -w 100 --height 100 --background "invalid:method"`
Expected: Error message about invalid extraction method

**Step 5: Commit**

```bash
git add main.py
git commit -m "feat: update background argument parser to support auto extraction"
```

---

## Task 3: Update scale_image Function

**Files:**
- Modify: `main.py:31-120` (scale_image function)

**Step 1: Update scale_image signature and handle auto extraction**

Modify the `scale_image()` function to handle extraction specs. Update the beginning of the function to:

```python
def scale_image(input_path, output_width, output_height, output_path=None, 
                output_format=None, background_color=(0, 0, 0)):
    """
    Scale an image to fit within specified dimensions while maintaining aspect ratio.
    
    Args:
        input_path: Path to input image file
        output_width: Target output width in pixels
        output_height: Target output height in pixels
        output_path: Path for output file (optional)
        output_format: Output image format (optional, e.g., 'PNG', 'JPEG')
        background_color: RGB tuple or extraction spec dict
    
    Returns:
        Path to the output file
    """
    # Load input image
    try:
        img = Image.open(input_path)
    except FileNotFoundError:
        raise FileNotFoundError(f"Input file not found: {input_path}")
    except Exception as e:
        raise ValueError(f"Failed to open image: {e}")
    
    # Handle auto background color extraction
    if isinstance(background_color, dict) and background_color.get('auto'):
        try:
            extracted_color = extract_background_color(
                img,
                method=background_color.get('method', 'dominant'),
                sampling_region=background_color.get('region', 'all')
            )
            print(f"Extracted background color: RGB{extracted_color} using method '{background_color['method']}'")
            background_color = extracted_color
        except Exception as e:
            print(f"Warning: Color extraction failed ({e}), falling back to black")
            background_color = (0, 0, 0)
    
    # Validate output dimensions
    if output_width <= 0 or output_height <= 0:
        raise ValueError("Output dimensions must be positive integers")
```

**Step 2: Verify compilation**

Run: `python -m py_compile main.py`
Expected: No output (successful compilation)

**Step 3: Commit**

```bash
git add main.py
git commit -m "feat: integrate color extraction into scale_image function"
```

---

## Task 4: Create Test Script and Validate

**Files:**
- Create: `test_color_extraction.py`

**Step 1: Create comprehensive test script**

```python
#!/usr/bin/env python3
"""Test script for color extraction feature."""

from PIL import Image, ImageDraw
import subprocess
import sys
from pathlib import Path

def create_test_image(filename, size, color, has_border=False):
    """Create a test image with specified color."""
    img = Image.new('RGB', size, color=color)
    
    if has_border:
        draw = ImageDraw.Draw(img)
        border_color = tuple(255 - c for c in color)  # Inverse color
        draw.rectangle([0, 0, size[0]-1, size[1]-1], outline=border_color, width=20)
    
    img.save(filename, 'JPEG')
    print(f"Created {filename}: {size}, color={color}")

def run_scaler(input_file, background_arg):
    """Run the wallpaper scaler with specified background."""
    cmd = [
        sys.executable, 'main.py',
        input_file,
        '-w', '1920',
        '--height', '1080',
        '--background', background_arg
    ]
    
    result = subprocess.run(cmd, capture_output=True, text=True)
    print(f"\n--- Test: --background {background_arg} ---")
    print(result.stdout)
    if result.returncode != 0:
        print("STDERR:", result.stderr, file=sys.stderr)
        return False
    return True

def main():
    """Run all tests."""
    # Clean up any existing test files
    for f in Path('.').glob('test_*.jpg'):
        f.unlink()
    for f in Path('.').glob('test_*_scaled.jpg'):
        f.unlink()
    
    print("=== Creating Test Images ===")
    
    # Create test images
    # Blue image (should extract blue-ish color)
    create_test_image('test_blue.jpg', (800, 600), (70, 130, 180))
    
    # Red image with border (for edge testing)
    create_test_image('test_red_border.jpg', (800, 600), (180, 70, 70), has_border=True)
    
    # Green image
    create_test_image('test_green.jpg', (800, 600), (70, 180, 90))
    
    print("\n=== Running Tests ===")
    
    tests = [
        ('test_blue.jpg', 'auto'),
        ('test_blue.jpg', 'auto:dominant'),
        ('test_blue.jpg', 'auto:average'),
        ('test_red_border.jpg', 'auto:edge:corners'),
        ('test_red_border.jpg', 'auto:edge:all'),
        ('test_green.jpg', 'black'),  # Manual color (backwards compatibility)
        ('test_green.jpg', '#FF0000'),  # Hex color (backwards compatibility)
    ]
    
    passed = 0
    failed = 0
    
    for input_file, bg_arg in tests:
        if run_scaler(input_file, bg_arg):
            passed += 1
        else:
            failed += 1
    
    print(f"\n=== Results ===")
    print(f"Passed: {passed}/{len(tests)}")
    print(f"Failed: {failed}/{len(tests)}")
    
    if failed > 0:
        sys.exit(1)

if __name__ == '__main__':
    main()
```

**Step 2: Run test script**

Run: `python test_color_extraction.py`
Expected: All tests pass, output shows extracted colors for auto modes

**Step 3: Visual inspection**

Manually inspect a few output images to verify:
- Colors are extracted correctly
- Images are centered properly
- Background fills correctly

**Step 4: Clean up test files**

Run: `rm test_*.jpg test_*_scaled.jpg test_color_extraction.py`

**Step 5: Commit**

```bash
git add .
git commit -m "test: validate color extraction feature"
```

---

## Task 5: Update Documentation

**Files:**
- Modify: `README.md`

**Step 1: Add auto-extraction section to README**

Find the "Custom Background Color" section and add after it:

```markdown
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
```

**Step 2: Update command-line options table**

Update the `--background` row in the options table:

```markdown
| `--background` | `-b` | Background color (name, hex, or auto extraction) | No |
```

**Step 3: Add to "How It Works" section**

Add a new step in the numbered list:

```markdown
1. **Load Input Image**: Opens the specified input image file
2. **Extract Background Color** (optional): If auto-extraction is enabled, analyzes the image to determine background color
3. **Calculate Scaling**: Scales the image to match 100% of the output height while maintaining aspect ratio
4. **Create Canvas**: Creates a new canvas with the specified output dimensions and background color
5. **Position Image**: Centers the scaled image horizontally on the canvas
6. **Save Output**: Saves the final image in the specified format
```

**Step 4: Verify README renders correctly**

Review the README.md file to ensure markdown formatting is correct.

**Step 5: Commit**

```bash
git add README.md
git commit -m "docs: add auto background color extraction to README"
```

---

## Task 6: Final Integration Test

**Files:**
- Test with real-world image

**Step 1: Test with actual image**

If you have a test image available:

Run: `python main.py <your-image.jpg> -w 3840 --height 1080 --background auto`
Expected: Image scaled correctly with extracted background color

**Step 2: Test error handling**

Run: `python main.py nonexistent.jpg -w 3840 --height 1080 --background auto:invalid`
Expected: Clear error message about invalid method

**Step 3: Test backwards compatibility**

Run: `python main.py <image> -w 1920 --height 1080 --background black`
Expected: Works as before with black background

**Step 4: Final commit if any fixes needed**

If any bugs found and fixed:
```bash
git add .
git commit -m "fix: final integration fixes for color extraction"
```

---

## Completion Checklist

- [ ] Color extraction functions implemented (dominant, average, edge)
- [ ] Background argument parser updated to handle auto specs
- [ ] scale_image function updated to use extracted colors
- [ ] All tests pass
- [ ] README documentation updated
- [ ] Backwards compatibility maintained
- [ ] Error handling works correctly
- [ ] Code follows existing style
