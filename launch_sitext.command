#!/bin/bash
# Launcher script for SiText
# This opens Terminal and runs the app

# Get the directory where this script is located
DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

# Run the app from the .app bundle
exec "$DIR/dist/SiText.app/Contents/MacOS/SiText"
