"""File list widget for browsing and searching markdown files.

Adds fast content search with background indexing and debounced queries.
"""

import re
from pathlib import Path
from typing import Optional

from PyQt6.QtCore import Qt, pyqtSignal, QThread, QTimer
from PyQt6.QtWidgets import (
    QLineEdit,
    QListWidget,
    QListWidgetItem,
    QMenu,
    QVBoxLayout,
    QWidget,
)


class ContentIndexer(QThread):
    """Background thread that builds a simple content index.

    Reads all markdown files once and caches lowercased contents in memory to
    make subsequent content searches fast (no disk I/O during search).
    """

    finished = pyqtSignal(object)  # emits dict[Path, str]

    def __init__(self, files: list[Path]):
        super().__init__()
        self._files = files

    def run(self):
        index: dict[Path, str] = {}
        for md_file in self._files:
            if self.isInterruptionRequested():
                break
            try:
                # Read and lowercase once for fast substring checks
                content = md_file.read_text(encoding="utf-8", errors="ignore").lower()
                index[md_file] = content
            except OSError:
                continue
        self.finished.emit(index)


class FileListWidget(QWidget):
    """Widget for displaying and filtering markdown files."""

    file_selected = pyqtSignal(Path)
    file_deleted = pyqtSignal()
    pin_requested = pyqtSignal(Path)
    unpin_requested = pyqtSignal(Path)

    def __init__(self, notes_directory: Path, parent=None):
        super().__init__(parent)
        self.notes_directory = notes_directory
        self.all_files = []
        self._order_mode: str = "alphabetical"  # or 'last_modified'
        # Content search index built in the background
        self._content_index: dict[Path, str] = {}
        self._index_thread: Optional[ContentIndexer] = None
        self._index_ready: bool = False
        self._pinned_names: set[str] = set()  # filenames with extension
        # Debounce timer for search input to avoid excessive work
        self._search_timer = QTimer(self)
        self._search_timer.setSingleShot(True)
        self._search_timer.setInterval(250)
        self._search_timer.timeout.connect(self._filter_files)

        layout = QVBoxLayout()
        layout.setContentsMargins(5, 5, 5, 5)
        layout.setSpacing(5)

        # Search input
        self.search_input = QLineEdit()
        self._update_search_placeholder()
        self.search_input.textChanged.connect(lambda: self._search_timer.start())
        self.search_input.returnPressed.connect(self._create_or_open_file)
        self.search_input.installEventFilter(self)
        layout.addWidget(self.search_input)

        # File list
        self.file_list = QListWidget()
        self.file_list.setSelectionMode(QListWidget.SelectionMode.ExtendedSelection)  # Enable multi-select
        self.file_list.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.file_list.customContextMenuRequested.connect(self._show_context_menu)
        self.file_list.itemDoubleClicked.connect(self._on_item_double_clicked)
        self.file_list.itemActivated.connect(self._on_item_activated)
        self.file_list.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
        layout.addWidget(self.file_list)

        self.setLayout(layout)

        # Load files
        self.refresh_files()

    def set_notes_directory(self, directory: Path):
        """Change the notes directory."""
        self.notes_directory = directory
        self.refresh_files()

    def set_pinned_names(self, names: set[str]):
        """Provide current pinned filenames (with extension) to drive context menu state."""
        self._pinned_names = set(names)

    def set_order(self, mode: str):
        """Set file ordering mode.

        Args:
            mode: 'alphabetical' or 'last_modified'
        """
        if mode not in ("alphabetical", "last_modified"):
            mode = "alphabetical"
        if self._order_mode != mode:
            self._order_mode = mode
            self.refresh_files()

    def refresh_files(self):
        """Scan notes directory and update file list."""
        if not self.notes_directory.exists():
            self.all_files = []
            self._update_display([])
            return

        # Get all .md files recursively (including subfolders) and order
        files = list(self.notes_directory.glob("**/*.md"))
        if self._order_mode == "last_modified":
            files.sort(key=lambda p: p.stat().st_mtime, reverse=True)
        else:
            # Sort by relative path for better folder grouping
            files.sort(key=lambda p: p.relative_to(self.notes_directory).as_posix().lower())
        self.all_files = files
        # (Re)build content index in the background for fast content searches
        self._start_indexing()
        self._filter_files()

    def _update_search_placeholder(self) -> None:
        """Update search input placeholder."""
        self.search_input.setPlaceholderText("Search files or #hashtag...")

    def _on_vector_index_error(self, error_msg: str) -> None:
        """Placeholder for removed AI functionality.

        Args:
            error_msg: Error message
        """
        pass  # Removed AI functionality

    def _start_indexing(self):
        """Start background indexing of file contents."""
        # Stop previous indexer if running (request interruption & wait briefly)
        if self._index_thread and self._index_thread.isRunning():
            try:
                self._index_thread.requestInterruption()
                self._index_thread.wait(200)
            except Exception:
                pass
        self._index_ready = False
        self._content_index.clear()
        self._index_thread = ContentIndexer(self.all_files)
        self._index_thread.finished.connect(self._on_index_finished)
        self._index_thread.start()

    def _on_index_finished(self, index: dict):
        """Handle completion of background indexing."""
        # Index arrives on the main thread via Qt signal
        self._content_index = index or {}
        self._index_ready = True
        # Re-run current filter to pull in content matches
        self._filter_files()

    def _filter_files(self):
        """Apply search filter to file list (filename + content)."""
        query = self.search_input.text().strip()

        # Empty -> show all
        if not query:
            self._update_display(self.all_files)
            return

        # Hashtag mode -> use content scanning for tags only
        if query.startswith('#') or query.startswith('£'):
            hashtag = query[1:]
            filtered = self._filter_by_hashtag(hashtag)
            self._update_display(filtered)
            return

        # Regular keyword search
        query_lower = query.lower()
        results: list[Path] = []
        seen: set[Path] = set()

        # 1) Filename and path matches (fast)
        for f in self.all_files:
            # Match against full relative path (e.g., "projects/foo")
            rel_path = f.relative_to(self.notes_directory)
            rel_str = str(rel_path)[:-3] if str(rel_path).endswith('.md') else str(rel_path)
            if query_lower in rel_str.lower():
                results.append(f)
                seen.add(f)

        # 2) Content matches (debounced and uses in-memory index)
        # Guard: minimum 2 chars to avoid too-broad searches; cap results
        MAX_CONTENT_RESULTS = 300
        if len(query_lower) >= 2 and self._index_ready and self._content_index:
            count = 0
            for path, content in self._content_index.items():
                if path in seen:
                    continue
                # Substring match in lowered content
                if query_lower in content:
                    results.append(path)
                    seen.add(path)
                    count += 1
                    if count >= MAX_CONTENT_RESULTS:
                        break

        # If index still building and no filename matches, keep UI responsive
        if not results and len(query) >= 2 and not self._index_ready:
            # Show path-only partial results while indexing completes
            path_only = []
            for f in self.all_files:
                rel_path = f.relative_to(self.notes_directory)
                rel_str = str(rel_path)[:-3] if str(rel_path).endswith('.md') else str(rel_path)
                if query in rel_str.lower():
                    path_only.append(f)
            if path_only:
                self._update_display(path_only)
                return
            # Show placeholder when nothing yet and index building
            self.file_list.clear()
            item = QListWidgetItem("Indexing content...")
            item.setFlags(Qt.ItemFlag.NoItemFlags)
            self.file_list.addItem(item)
            return

        self._update_display(results)

    def _show_context_menu(self, pos):
        item = self.file_list.itemAt(pos)
        if not item:
            return
        path: Path = item.data(Qt.ItemDataRole.UserRole)
        if not isinstance(path, Path):
            return
        menu = QMenu(self)
        filename = path.name
        is_pinned = filename in self._pinned_names
        action_text = "Unpin" if is_pinned else "Pin"
        toggle_action = menu.addAction(action_text)
        chosen = menu.exec(self.file_list.mapToGlobal(pos))
        if chosen == toggle_action:
            if is_pinned:
                self.unpin_requested.emit(path)
            else:
                self.pin_requested.emit(path)

    def _filter_by_hashtag(self, hashtag: str) -> list[Path]:
        """Filter files that contain a specific hashtag.

        Uses in-memory content index when available to avoid disk I/O.
        """
        matching_files: list[Path] = []
        hashtag_pattern = re.compile(r'#([a-zA-Z0-9_]+)')

        if self._index_ready and self._content_index:
            for md_file, content in self._content_index.items():
                tags = hashtag_pattern.findall(content)
                if any(tag.lower() == hashtag.lower() for tag in tags):
                    matching_files.append(md_file)
            return [f for f in self.all_files if f in matching_files]

        # Fallback to on-demand reads
        for md_file in self.all_files:
            try:
                content = md_file.read_text(encoding='utf-8')
                tags = hashtag_pattern.findall(content)
                if any(tag.lower() == hashtag.lower() for tag in tags):
                    matching_files.append(md_file)
            except (OSError, UnicodeDecodeError):
                continue
        return matching_files

    def _update_display(self, files: list[Path]):
        """Update the list widget with filtered files."""
        self.file_list.clear()

        if not files:
            item = QListWidgetItem("No files found")
            item.setFlags(Qt.ItemFlag.NoItemFlags)
            self.file_list.addItem(item)
            return

        # Stable-partition: pinned first (only if present in 'files'), then others
        pinned_names = self._pinned_names
        pinned: list[Path] = []
        others: list[Path] = []
        for p in files:
            (pinned if p.name in pinned_names else others).append(p)

        def add_items(paths: list[Path], is_pinned: bool = False):
            for file_path in paths:
                # Show relative path from notes directory (e.g., "projects/foo" or "bar")
                rel_path = file_path.relative_to(self.notes_directory)
                # Remove .md extension for cleaner display
                display_name = str(rel_path)[:-3] if str(rel_path).endswith('.md') else str(rel_path)
                display = f"📌 {display_name}" if is_pinned else display_name
                item = QListWidgetItem(display)
                item.setData(Qt.ItemDataRole.UserRole, file_path)
                self.file_list.addItem(item)

        add_items(pinned, is_pinned=True)
        add_items(others, is_pinned=False)

    def _on_item_double_clicked(self, item: QListWidgetItem):
        """Handle double-click on file item."""
        if not item:
            return
        file_path = item.data(Qt.ItemDataRole.UserRole) if item else None
        if file_path:
            self.file_selected.emit(file_path)

    def _on_item_activated(self, item: QListWidgetItem):
        """Handle Enter key on file item."""
        if not item:
            return
        file_path = item.data(Qt.ItemDataRole.UserRole) if item else None
        if file_path:
            self.file_selected.emit(file_path)

    def _create_or_open_file(self):
        """Create or open a file based on search text."""
        search_text = self.search_input.text().strip()
        if not search_text:
            # If search is empty and there's a selected item, open it
            current_item = self.file_list.currentItem()
            if current_item:
                file_path = current_item.data(Qt.ItemDataRole.UserRole)
                if file_path:
                    self.file_selected.emit(file_path)
            return

        # Support folder paths (e.g., "projects/foo" or just "foo")
        # Add .md extension if not present
        filename = search_text if search_text.endswith(".md") else f"{search_text}.md"
        file_path = self.notes_directory / filename

        self.file_selected.emit(file_path)
        self.search_input.clear()

    def eventFilter(self, obj, event):
        """Filter events for the search input."""
        from PyQt6.QtCore import QEvent, Qt
        from PyQt6.QtGui import QKeyEvent
        
        # Intercept key events on the search input
        if obj == self.search_input and event.type() == QEvent.Type.KeyPress:
            # Down arrow - move to file list
            if event.key() == Qt.Key.Key_Down:
                if self.file_list.count() > 0:
                    self.file_list.setFocus()
                    self.file_list.setCurrentRow(0)
                    return True
            # Up arrow - move to file list (last item)
            elif event.key() == Qt.Key.Key_Up:
                if self.file_list.count() > 0:
                    self.file_list.setFocus()
                    self.file_list.setCurrentRow(self.file_list.count() - 1)
                    return True
        
        return super().eventFilter(obj, event)

    def keyPressEvent(self, event):
        """Handle key presses for Enter and Delete in file list."""
        from PyQt6.QtCore import Qt
        from PyQt6.QtWidgets import QMessageBox
        
        # If file list has focus and Enter is pressed
        if self.file_list.hasFocus() and event.key() in (Qt.Key.Key_Return, Qt.Key.Key_Enter):
            current_item = self.file_list.currentItem()
            if current_item:
                file_path = current_item.data(Qt.ItemDataRole.UserRole)
                if file_path:
                    self.file_selected.emit(file_path)
                    event.accept()
                    return
        
        # If file list has focus and Backspace/Delete is pressed
        if self.file_list.hasFocus() and event.key() in (Qt.Key.Key_Backspace, Qt.Key.Key_Delete):
            selected_items = self.file_list.selectedItems()
            if selected_items:
                # Get all file paths from selected items
                file_paths = []
                for item in selected_items:
                    file_path = item.data(Qt.ItemDataRole.UserRole)
                    if file_path and isinstance(file_path, Path) and file_path.exists():
                        file_paths.append(file_path)

                if not file_paths:
                    event.accept()
                    return

                # Confirm deletion
                if len(file_paths) == 1:
                    message = f"Are you sure you want to delete '{file_paths[0].name}'?"
                else:
                    message = f"Are you sure you want to delete {len(file_paths)} files?"

                msg_box = QMessageBox(
                    QMessageBox.Icon.Question,
                    "Delete File" if len(file_paths) == 1 else "Delete Files",
                    message,
                    QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                    self
                )
                # Set Yes as the default button (Enter will activate it)
                msg_box.setDefaultButton(QMessageBox.StandardButton.Yes)
                reply = msg_box.exec()

                if reply == QMessageBox.StandardButton.Yes:
                    failed_deletions = []
                    for file_path in file_paths:
                        try:
                            file_path.unlink()
                        except OSError as e:
                            failed_deletions.append(f"{file_path.name}: {e}")

                    # Refresh the file list
                    self.refresh_files()
                    # Emit signal to close files if they're open in editor
                    self.file_deleted.emit()

                    # Show errors if any
                    if failed_deletions:
                        QMessageBox.warning(
                            self,
                            "Delete Failed",
                            f"Could not delete some files:\n" + "\n".join(failed_deletions)
                        )

                event.accept()
                return
        
        # Otherwise, let the default handler process it
        super().keyPressEvent(event)

    # --- Lifecycle management ---
    def shutdown(self):
        """Stop background indexing threads safely."""
        # Stop content indexer
        if self._index_thread and self._index_thread.isRunning():
            try:
                self._index_thread.requestInterruption()
                self._index_thread.wait(500)
            except Exception:
                pass

    def __del__(self):  # noqa: D401 (simple cleanup)
        self.shutdown()
