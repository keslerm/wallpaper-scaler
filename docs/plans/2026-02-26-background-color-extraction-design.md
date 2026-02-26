# Background Color Extraction Feature Design

**Date:** 2026-02-26  
**Status:** Approved  
**Approach:** Pure Pillow Implementation

## Overview

Add automatic background color extraction that analyzes the input image and uses a derived color for the canvas background instead of requiring users to specify a color manually.

## Requirements

- Multiple color extraction methods available via CLI
- Backwards compatible with existing manual color specification
- User-configurable sampling strategies
- Default to dominant color extraction
- No additional dependencies beyond Pillow

## CLI Interface

### Syntax

The `--background` flag will accept both manual colors and auto-extraction specifications:

```bash
--background auto                    # Use dominant color (default method)
--background auto:dominant           # Explicitly use dominant color
--background auto:average            # Use average/mean color
--background auto:edge               # Sample from edge pixels (default: all edges)
--background auto:edge:corners       # Sample only from corners
--background auto:edge:all           # Sample from all edges
--background "#FF0000"               # Existing behavior: manual color
--background black                   # Existing behavior: named color
```

### Examples

```bash
# Auto with default (dominant)
python main.py input.jpg -w 3840 --height 1080 --background auto

# Specific extraction methods
python main.py input.jpg -w 3840 --height 1080 --background auto:average
python main.py input.jpg -w 3840 --height 1080 --background auto:edge:corners

# Still works - manual color
python main.py input.jpg -w 3840 --height 1080 --background black
```

## Color Extraction Algorithms

### 1. Dominant Color Extraction (Default)

**Method:** Analyze pixel color frequency using Pillow's quantization

**Implementation:**
1. Convert image to RGB if needed
2. Use `Image.quantize(colors=1)` to reduce to single dominant color
3. Extract that color's RGB value
4. Alternative fallback: Build histogram and find peak color

**Characteristics:**
- Fast and simple
- Works well for images with clear color themes
- Best for images with distinct color regions

### 2. Average Color Extraction

**Method:** Calculate mean RGB values across all pixels

**Implementation:**
1. Get all pixel data using `Image.getdata()`
2. Calculate average R, G, B values
3. For large images (>2MP), optionally downsample first for performance

**Characteristics:**
- Mathematical average creates "blended" color
- Good for images without single dominant color
- Result may not be a color that actually appears in image

### 3. Edge Sampling

**Method:** Sample pixels from image borders

**Implementation:**
- **corners mode**: Sample pixels from 4 corners (10x10 region from each corner)
- **all mode**: Sample pixels along all four edges
- Calculate average color from sampled regions

**Characteristics:**
- Useful when background is at image edges
- Good for photos with centered subjects
- Fast - only analyzes small portion of image

## Code Architecture

### New Functions

#### `extract_background_color(img, method='dominant', sampling_region='all')`
Main entry point for color extraction.

**Parameters:**
- `img`: PIL Image object
- `method`: 'dominant', 'average', or 'edge'
- `sampling_region`: 'all', 'corners' (for edge method)

**Returns:** RGB tuple (r, g, b)

**Behavior:** Dispatches to specific extraction functions based on method

#### `extract_dominant_color(img)`
Uses `Image.quantize(colors=1)` to find most common color.

**Returns:** RGB tuple

#### `extract_average_color(img)`
Calculates mean RGB across all pixels. Optionally downsamples large images (>2MP) for performance.

**Returns:** RGB tuple

#### `extract_edge_color(img, region='all')`
Samples pixels from image borders.

**Parameters:**
- `region='corners'`: Sample 10x10 from each corner
- `region='all'`: Sample all edge pixels

**Returns:** Average RGB tuple of sampled pixels

#### `parse_background_arg(background_string)`
Replaces the existing `parse_color()` function.

**Parameters:**
- `background_string`: Either a color spec or auto-extraction spec

**Returns:** 
- If manual color: RGB tuple
- If auto: dict with `{'auto': True, 'method': str, 'region': str}`

**Examples:**
- `"black"` → `(0, 0, 0)`
- `"#FF0000"` → `(255, 0, 0)`
- `"auto"` → `{'auto': True, 'method': 'dominant', 'region': 'all'}`
- `"auto:edge:corners"` → `{'auto': True, 'method': 'edge', 'region': 'corners'}`

### Modified Functions

#### `scale_image()`
**Changes:**
- Accept extraction spec dict in addition to RGB tuple for `background_color` parameter
- If auto-extraction requested, call `extract_background_color()` after loading image
- Pass extracted color to canvas creation
- Add verbose output showing extracted color when applicable

#### `main()`
**Changes:**
- Update to use new `parse_background_arg()` function instead of `parse_color()`
- Pass extraction spec to `scale_image()`
- Update argument parser help text with auto-extraction examples

### Error Handling

- **Invalid method names**: Provide helpful error message listing valid methods
- **Color extraction failures**: Fallback to black with warning message
- **Large images**: Automatic downsampling for average color with debug message if verbose
- **Malformed auto spec**: Clear error showing expected format

## Performance Considerations

- **Dominant color**: Fast, uses optimized Pillow quantization
- **Average color**: Downsample images >2MP (1920x1080) to 1MP before averaging
- **Edge sampling**: Fastest, only processes border pixels

## Testing Strategy

Test cases to validate:
1. `--background auto` uses dominant color
2. `--background auto:average` calculates average color
3. `--background auto:edge:corners` samples corners only
4. `--background auto:edge:all` samples all edges
5. Backwards compatibility with manual colors (`--background black`, `--background "#FF0000"`)
6. Invalid method names produce helpful errors
7. Large images are handled efficiently

## Future Enhancements (Not in Scope)

- K-means clustering for better dominant color detection
- Perceptual color weighting
- Multiple color palette extraction
- Blur/gradient backgrounds using extracted colors
