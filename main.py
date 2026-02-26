#!/usr/bin/env python3
"""
Wallpaper Scaler - Scale images to fit specific output dimensions while maintaining aspect ratio.

The input image is scaled to match the output height (100% of target height), then centered
horizontally on a canvas with the specified output dimensions.
"""

import argparse
import sys
from pathlib import Path
from PIL import Image, ImageColor


def parse_color(color_string):
    """
    Parse a color string into an RGB tuple.
    
    Args:
        color_string: Color name (e.g., 'black', 'white') or hex code (e.g., '#FF0000')
    
    Returns:
        RGB tuple (r, g, b)
    """
    try:
        return ImageColor.getrgb(color_string)
    except ValueError:
        raise argparse.ArgumentTypeError(f"Invalid color: {color_string}")


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
        corner_size = min(10, max(1, width // 4), max(1, height // 4))
        
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
    if not pixels:
        raise ValueError("No pixels collected for edge sampling")
    
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
        background_color: RGB tuple for background color (default: black)
    
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
    
    # Validate output dimensions
    if output_width <= 0 or output_height <= 0:
        raise ValueError("Output dimensions must be positive integers")
    
    # Calculate scaled dimensions
    # The scaled image height should be 100% of the output height
    scaled_height = output_height
    
    # Calculate the scaled width maintaining the aspect ratio
    input_width, input_height = img.size
    aspect_ratio = input_width / input_height
    scaled_width = int(scaled_height * aspect_ratio)
    
    # Resize the input image
    scaled_img = img.resize((scaled_width, scaled_height), Image.Resampling.LANCZOS)
    
    # Create output canvas with background color
    # Handle both RGB and RGBA images
    if img.mode == 'RGBA' or (output_format and output_format.upper() == 'PNG'):
        canvas = Image.new('RGBA', (output_width, output_height), background_color + (255,))
    else:
        canvas = Image.new('RGB', (output_width, output_height), background_color)
    
    # Calculate position to center the scaled image horizontally
    x_offset = (output_width - scaled_width) // 2
    y_offset = 0  # Image is always at the top (or bottom) since it's 100% height
    
    # Paste the scaled image onto the canvas
    if scaled_img.mode == 'RGBA':
        canvas.paste(scaled_img, (x_offset, y_offset), scaled_img)
    else:
        if canvas.mode == 'RGBA':
            scaled_img = scaled_img.convert('RGBA')
        canvas.paste(scaled_img, (x_offset, y_offset))
    
    # Determine output path
    if output_path is None:
        input_path_obj = Path(input_path)
        output_path = input_path_obj.parent / f"{input_path_obj.stem}_scaled{input_path_obj.suffix}"
    
    # Determine output format
    if output_format:
        output_format = output_format.upper()
    else:
        # Use input format or infer from output path extension
        output_path_obj = Path(output_path)
        if output_path_obj.suffix:
            format_map = {
                '.jpg': 'JPEG',
                '.jpeg': 'JPEG',
                '.png': 'PNG',
                '.webp': 'WEBP',
                '.bmp': 'BMP',
            }
            output_format = format_map.get(output_path_obj.suffix.lower(), img.format)
        else:
            output_format = img.format
    
    # Convert RGBA to RGB for formats that don't support transparency
    if canvas.mode == 'RGBA' and output_format in ['JPEG', 'BMP']:
        # Create a white background for formats that don't support transparency
        rgb_canvas = Image.new('RGB', canvas.size, background_color)
        rgb_canvas.paste(canvas, (0, 0), canvas)
        canvas = rgb_canvas
    
    # Save the output image
    try:
        canvas.save(output_path, format=output_format)
    except Exception as e:
        raise ValueError(f"Failed to save output image: {e}")
    
    return output_path


def main():
    """Main entry point for the wallpaper-scaler CLI."""
    parser = argparse.ArgumentParser(
        description="Scale images to fit specific output dimensions while maintaining aspect ratio.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s input.jpg --width 3840 --height 1080
  %(prog)s input.jpg -w 3840 -h 1080 -o wallpaper.png -f png
  %(prog)s input.jpg -w 5120 -h 1440 --background "#1a1a1a"
        """
    )
    
    parser.add_argument(
        'input',
        type=str,
        help='Path to input image file'
    )
    
    parser.add_argument(
        '-w', '--width',
        type=int,
        required=True,
        help='Output width in pixels'
    )
    
    parser.add_argument(
        '--height',
        type=int,
        required=True,
        help='Output height in pixels'
    )
    
    parser.add_argument(
        '-o', '--output',
        type=str,
        help='Output file path (default: input_scaled.ext)'
    )
    
    parser.add_argument(
        '-f', '--format',
        type=str,
        choices=['jpg', 'jpeg', 'png', 'webp', 'bmp'],
        help='Output image format (default: same as input)'
    )
    
    parser.add_argument(
        '-b', '--background',
        type=parse_color,
        default='black',
        help='Background color (name or hex code, default: black)'
    )
    
    args = parser.parse_args()
    
    try:
        output_path = scale_image(
            input_path=args.input,
            output_width=args.width,
            output_height=args.height,
            output_path=args.output,
            output_format=args.format,
            background_color=args.background
        )
        
        print(f"Successfully created: {output_path}")
        print(f"Output dimensions: {args.width}x{args.height}")
        
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
