"""File list widget for displaying and selecting markdown files."""

from pathlib import Path
from typing import List, Optional

from textual import events
from textual.app import ComposeResult
from textual.containers import Vertical, VerticalScroll
from textual.message import Message
from textual.reactive import reactive
from textual.widget import Widget
from textual.widgets import Input, Label, ListItem, ListView


class FileList(Widget):
    """Widget for displaying a list of markdown files with search."""

    DEFAULT_CSS = """
    FileList {
        width: 30;
        background: $panel;
    }

    FileList #file-list-title {
        padding: 1 2;
        color: $text;
        background: $primary;
        text-style: bold;
    }

    FileList Input {
        margin: 0 1 1 1;
        border: tall $primary;
        background: $surface;
        padding: 0 1;
    }

    FileList Input:focus {
        border: tall $accent;
    }

    FileList ListView {
        height: 1fr;
        background: $panel;
        padding: 0 1;
    }

    FileList ListView > ListItem {
        padding: 0 1;
        background: black;
        color: green;
    }

    FileList ListView > ListItem:hover {
        background: green;
        color: black;
    }

    FileList ListView > ListItem.--highlight {
        background: green !important;
        color: black !important;
    }
    
    FileList ListView:focus > ListItem.--highlight {
        background: green !important;
        color: black !important;
    }
    
    FileList ListView > ListItem.--highlight > * {
        background: green !important;
        color: black !important;
    }
    
    FileList ListView:focus > ListItem.--highlight > * {
        background: green !important;
        color: black !important;
    }
    """

    files: reactive[List[Path]] = reactive(list, init=False)
    filtered_files: reactive[List[Path]] = reactive(list, init=False)
    search_query: reactive[str] = reactive("", init=False)
    notes_directory: reactive[Path] = reactive(Path.home(), init=False)

    def __init__(self, notes_directory: Path, **kwargs) -> None:
        """Initialize the file list.

        Args:
            notes_directory: Directory containing markdown files
            **kwargs: Additional widget arguments
        """
        super().__init__(**kwargs)
        self.notes_directory = notes_directory

    def compose(self) -> ComposeResult:
        """Compose the file list widget."""
        yield Label("📝 Files", id="file-list-title")
        yield Input(placeholder="Search files...", id="file-search")
        yield ListView(id="file-list-view")

    def on_mount(self) -> None:
        """Called when widget is mounted."""
        # Defer refresh until after widgets are ready
        self.call_after_refresh(self.refresh_files)

    def refresh_files(self) -> None:
        """Scan notes directory and update file list."""
        if not self.notes_directory.exists():
            self.files = []
            self.filtered_files = []
            return

        # Get all .md files
        md_files = sorted(self.notes_directory.glob("*.md"))
        self.files = md_files
        self.apply_filter()

    def apply_filter(self) -> None:
        """Apply search filter to file list."""
        query = self.search_query.lower()
        if not query:
            self.filtered_files = self.files
        elif query.startswith('#') or query.startswith('£'):
            # Filter by hashtag content (accept both # and £ for terminal compatibility)
            hashtag = query[1:]  # Remove the # or £ prefix
            self.filtered_files = self._filter_by_hashtag(hashtag)
        else:
            # Filter by filename
            self.filtered_files = [
                f for f in self.files if query in f.stem.lower()
            ]
        self.update_list_view()

    def _filter_by_hashtag(self, hashtag: str) -> List[Path]:
        """Filter files that contain a specific hashtag.

        Args:
            hashtag: Hashtag to search for (without # prefix)

        Returns:
            List of files containing the hashtag
        """
        import re
        matching_files = []
        hashtag_pattern = re.compile(r'#([a-zA-Z0-9_]+)')
        
        for md_file in self.files:
            try:
                content = md_file.read_text(encoding='utf-8')
                tags = hashtag_pattern.findall(content)
                # Case-insensitive match
                if any(tag.lower() == hashtag.lower() for tag in tags):
                    matching_files.append(md_file)
            except (OSError, UnicodeDecodeError):
                continue
        
        return matching_files

    def update_list_view(self) -> None:
        """Update the ListView with filtered files."""
        try:
            list_view = self.query_one("#file-list-view", ListView)
        except Exception:
            # Widget not ready yet
            return
            
        list_view.clear()

        if not self.filtered_files:
            list_view.append(ListItem(Label("No files found")))
            return

        for file_path in self.filtered_files:
            list_view.append(ListItem(Label(file_path.stem)))

    def on_input_changed(self, event: Input.Changed) -> None:
        """Handle search input changes."""
        if event.input.id == "file-search":
            self.search_query = event.value
            self.apply_filter()

    def on_key(self, event: events.Key) -> None:
        """Handle key presses in the widget."""
        try:
            search_input = self.query_one("#file-search", Input)
            list_view = self.query_one("#file-list-view", ListView)
        except Exception:
            return
        
        # Check if search input is focused
        if search_input.has_focus:
            # Map Option/Alt+3 to '#' for UK keyboards in terminals where Option is Meta
            try:
                is_alt = getattr(event, "alt", False) or getattr(event, "meta", False)
            except Exception:
                is_alt = False
            if event.key in ("alt+3", "meta+3") or (event.key == "3" and is_alt):
                pos = getattr(search_input, "cursor_position", len(search_input.value))
                val = search_input.value
                search_input.value = val[:pos] + "#" + val[pos:]
                try:
                    search_input.cursor_position = pos + 1  # type: ignore[attr-defined]
                except Exception:
                    pass
                event.prevent_default()
                event.stop()
                return
            if event.key == "down":
                # Move focus to list view and select first item
                if self.filtered_files:
                    list_view.focus()
                    list_view.index = 0
                event.prevent_default()
                event.stop()
            elif event.key == "enter":
                # If there's text in search, create/open a file with that name
                search_text = search_input.value.strip()
                if search_text:
                    # Add .md extension if not present
                    filename = search_text if search_text.endswith(".md") else f"{search_text}.md"
                    file_path = self.notes_directory / filename
                    self.post_message(self.FileSelected(file_path))
                    # Clear search after creating/opening
                    search_input.value = ""
                event.prevent_default()
                event.stop()
            elif event.key == "escape":
                # If search has text, clear it; otherwise let event bubble up
                if search_input.value:
                    search_input.value = ""
                    event.prevent_default()
                    event.stop()
                # If search is empty, let ESC bubble up for double-tap detection
        # Check if list view is focused
        elif list_view.has_focus:
            if event.key == "enter":
                # Open the selected file
                index = list_view.index
                if index is not None and 0 <= index < len(self.filtered_files):
                    selected_file = self.filtered_files[index]
                    self.post_message(self.FileSelected(selected_file))
                event.prevent_default()
                event.stop()

    def on_list_view_selected(self, event: ListView.Selected) -> None:
        """Handle file selection (when clicking on an item)."""
        if event.list_view.id == "file-list-view":
            index = event.list_view.index
            if index is not None and 0 <= index < len(self.filtered_files):
                selected_file = self.filtered_files[index]
                self.post_message(self.FileSelected(selected_file))

    def watch_notes_directory(self, new_directory: Path) -> None:
        """Watch for changes to notes directory."""
        self.refresh_files()

    class FileSelected(Message):
        """Message sent when a file is selected."""

        def __init__(self, file_path: Path) -> None:
            """Initialize message.

            Args:
                file_path: Path to selected file
            """
            super().__init__()
            self.file_path = file_path
