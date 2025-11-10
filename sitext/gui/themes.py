"""Theme definitions for SiText GUI.

Provides a mapping from theme names to stylesheets.
"""
from __future__ import annotations

from typing import Dict

# Base shared tokens could be extracted later; keeping simple for now.

THEMES: Dict[str, str] = {
    # Native macOS theme - uses system colors and native styling
    "macos_native": """
        QMainWindow, QWidget {
            background-color: #f5f5f7;
            color: #1d1d1f;
            font-family: -apple-system, 'SF Pro Text', 'Helvetica Neue', Helvetica, Arial, sans-serif;
            font-size: 13px;
        }
        QListWidget, QTextEdit, QLineEdit {
            background-color: #ffffff;
            color: #1d1d1f;
            border: 1px solid #d2d2d7;
            border-radius: 6px;
            padding: 4px;
            selection-background-color: #007aff;
            selection-color: #ffffff;
        }
        QListWidget::item {
            padding: 6px 8px;
            border-radius: 4px;
        }
        QListWidget::item:hover {
            background-color: #f0f0f5;
        }
        QListWidget::item:selected {
            background-color: #007aff;
            color: #ffffff;
        }
        QPushButton {
            background-color: #ffffff;
            color: #007aff;
            border: 1px solid #d2d2d7;
            border-radius: 6px;
            padding: 6px 16px;
            font-weight: 500;
        }
        QPushButton:hover {
            background-color: #f5f5f7;
            border-color: #007aff;
        }
        QPushButton:pressed {
            background-color: #007aff;
            color: #ffffff;
        }
        QStatusBar {
            background-color: #f5f5f7;
            color: #86868b;
            border-top: 1px solid #d2d2d7;
        }
        QSplitter::handle {
            background-color: #d2d2d7;
            width: 1px;
            height: 1px;
        }
        QDialog {
            background-color: #f5f5f7;
            color: #1d1d1f;
        }
        QComboBox {
            background-color: #ffffff;
            border: 1px solid #d2d2d7;
            border-radius: 6px;
            padding: 5px 10px;
            color: #1d1d1f;
        }
        QComboBox:hover {
            border-color: #007aff;
        }
        QComboBox::drop-down {
            border: none;
        }
        QMessageBox {
            background-color: #f5f5f7;
        }
        /* macOS-style scrollbars - thin, rounded, minimal */
        QScrollBar:vertical {
            background-color: transparent;
            width: 10px;
            margin: 0px;
        }
        QScrollBar::handle:vertical {
            background-color: rgba(0, 0, 0, 0.25);
            border-radius: 4px;
            min-height: 30px;
            margin: 2px 3px;
        }
        QScrollBar::handle:vertical:hover {
            background-color: rgba(0, 0, 0, 0.4);
        }
        QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
            height: 0px;
            background: transparent;
        }
        QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical {
            background: transparent;
        }
        QScrollBar:horizontal {
            background-color: transparent;
            height: 10px;
            margin: 0px;
        }
        QScrollBar::handle:horizontal {
            background-color: rgba(0, 0, 0, 0.25);
            border-radius: 4px;
            min-width: 30px;
            margin: 3px 2px;
        }
        QScrollBar::handle:horizontal:hover {
            background-color: rgba(0, 0, 0, 0.4);
        }
        QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {
            width: 0px;
            background: transparent;
        }
        QScrollBar::add-page:horizontal, QScrollBar::sub-page:horizontal {
            background: transparent;
        }
    """,
    # Existing default dark green terminal style (key preserved as 'dark' for backward compat)
    "dark": """
        QMainWindow, QWidget { background-color: #000000; color: #00ff00; font-family: 'Monaco', 'Menlo', 'Courier New', monospace; font-size: 13px; }
        QListWidget, QTextEdit, QLineEdit { background-color: #000000; color: #00ff00; border: 1px solid #00ff00; selection-background-color: #00ff00; selection-color: #000000; }
        QListWidget::item:hover { background-color: #003300; }
        QListWidget::item:selected { background-color: #00ff00; color: #000000; }
        QPushButton { background-color: #000000; color: #00ff00; border: 1px solid #00ff00; padding: 5px 15px; }
        QPushButton:hover { background-color: #003300; }
        QPushButton:pressed { background-color: #00ff00; color: #000000; }
        QStatusBar { background-color: #000000; color: #00ff00; border-top: 1px solid #00ff00; }
        QSplitter::handle { background-color: #00ff00; width: 2px; height: 2px; }
        QDialog { background-color: #000000; color: #00ff00; }
    """,
    # Light theme
    "light": """
        QMainWindow, QWidget { background-color: #f5f5f5; color: #222222; font-family: 'Menlo', 'Monaco', 'Courier New', monospace; font-size: 13px; }
        QListWidget, QTextEdit, QLineEdit { background-color: #ffffff; color: #222222; border: 1px solid #999999; selection-background-color: #3366ff; selection-color: #ffffff; }
        QListWidget::item:hover { background-color: #e6f0ff; }
        QListWidget::item:selected { background-color: #3366ff; color: #ffffff; }
        QPushButton { background-color: #ffffff; color: #222222; border: 1px solid #888888; padding: 5px 15px; }
        QPushButton:hover { background-color: #e6e6e6; }
        QPushButton:pressed { background-color: #3366ff; color: #ffffff; }
        QStatusBar { background-color: #f0f0f0; color: #222222; border-top: 1px solid #cccccc; }
        QSplitter::handle { background-color: #cccccc; width: 2px; height: 2px; }
        QDialog { background-color: #ffffff; color: #222222; }
    """,
    # Solarized Dark
    "solarized_dark": """
        QMainWindow, QWidget { background-color: #002b36; color: #93a1a1; font-family: 'Menlo', 'Monaco', 'Courier New', monospace; font-size: 13px; }
        QListWidget, QTextEdit, QLineEdit { background-color: #073642; color: #93a1a1; border: 1px solid #586e75; selection-background-color: #268bd2; selection-color: #fdf6e3; }
        QListWidget::item:hover { background-color: #0d4450; }
        QListWidget::item:selected { background-color: #268bd2; color: #fdf6e3; }
        QPushButton { background-color: #073642; color: #93a1a1; border: 1px solid #586e75; padding: 5px 15px; }
        QPushButton:hover { background-color: #0d4450; }
        QPushButton:pressed { background-color: #268bd2; color: #fdf6e3; }
        QStatusBar { background-color: #002b36; color: #93a1a1; border-top: 1px solid #586e75; }
        QSplitter::handle { background-color: #586e75; width: 2px; height: 2px; }
        QDialog { background-color: #002b36; color: #93a1a1; }
    """,
    # Solarized Light
    "solarized_light": """
        QMainWindow, QWidget { background-color: #fdf6e3; color: #657b83; font-family: 'Menlo', 'Monaco', 'Courier New', monospace; font-size: 13px; }
        QListWidget, QTextEdit, QLineEdit { background-color: #eee8d5; color: #586e75; border: 1px solid #93a1a1; selection-background-color: #268bd2; selection-color: #fdf6e3; }
        QListWidget::item:hover { background-color: #e4ddc8; }
        QListWidget::item:selected { background-color: #268bd2; color: #fdf6e3; }
        QPushButton { background-color: #eee8d5; color: #586e75; border: 1px solid #93a1a1; padding: 5px 15px; }
        QPushButton:hover { background-color: #e4ddc8; }
        QPushButton:pressed { background-color: #268bd2; color: #fdf6e3; }
        QStatusBar { background-color: #fdf6e3; color: #657b83; border-top: 1px solid #93a1a1; }
        QSplitter::handle { background-color: #93a1a1; width: 2px; height: 2px; }
        QDialog { background-color: #fdf6e3; color: #657b83; }
    """,
    # High contrast
    "high_contrast": """
        QMainWindow, QWidget { background-color: #000000; color: #ffffff; font-family: 'Menlo', 'Monaco', 'Courier New', monospace; font-size: 14px; }
        QListWidget, QTextEdit, QLineEdit { background-color: #000000; color: #ffffff; border: 2px solid #ffffff; selection-background-color: #ffffff; selection-color: #000000; }
        QListWidget::item:hover { background-color: #222222; }
        QListWidget::item:selected { background-color: #ffffff; color: #000000; }
        QPushButton { background-color: #000000; color: #ffffff; border: 2px solid #ffffff; padding: 6px 18px; }
        QPushButton:hover { background-color: #222222; }
        QPushButton:pressed { background-color: #ffffff; color: #000000; }
        QStatusBar { background-color: #000000; color: #ffffff; border-top: 2px solid #ffffff; }
        QSplitter::handle { background-color: #ffffff; width: 2px; height: 2px; }
        QDialog { background-color: #000000; color: #ffffff; }
    """,
}


def available_themes() -> list[str]:
    return list(THEMES.keys())


def get_stylesheet(theme: str) -> str:
    # Fallback to dark if unknown
    return THEMES.get(theme, THEMES["dark"])  # type: ignore[index]
