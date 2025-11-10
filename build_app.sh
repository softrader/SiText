#!/bin/bash
# Build script for creating SiText.app

set -e

echo "🔧 Building SiText.app..."

# Activate virtual environment
source .venv/bin/activate

# Clean previous builds
rm -rf build dist

# Build the app using PyInstaller
pyinstaller SiText.spec

# Fix macOS bundle for Dock compatibility
echo ""
echo "🔧 Fixing macOS app bundle..."
chmod +x dist/SiText.app/Contents/MacOS/SiText
xattr -cr dist/SiText.app
touch dist/SiText.app
/System/Library/Frameworks/CoreServices.framework/Frameworks/LaunchServices.framework/Support/lsregister -f dist/SiText.app

echo ""
echo "✅ Build complete!"
echo ""
echo "📦 Your app is located at: dist/SiText.app"
echo ""
echo "To install:"
echo "  cp -r dist/SiText.app /Applications/"
echo ""
echo "Or run directly:"
echo "  open dist/SiText.app"
