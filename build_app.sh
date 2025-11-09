#!/bin/bash
# Build script for creating SiTermText.app

set -e

echo "🔧 Building SiTermText.app..."

# Activate virtual environment
source .venv/bin/activate

# Clean previous builds
rm -rf build dist

# Build the app using PyInstaller
pyinstaller SiTermText.spec

echo "✅ Build complete!"
echo ""
echo "📦 Your app is located at: dist/SiTermText.app"
echo ""
echo "To install:"
echo "  cp -r dist/SiTermText.app /Applications/"
echo ""
echo "Or run directly:"
echo "  open dist/SiTermText.app"
