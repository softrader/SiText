#!/usr/bin/env python3
"""Create a rounded-corner version of the app icon (iOS-style)."""

from PIL import Image, ImageDraw
from pathlib import Path


def add_rounded_corners(input_path: Path, output_path: Path, radius_percent: float = 0.225, padding_percent: float = 0.08):
    """Add rounded corners to an image (iOS-style) with padding for Dock.
    
    Args:
        input_path: Path to input image
        output_path: Path to save output image
        radius_percent: Corner radius as percentage of image size (0.225 = 22.5% for iOS-style)
        padding_percent: Transparent padding around icon (0.08 = 8% on each side)
    """
    # Open the image
    img = Image.open(input_path).convert("RGBA")
    original_width, original_height = img.size
    
    # Calculate padding (8% on each side = 16% total reduction)
    padding = int(min(original_width, original_height) * padding_percent)
    
    # Resize image to leave room for padding
    new_size = original_width - (padding * 2)
    img = img.resize((new_size, new_size), Image.LANCZOS)
    
    width, height = img.size
    
    # Calculate corner radius (iOS uses ~22.5% of icon size)
    radius = int(min(width, height) * radius_percent)
    
    # Create a mask for rounded corners
    mask = Image.new('L', (width, height), 0)
    draw = ImageDraw.Draw(mask)
    
    # Draw rounded rectangle on mask using ellipse for corners
    # Fill the main rectangle
    draw.rectangle([(radius, 0), (width - radius, height)], fill=255)
    draw.rectangle([(0, radius), (width, height - radius)], fill=255)
    
    # Draw circles at corners
    draw.ellipse([(0, 0), (radius * 2, radius * 2)], fill=255)
    draw.ellipse([(width - radius * 2, 0), (width, radius * 2)], fill=255)
    draw.ellipse([(0, height - radius * 2), (radius * 2, height)], fill=255)
    draw.ellipse([(width - radius * 2, height - radius * 2), (width, height)], fill=255)
    
    # Create output image with transparency
    rounded_img = Image.new('RGBA', (width, height), (0, 0, 0, 0))
    rounded_img.paste(img, (0, 0))
    rounded_img.putalpha(mask)
    
    # Create final output with padding (back to original size)
    output = Image.new('RGBA', (original_width, original_height), (0, 0, 0, 0))
    output.paste(rounded_img, (padding, padding))
    
    # Save the result
    output.save(output_path, 'PNG')
    print(f"Created rounded icon with {padding_percent*100:.0f}% padding: {output_path}")


def main():
    """Create rounded-corner icon from source."""
    base_dir = Path(__file__).parent
    input_icon = base_dir / "images" / "icon.png"
    output_icon = base_dir / "images" / "icon_rounded.png"
    
    if not input_icon.exists():
        print(f"Error: Source icon not found: {input_icon}")
        return 1
    
    # Create rounded version
    add_rounded_corners(input_icon, output_icon)
    
    # Also create .icns from the rounded PNG
    print("\nConverting to .icns format...")
    import subprocess
    icns_output = base_dir / "images" / "icon_rounded.icns"
    
    # Use macOS iconutil or sips to convert PNG to ICNS
    try:
        # Create iconset directory
        iconset_dir = base_dir / "images" / "icon_rounded.iconset"
        iconset_dir.mkdir(exist_ok=True)
        
        # Generate required sizes for .icns
        sizes = [16, 32, 64, 128, 256, 512, 1024]
        img = Image.open(output_icon)
        
        for size in sizes:
            resized = img.resize((size, size), Image.LANCZOS)
            resized.save(iconset_dir / f"icon_{size}x{size}.png")
            if size <= 512:  # @2x versions
                resized_2x = img.resize((size * 2, size * 2), Image.LANCZOS)
                resized_2x.save(iconset_dir / f"icon_{size}x{size}@2x.png")
        
        # Convert iconset to icns
        result = subprocess.run(
            ['iconutil', '-c', 'icns', str(iconset_dir), '-o', str(icns_output)],
            capture_output=True,
            text=True
        )
        
        if result.returncode == 0:
            print(f"Created .icns file: {icns_output}")
            # Clean up iconset directory
            import shutil
            shutil.rmtree(iconset_dir)
        else:
            print(f"Warning: Could not create .icns file: {result.stderr}")
    except Exception as e:
        print(f"Warning: Could not create .icns file: {e}")
    
    print("\n✅ Done! Rounded icon created.")
    print(f"   PNG: {output_icon}")
    print(f"   ICNS: {icns_output}")
    print("\nTo use the new icon:")
    print("1. Update SiText.spec to use 'images/icon_rounded.icns'")
    print("2. Rebuild the app with ./build_app.sh")
    
    return 0


if __name__ == "__main__":
    exit(main())
