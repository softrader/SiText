#!/bin/bash
# Installation script for SiTermText
# This creates a symlink so you can run 'sitermtext' from anywhere

set -e

# Colors for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${BLUE}SiTermText Installer${NC}"
echo "===================="
echo ""

# Get the directory where this script is located
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
APP_PATH="$SCRIPT_DIR/dist/SiTermText.app/Contents/MacOS/SiTermText"

# Check if the app exists
if [ ! -f "$APP_PATH" ]; then
    echo -e "${RED}Error: SiTermText.app not found!${NC}"
    echo "Please run ./build_app.sh first to build the application."
    exit 1
fi

# Determine install location
INSTALL_DIR="/usr/local/bin"
SYMLINK_PATH="$INSTALL_DIR/sitermtext"

# Check if /usr/local/bin exists, create if needed
if [ ! -d "$INSTALL_DIR" ]; then
    echo "Creating $INSTALL_DIR directory..."
    sudo mkdir -p "$INSTALL_DIR"
fi

# Remove existing symlink if present
if [ -L "$SYMLINK_PATH" ] || [ -f "$SYMLINK_PATH" ]; then
    echo "Removing existing installation..."
    sudo rm -f "$SYMLINK_PATH"
fi

# Create symlink
echo "Installing sitermtext to $INSTALL_DIR..."
sudo ln -s "$APP_PATH" "$SYMLINK_PATH"

# Verify installation
if [ -L "$SYMLINK_PATH" ]; then
    echo ""
    echo -e "${GREEN}✓ Installation successful!${NC}"
    echo ""
    echo "You can now run SiTermText from anywhere by typing:"
    echo -e "  ${BLUE}sitermtext${NC}"
    echo ""
    echo "To uninstall, run:"
    echo -e "  ${BLUE}sudo rm $SYMLINK_PATH${NC}"
else
    echo -e "${RED}✗ Installation failed${NC}"
    exit 1
fi
