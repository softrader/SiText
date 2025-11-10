#!/bin/bash
# Fix macOS app bundle to make it dock-compatible

APP_PATH="dist/SiText.app"

if [ ! -d "$APP_PATH" ]; then
    echo "Error: App not found at $APP_PATH"
    echo "Build the app first with ./build_app.sh"
    exit 1
fi

echo "Fixing SiText.app bundle for macOS compatibility..."

# Ensure proper permissions
chmod +x "$APP_PATH/Contents/MacOS/SiText"

# Clear extended attributes that might cause issues
xattr -cr "$APP_PATH"

# Force macOS to refresh the app database
touch "$APP_PATH"

# Register the app with Launch Services
/System/Library/Frameworks/CoreServices.framework/Frameworks/LaunchServices.framework/Support/lsregister -f "$APP_PATH"

echo "✅ Fixed! The app should now be draggable to the Dock."
echo "   If it's already in /Applications, you may need to:"
echo "   1. Remove it from /Applications"
echo "   2. Copy the fixed version from dist/SiText.app"
echo "   3. Try dragging to Dock again"
