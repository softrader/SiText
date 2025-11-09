"""Main window for SiText GUI application."""

import re
from pathlib import Path
from typing import Optional

from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QKeySequence, QShortcut
from PyQt6.QtWidgets import (
    QDialog,
    QComboBox,
    QFileDialog,
    QHBoxLayout,
    QLabel,
    QListWidget,
    QListWidgetItem,
    QLineEdit,
    QMainWindow,
    QMessageBox,
    QPushButton,
    QSplitter,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from sitermtext.config import Config
from sitermtext.gui.editor import MarkdownEditor
from sitermtext.gui.file_list import FileListWidget
from sitermtext.gui.hashtag_panel import HashtagPanel
from sitermtext.gui.themes import available_themes, get_stylesheet


class HowToDialog(QDialog):
    """Dialog showing how to use SiText features."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("How To Use SiText")
        self.setModal(False)
        self.resize(700, 600)

        layout = QVBoxLayout()

        # Create scrollable text area
        text_edit = QTextEdit()
        text_edit.setReadOnly(True)
        text_edit.setMarkdown(self._get_help_content())
        layout.addWidget(text_edit)

        # Close button
        close_btn = QPushButton("Close")
        close_btn.clicked.connect(self.close)
        layout.addWidget(close_btn)

        self.setLayout(layout)

    def _get_help_content(self) -> str:
        """Return the help content in Markdown format."""
        return """# SiText - How To Guide

## Core Features

### Creating and Opening Notes
- **Create a new note**: Type a filename in the search box and press Enter
- **Open a note**: Double-click a file in the list, or select and press Enter
- **Search files**: Type in the search box to filter by filename, folder, or content

### Wiki-Links
- **Create a link**: Type `[[note name]]` to link to another note
- **Navigate**: Click on any `[[wiki-link]]` to open that note
- **Create on click**: Clicking a non-existent wiki-link creates the file
- **Autocomplete**: Type `[[` and select from existing files with arrow keys + Enter
- **Folder paths**: Use `[[folder/note]]` for files in subfolders

### Hashtags
- **Add tags**: Type `#tagname` anywhere in your note
- **View all tags**: See the hashtag panel on the right (shows frequency)
- **Filter by tag**: Click a hashtag in the panel, or click one in your note
- **Search tags**: Type `#tagname` in the search box
- **Autocomplete**: Type `#` and select from existing hashtags with arrow keys + Enter

### URLs and Links
- **Markdown links**: `[text](https://example.com)` - displayed in blue
- **Bare URLs**: `https://example.com` - displayed in blue
- **Open URL**: Shift+Click on any URL to open in browser

### File Organization

#### Subfolders
- **Nested structure**: Place `.md` files in subfolders to organize
- **Search folders**: Type folder name to filter (e.g., "projects")
- **Display**: Files shown as `folder/filename` in the list
- **Preservation**: File locations never change - structure is preserved

#### Pinning
- **Pin a file**: Right-click → Pin, or use the 📌 button in the editor
- **Pinned location**: Pinned files always appear at top of list
- **Unpin**: Right-click → Unpin, or toggle the 📌 button

### Editing

#### Markdown Syntax Highlighting
- **Headers**: `# Header` - green, bold
- **Bold**: `**text**` or `__text__`
- **Italic**: `*text*` or `_text*`
- **Code**: `` `code` `` - monospace, yellow-green
- **Wiki-links**: `[[link]]` - purple, underlined
- **URLs**: `https://...` or `[text](url)` - blue, underlined
- **Hashtags**: `#tag` - orange/yellow, bold

#### Auto-save
- Files automatically save 2 seconds after you stop typing
- Modified files show `*` in the title

### Multi-Select and Deletion
- **Select multiple**: Shift+Up/Down to select multiple files
- **Delete files**: Select file(s) and press Backspace or Delete
- **Confirmation**: Always asks before deleting

### Export
- **Export to PDF**: File → Export to PDF (or Ctrl+E)
- **Formatted output**: Markdown is converted to styled PDF with proper formatting
- **Preserves structure**: Headers, lists, code blocks, links all formatted correctly

### Keyboard Shortcuts
- **Escape**: Focus search box
- **Cmd+J / Ctrl+J**: Follow wiki-link at cursor
- **Cmd+, / Ctrl+,**: Open settings
- **Ctrl+E**: Export current note to PDF
- **Enter** (in search): Open selected file or create new file
- **Backspace/Delete** (in file list): Delete selected file(s)
- **Shift+Click** (on URL): Open URL in browser

### Themes
- **Available themes**: macOS Native, Light, Dark, Solarized Light, Solarized Dark, High Contrast
- **Change theme**: Settings → Theme → Select and Apply
- **Adaptive syntax**: Syntax colors adjust for each theme
- **macOS Native**: Modern Mac-style interface with system colors (default)

### File Ordering
- **Alphabetical**: Files sorted A-Z (default)
- **Last Modified**: Most recently edited files first
- **Change order**: Settings → File Order

### Graph View
- **Open graph**: View → Graph (if available)
- **Visual links**: See connections between notes via wiki-links
- **Navigate**: Double-click nodes to open files

## Tips & Tricks

1. **Quick navigation**: Use wiki-links to create a web of connected notes
2. **Project organization**: Use subfolders for different projects
3. **Tag everything**: Hashtags make finding related notes easy
4. **Pin important files**: Keep frequently-used notes at the top
5. **Full-text search**: Search box finds text inside files (after indexing)
6. **Autocomplete**: Let `[[` and `#` save you typing

## Notes

- All files are plain `.md` (Markdown) - use them with any other app
- Files are stored exactly where you put them - no hidden databases
- Compatible with other note apps (Obsidian, Foam, etc.)
"""


class SettingsDialog(QDialog):
    """Dialog for changing application settings (directory + UI behaviors)."""

    def __init__(self, config: Config, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Settings")
        self.setModal(True)
        self._config = config
        self.selected_directory = config.notes_directory

        layout = QVBoxLayout()

        # Directory selection
        dir_layout = QHBoxLayout()
        dir_label = QLabel("Notes Directory:")
        self.dir_input = QLineEdit(str(self.selected_directory))
        self.dir_input.setReadOnly(True)
        browse_btn = QPushButton("Browse...")
        browse_btn.clicked.connect(self._browse_directory)
        dir_layout.addWidget(dir_label)
        dir_layout.addWidget(self.dir_input)
        dir_layout.addWidget(browse_btn)
        layout.addLayout(dir_layout)

        # UI behavior settings
        self.select_search_checkbox = QPushButton("Select search text on ESC: ON")
        self.select_search_checkbox.setCheckable(True)
        initial = bool(self._config.get("ui.select_search_on_escape", True))
        self.select_search_checkbox.setChecked(initial)
        self._update_select_search_label()
        self.select_search_checkbox.clicked.connect(self._update_select_search_label)
        layout.addWidget(self.select_search_checkbox)

        # Theme selection
        theme_row = QHBoxLayout()
        theme_label = QLabel("Theme:")
        self.theme_combo = QComboBox()
        self.theme_combo.addItems(available_themes())
        current_theme = str(self._config.get("theme", "dark"))
        idx = self.theme_combo.findText(current_theme)
        if idx >= 0:
            self.theme_combo.setCurrentIndex(idx)
        theme_row.addWidget(theme_label)
        theme_row.addWidget(self.theme_combo)
        layout.addLayout(theme_row)

        # File ordering selection
        order_row = QHBoxLayout()
        order_label = QLabel("File Order:")
        self.order_combo = QComboBox()
        self.order_combo.addItems(["alphabetical", "last_modified"])
        current_order = str(self._config.get("ui.file_order", "alphabetical"))
        idx_o = self.order_combo.findText(current_order)
        if idx_o >= 0:
            self.order_combo.setCurrentIndex(idx_o)
        order_row.addWidget(order_label)
        order_row.addWidget(self.order_combo)
        layout.addLayout(order_row)

        # Buttons
        button_layout = QHBoxLayout()
        save_btn = QPushButton("Save")
        save_btn.clicked.connect(self.accept)
        cancel_btn = QPushButton("Cancel")
        cancel_btn.clicked.connect(self.reject)
        button_layout.addStretch()
        button_layout.addWidget(save_btn)
        button_layout.addWidget(cancel_btn)
        layout.addLayout(button_layout)

        self.setLayout(layout)
        self.resize(520, 220)

    def _update_select_search_label(self):
        state = "ON" if self.select_search_checkbox.isChecked() else "OFF"
        self.select_search_checkbox.setText(f"Select search text on ESC: {state}")

    def _browse_directory(self):
        """Open directory picker."""
        directory = QFileDialog.getExistingDirectory(
            self,
            "Select Notes Directory",
            str(self.selected_directory),
            QFileDialog.Option.ShowDirsOnly
        )
        if directory:
            self.selected_directory = Path(directory)
            self.dir_input.setText(str(self.selected_directory))

    def get_directory(self) -> Path:
        """Get the selected directory."""
        return self.selected_directory


class MainWindow(QMainWindow):
    """Main application window."""

    def __init__(self, config: Config):
        super().__init__()
        self.config = config
        self.notes_directory = config.ensure_notes_directory()
        
        self.setWindowTitle("SiText")
        self.resize(1200, 800)

        # Create menu bar
        self._create_menu_bar()

        # Apply dark theme stylesheet
        self._apply_stylesheet()

        # Create central widget with splitters
        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        main_layout = QHBoxLayout(central_widget)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # Main horizontal splitter
        main_splitter = QSplitter(Qt.Orientation.Horizontal)

        # Left panel (file list + hashtags)
        left_panel = QWidget()
        left_layout = QVBoxLayout(left_panel)
        left_layout.setContentsMargins(0, 0, 0, 0)
        left_layout.setSpacing(0)

        # File list
        self.file_list = FileListWidget(self.notes_directory)
        # Apply initial file order preference from config
        initial_order = str(self.config.get("ui.file_order", "alphabetical"))
        self.file_list.set_order(initial_order)
        # Keep file list aware of pinned state for context menu
        current_pins = set(self.config.get_pinned_for_dir(self.notes_directory))
        self.file_list.set_pinned_names(current_pins)
        self.file_list.file_selected.connect(self._open_file)
        self.file_list.file_deleted.connect(self._on_file_deleted)
        self.file_list.pin_requested.connect(self._on_pin_requested)
        self.file_list.unpin_requested.connect(self._on_unpin_requested)
        left_layout.addWidget(self.file_list, stretch=3)

        # Load initial pins (no separate widget; pins float to top of file list)
        self._apply_pins()

        # Hashtag panel
        self.hashtag_panel = HashtagPanel(self.notes_directory)
        self.hashtag_panel.hashtag_selected.connect(self._filter_by_hashtag)
        left_layout.addWidget(self.hashtag_panel, stretch=1)

        # Buttons at bottom
        button_layout = QHBoxLayout()
        button_layout.setContentsMargins(5, 5, 5, 5)
        button_layout.setSpacing(5)

        self.howto_btn = QPushButton("How To")
        self.howto_btn.setFixedHeight(32)
        self.howto_btn.clicked.connect(self._show_howto)
        button_layout.addWidget(self.howto_btn)

        self.settings_btn = QPushButton("Settings")
        self.settings_btn.setFixedHeight(32)
        self.settings_btn.clicked.connect(self._show_settings)
        button_layout.addWidget(self.settings_btn)

        left_layout.addLayout(button_layout)

        main_splitter.addWidget(left_panel)

        # Editor
        self.editor = MarkdownEditor(self.notes_directory)
        self.editor.file_saved.connect(self._on_file_saved)
        self.editor.wiki_link_clicked.connect(self._open_file)
        # Sync pin checkbox state when user toggles pin in editor
        self.editor.pin_toggled.connect(self._on_editor_pin_toggled)
        # Hashtag clicks populate search input
        self.editor.hashtag_clicked.connect(self._on_editor_hashtag_clicked)
        # Export button triggers PDF export
        self.editor.export_requested.connect(self._export_file_to_pdf)
        main_splitter.addWidget(self.editor)

        # Set initial splitter sizes (30% left, 70% right)
        main_splitter.setSizes([360, 840])

        main_layout.addWidget(main_splitter)

        # Setup keyboard shortcuts
        self._setup_shortcuts()

        # Status bar
        self.statusBar().showMessage(f"Notes: {self.notes_directory}")
        
        # Apply initial theme to editor
        theme_key = self.config.get("theme", "dark")
        self.editor.set_theme(theme_key)

    def _apply_stylesheet(self):
        """Apply theme stylesheet from config via themes module."""
        theme_key = self.config.get("theme", "dark")
        self.setStyleSheet(get_stylesheet(theme_key))
        # Update editor syntax highlighting colors
        if hasattr(self, 'editor'):
            self.editor.set_theme(theme_key)

    def _setup_shortcuts(self):
        """Setup keyboard shortcuts."""
        # Cmd+Q / Ctrl+Q - Quit
        quit_shortcut = QShortcut(QKeySequence.StandardKey.Quit, self)
        quit_shortcut.activated.connect(self.close)

        # Cmd+W / Ctrl+W - Close window
        close_shortcut = QShortcut(QKeySequence.StandardKey.Close, self)
        close_shortcut.activated.connect(self.close)

        # Cmd+, / Ctrl+, - Settings
        settings_shortcut = QShortcut(QKeySequence.StandardKey.Preferences, self)
        settings_shortcut.activated.connect(self._show_settings)

        # Cmd+J / Ctrl+J - Follow wiki-link at cursor (support both Meta and Control)
        follow_link_shortcut_ctrl = QShortcut(QKeySequence("Ctrl+J"), self)
        follow_link_shortcut_ctrl.activated.connect(self.editor.follow_link_at_cursor)
        follow_link_shortcut_cmd = QShortcut(QKeySequence("Meta+J"), self)
        follow_link_shortcut_cmd.activated.connect(self.editor.follow_link_at_cursor)

        # Cmd+3 / Ctrl+3 - Insert hash
        hash_shortcut = QShortcut(QKeySequence("Ctrl+3"), self)
        hash_shortcut.activated.connect(self._insert_hash)

        # Track last ESC time for double-tap detection
        self._last_escape_time = 0.0
    # (Graph shortcut removed)

    def _insert_hash(self):
        """Insert a # character at cursor."""
        if self.editor.text_edit.hasFocus():
            self.editor.text_edit.insertPlainText("#")
        elif self.file_list.search_input.hasFocus():
            self.file_list.search_input.insert("#")

    def _create_menu_bar(self):
        """Create the application menu bar."""
        menubar = self.menuBar()

        # File menu
        file_menu = menubar.addMenu("File")

        # Export to PDF action
        export_action = file_menu.addAction("Export to PDF...")
        export_action.setShortcut("Ctrl+E")
        export_action.triggered.connect(self._export_to_pdf)

    def _export_to_pdf(self):
        """Export the current note to PDF."""
        if not self.editor.current_file:
            QMessageBox.information(
                self,
                "No File Open",
                "Please open a note to export to PDF."
            )
            return

        # Prompt for save location
        default_name = self.editor.current_file.stem + ".pdf"
        save_path, _ = QFileDialog.getSaveFileName(
            self,
            "Export to PDF",
            str(Path.home() / default_name),
            "PDF Files (*.pdf)"
        )

        if not save_path:
            return

        # Perform export
        from sitermtext.utils.pdf_export import export_to_pdf
        success = export_to_pdf(self.editor.current_file, Path(save_path))

        if success:
            QMessageBox.information(
                self,
                "Export Successful",
                f"PDF exported to:\n{save_path}"
            )
        else:
            QMessageBox.warning(
                self,
                "Export Failed",
                "Failed to export PDF. Check console for errors."
            )

    def _export_file_to_pdf(self, file_path: Path):
        """Export a specific file to PDF (triggered by Export button)."""
        # Prompt for save location
        default_name = file_path.stem + ".pdf"
        save_path, _ = QFileDialog.getSaveFileName(
            self,
            "Export to PDF",
            str(Path.home() / default_name),
            "PDF Files (*.pdf)"
        )

        if not save_path:
            return

        # Perform export
        from sitermtext.utils.pdf_export import export_to_pdf
        success = export_to_pdf(file_path, Path(save_path))

        if success:
            QMessageBox.information(
                self,
                "Export Successful",
                f"PDF exported to:\n{save_path}"
            )
        else:
            QMessageBox.warning(
                self,
                "Export Failed",
                "Failed to export PDF. Check console for errors."
            )

    def _show_howto(self):
        """Show How To dialog."""
        dialog = HowToDialog(self)
        dialog.show()

    def _show_settings(self):
        """Show settings dialog."""
        dialog = SettingsDialog(self.config, self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            # Persist directory change if modified
            new_directory = dialog.get_directory()
            if new_directory != self.notes_directory:
                self.config.set("notes_directory", str(new_directory))
                self.notes_directory = new_directory
                self.statusBar().showMessage(f"Notes: {self.notes_directory}")
                self.file_list.set_notes_directory(new_directory)
                self.hashtag_panel.set_notes_directory(new_directory)
                self.editor.set_notes_directory(new_directory)
                self.editor.close_file()
                # Reapply pin ordering
                self._apply_pins()

            # Persist select-on-ESC setting
            self.config.set("ui.select_search_on_escape", dialog.select_search_checkbox.isChecked())

            # Persist theme selection + apply immediately
            selected_theme = dialog.theme_combo.currentText()
            self.config.set("theme", selected_theme)
            # Persist file order
            selected_order = dialog.order_combo.currentText()
            self.config.set("ui.file_order", selected_order)
            self.config.save()
            self._apply_stylesheet()
            # Apply file ordering immediately
            self.file_list.set_order(selected_order)

    def _apply_pins(self):
        pins = set(self.config.get_pinned_for_dir(self.notes_directory))
        self.file_list.set_pinned_names(pins)
        # Force refresh display ordering
        self.file_list.refresh_files()
        # Update editor pin button if current file is open
        editor = getattr(self, "editor", None)
        if editor and editor.current_file:
            editor.set_pin_checked(editor.current_file.name in pins)

    # (Graph dialog removed)

    def _on_pin_requested(self, file_path: Path):
        self.config.add_pin(self.notes_directory, file_path.name)
        self.config.save()
        self._apply_pins()

    def _on_unpin_requested(self, file_path: Path):
        self.config.remove_pin(self.notes_directory, file_path.name)
        self.config.save()
        self._apply_pins()

    def _on_editor_pin_toggled(self, file_path: Path, pinned: bool):
        if pinned:
            self.config.add_pin(self.notes_directory, file_path.name)
        else:
            self.config.remove_pin(self.notes_directory, file_path.name)
        self.config.save()
        self._apply_pins()

    def _on_editor_hashtag_clicked(self, tag: str):
        # Populate search box with hashtag and focus list filtering
        self.file_list.search_input.setText(f"#{tag}")
        self.file_list.search_input.setFocus()
        # Trigger filtering immediately
        self.file_list._filter_files()

    def _open_file(self, file_path: Path):
        """Open a file in the editor."""
        if not file_path.exists():
            # Create new file
            try:
                file_path.touch()
                self.file_list.refresh_files()
            except OSError as e:
                QMessageBox.critical(self, "Error", f"Could not create file: {e}")
                return
        
        self.editor.load_file(file_path)
        # Sync pin checkbox state for the opened file
        self._apply_pins()

    def _on_file_deleted(self):
        """Handle file deletion - clear the editor."""
        self.editor.close_file()
        self.hashtag_panel.refresh_hashtags()

    def _on_file_saved(self, file_path: Path):
        """Handle file saved event."""
        self.file_list.refresh_files()
        self.hashtag_panel.refresh_hashtags()
        self.statusBar().showMessage(f"Saved: {file_path.name}", 3000)

    def _filter_by_hashtag(self, hashtag: str):
        """Filter files by hashtag."""
        self.file_list.search_input.setText(f"#{hashtag}")
        self.file_list.search_input.setFocus()

    def keyPressEvent(self, event):
        """Handle key press events for double ESC detection."""
        import time
        
        if event.key() == Qt.Key.Key_Escape:
            current_time = time.time()
            time_since_last = current_time - self._last_escape_time
            
            # Check if this is a double-tap (within 0.5 seconds)
            if time_since_last < 0.5:
                # Double ESC: Focus hashtags
                self.hashtag_panel.hashtag_list.setFocus()
                if self.hashtag_panel.hashtag_list.count() > 0:
                    self.hashtag_panel.hashtag_list.setCurrentRow(0)
                self._last_escape_time = 0.0  # Reset timer
            else:
                # Single ESC: Focus file search
                self.file_list.search_input.setFocus()
                if self.config.get("ui.select_search_on_escape", True):
                    self.file_list.search_input.selectAll()
                self._last_escape_time = current_time
            
            event.accept()
            return
        
        super().keyPressEvent(event)

    def closeEvent(self, event):
        """Handle window close event."""
        # Save any unsaved changes
        if self.editor.is_modified():
            reply = QMessageBox.question(
                self,
                "Unsaved Changes",
                "You have unsaved changes. Save before closing?",
                QMessageBox.StandardButton.Save | 
                QMessageBox.StandardButton.Discard | 
                QMessageBox.StandardButton.Cancel
            )
            
            if reply == QMessageBox.StandardButton.Save:
                self.editor.save_file()
                # fall through to shutdown
            elif reply == QMessageBox.StandardButton.Discard:
                # fall through to shutdown
                pass
            else:
                event.ignore()
                return
        # Ensure background threads are stopped before closing
        try:
            self.file_list.shutdown()
        except Exception:
            pass
        event.accept()
