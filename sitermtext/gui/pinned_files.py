"""Pinned files widget.

Displays a list of pinned files with a small header label. Allows unpin via
context menu and emits signals for selection/unpin requests.
"""

from pathlib import Path
from typing import Optional

from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtWidgets import (
    QLabel,
    QListWidget,
    QListWidgetItem,
    QMenu,
    QVBoxLayout,
    QWidget,
)


class PinnedFilesWidget(QWidget):
    """Widget showing pinned files for the current notes directory."""

    pinned_selected = pyqtSignal(Path)
    unpin_requested = pyqtSignal(Path)

    def __init__(self, notes_directory: Path, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self.notes_directory = notes_directory
        self._pins: list[str] = []  # filenames with extension

        layout = QVBoxLayout(self)
        layout.setContentsMargins(5, 5, 0, 0)
        layout.setSpacing(2)

        self.header = QLabel("Pinned")
        self.header.setObjectName("PinnedHeader")
        self.header.setStyleSheet("font-weight: bold; padding-left: 2px;")
        layout.addWidget(self.header)

        self.list = QListWidget()
        self.list.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.list.customContextMenuRequested.connect(self._show_context_menu)
        self.list.itemActivated.connect(self._on_item_activated)
        layout.addWidget(self.list)

        self.setLayout(layout)

    def set_notes_directory(self, notes_directory: Path) -> None:
        self.notes_directory = notes_directory
        # Keep pins list; caller should refresh with load_pins

    def load_pins(self, filenames: list[str]) -> None:
        """Load and display provided list of pinned filenames.

        Args:
            filenames: Filenames with extension relative to notes dir
        """
        self._pins = list(dict.fromkeys(filenames))
        self._refresh()

    def _refresh(self) -> None:
        self.list.clear()
        if not self._pins:
            placeholder = QListWidgetItem("No pinned files")
            placeholder.setFlags(Qt.ItemFlag.NoItemFlags)
            self.list.addItem(placeholder)
            return
        for name in self._pins:
            path = self.notes_directory / name
            item = QListWidgetItem(path.stem)
            item.setData(Qt.ItemDataRole.UserRole, path)
            self.list.addItem(item)

    def _on_item_activated(self, item: QListWidgetItem) -> None:
        path = item.data(Qt.ItemDataRole.UserRole)
        if isinstance(path, Path):
            self.pinned_selected.emit(path)

    def _show_context_menu(self, pos) -> None:
        item = self.list.itemAt(pos)
        if not item:
            return
        path = item.data(Qt.ItemDataRole.UserRole)
        if not isinstance(path, Path):
            return
        menu = QMenu(self)
        unpin_action = menu.addAction("Unpin")
        action = menu.exec(self.list.mapToGlobal(pos))
        if action == unpin_action:
            self.unpin_requested.emit(path)
