#!/bin/bash
# Build script for creating native ARM64 SiText.app for Apple Silicon (M1/M2/M3)

set -e

echo "🍎 Building SiText.app for ARM64 (Apple Silicon)..."

# Check if we're on ARM64
ARCH=$(uname -m)
if [ "$ARCH" != "arm64" ]; then
    echo "⚠️  Warning: You're running on $ARCH, not ARM64."
    echo "The build will still target ARM64 but may require Rosetta."
fi

# Create ARM64-specific venv if it doesn't exist
if [ ! -d ".venv-arm64" ]; then
    echo "📦 Creating ARM64 virtual environment..."
    /usr/bin/arch -arm64 /usr/local/bin/python3 -m venv .venv-arm64
fi

# Activate ARM64 venv
source .venv-arm64/bin/activate

# Verify we're using ARM64 Python
PYTHON_ARCH=$(python -c "import platform; print(platform.machine())")
echo "🔍 Python architecture: $PYTHON_ARCH"

if [ "$PYTHON_ARCH" != "arm64" ]; then
    echo "❌ Error: Python is not ARM64. Something went wrong with venv creation."
    exit 1
fi

# Install dependencies if needed
if ! python -c "import PyQt6" 2>/dev/null; then
    echo "📚 Installing dependencies..."
    pip install --upgrade pip
    pip install -r requirements.txt
    pip install pyinstaller
fi

# Clean previous builds
rm -rf build dist

# Build the app using PyInstaller with ARM64 target
echo "🔨 Running PyInstaller for ARM64..."
pyinstaller SiTermText.spec

echo "✅ ARM64 build complete!"
echo ""
echo "📦 Your app is located at: dist/SiText.app"
echo ""

# Verify architecture
if [ -f "dist/SiText.app/Contents/MacOS/SiText" ]; then
    echo "🔍 Binary architecture:"
    file dist/SiText.app/Contents/MacOS/SiText
    echo ""
fi

echo "To install:"
echo "  cp -r dist/SiText.app /Applications/"
echo ""
echo "Or run directly:"
echo "  open dist/SiText.app"
