"""Main entry point for SiText GUI application."""

import argparse
import sys
from pathlib import Path

from PyQt6.QtWidgets import QApplication

from sitext.config import Config
from sitext.gui.main_window import MainWindow


def run() -> None:
    """Run the SiText application."""
    parser = argparse.ArgumentParser(description="SiText - Note-Taking App")
    parser.add_argument(
        "--notes-dir",
        type=str,
        help="Directory containing markdown notes",
    )
    args = parser.parse_args()

    # Load configuration
    config = Config()

    # Override notes directory if provided via CLI
    if args.notes_dir:
        config.set("notes_directory", args.notes_dir)

    # Create Qt application
    app = QApplication(sys.argv)
    app.setApplicationName("SiText")
    app.setOrganizationName("SiText")

    # Create and show main window
    window = MainWindow(config)
    window.show()

    # Run event loop
    sys.exit(app.exec())


if __name__ == "__main__":
    run()
