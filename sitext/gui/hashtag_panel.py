"""Hashtag panel widget for displaying tags from notes."""

import re
from collections import Counter
from pathlib import Path

from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtWidgets import QLabel, QListWidget, QListWidgetItem, QVBoxLayout, QWidget


class HashtagPanel(QWidget):
    """Widget for displaying hashtags with frequency counts."""

    hashtag_selected = pyqtSignal(str)

    def __init__(self, notes_directory: Path, parent=None):
        super().__init__(parent)
        self.notes_directory = notes_directory
        self.hashtags = {}

        layout = QVBoxLayout()
        layout.setContentsMargins(5, 5, 5, 5)
        layout.setSpacing(5)

        # Title
        title = QLabel("Tags")
        title.setStyleSheet("font-weight: bold; padding: 5px;")
        layout.addWidget(title)

        # Hashtag list
        self.hashtag_list = QListWidget()
        self.hashtag_list.itemDoubleClicked.connect(self._on_item_double_clicked)
        self.hashtag_list.itemActivated.connect(self._on_item_activated)
        self.hashtag_list.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
        layout.addWidget(self.hashtag_list)

        self.setLayout(layout)

        # Load hashtags
        self.refresh_hashtags()

    def set_notes_directory(self, directory: Path):
        """Change the notes directory."""
        self.notes_directory = directory
        self.refresh_hashtags()

    def refresh_hashtags(self):
        """Scan all files and extract hashtags."""
        if not self.notes_directory.exists():
            self.hashtags = {}
            self._update_display()
            return

        # Extract hashtags from all .md files recursively (including subfolders)
        tag_counter = Counter()
        hashtag_pattern = re.compile(r"#([a-zA-Z0-9_]+)")

        for md_file in self.notes_directory.glob("**/*.md"):
            try:
                content = md_file.read_text(encoding="utf-8")
                tags = hashtag_pattern.findall(content)
                tag_counter.update(tags)
            except (OSError, UnicodeDecodeError):
                continue

        # Convert to dict sorted by frequency
        self.hashtags = dict(tag_counter.most_common())
        self._update_display()

    def _update_display(self):
        """Update the list widget with hashtags."""
        self.hashtag_list.clear()
        
        if not self.hashtags:
            item = QListWidgetItem("No hashtags found")
            item.setFlags(Qt.ItemFlag.NoItemFlags)
            self.hashtag_list.addItem(item)
            return
        
        for tag, count in self.hashtags.items():
            item = QListWidgetItem(f"#{tag} ({count})")
            item.setData(Qt.ItemDataRole.UserRole, tag)
            self.hashtag_list.addItem(item)

    def _on_item_double_clicked(self, item: QListWidgetItem):
        """Handle double-click on hashtag item."""
        tag = item.data(Qt.ItemDataRole.UserRole)
        if tag:
            self.hashtag_selected.emit(tag)

    def _on_item_activated(self, item: QListWidgetItem):
        """Handle Enter key on hashtag item."""
        tag = item.data(Qt.ItemDataRole.UserRole)
        if tag:
            self.hashtag_selected.emit(tag)

    def keyPressEvent(self, event):
        """Handle key presses for Enter key navigation."""
        from PyQt6.QtCore import Qt
        
        # If hashtag list has focus and Enter is pressed
        if self.hashtag_list.hasFocus() and event.key() in (Qt.Key.Key_Return, Qt.Key.Key_Enter):
            current_item = self.hashtag_list.currentItem()
            if current_item:
                tag = current_item.data(Qt.ItemDataRole.UserRole)
                if tag:
                    self.hashtag_selected.emit(tag)
                    event.accept()
                    return
        
        # Otherwise, let the default handler process it
        super().keyPressEvent(event)
