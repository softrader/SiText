"""Markdown editor widget with syntax highlighting."""

import re
from pathlib import Path
from typing import Optional

from textual import events, work
from textual.app import ComposeResult
from textual.message import Message
from textual.reactive import reactive
from textual.widget import Widget
from textual.widgets import Label, TextArea


class MarkdownEditor(Widget):
    """Widget for editing markdown files with syntax highlighting."""

    DEFAULT_CSS = """
    MarkdownEditor {
        background: black;
        border-left: thick green;
    }

    MarkdownEditor #editor-title {
        padding: 1 2;
        background: black;
        color: green;
        text-style: bold;
    }

    MarkdownEditor TextArea {
        height: 1fr;
        background: black;
        color: green;
        border: none;
        padding: 1 2;
    }

    MarkdownEditor TextArea:focus {
        border: none;
    }
    """

    current_file: reactive[Optional[Path]] = reactive(None, init=False)
    is_modified: reactive[bool] = reactive(False, init=False)
    _auto_save_timer: Optional[object] = None

    def compose(self) -> ComposeResult:
        """Compose the editor widget."""
        yield Label("No file open", id="editor-title")
        yield TextArea(language="markdown", theme="monokai", id="editor-textarea")

    def on_mount(self) -> None:
        """Called when widget is mounted."""
        text_area = self.query_one("#editor-textarea", TextArea)
        text_area.can_focus = True

    def load_file(self, file_path: Path) -> None:
        """Load a file into the editor.

        Args:
            file_path: Path to the markdown file to load
        """
        try:
            content = file_path.read_text(encoding="utf-8")
            text_area = self.query_one("#editor-textarea", TextArea)
            text_area.text = content
            self.current_file = file_path
            self.is_modified = False
            self.update_title()
            # Focus the text area for immediate editing
            text_area.focus()
        except (OSError, UnicodeDecodeError) as e:
            self.notify(f"Error loading file: {e}", severity="error")

    def save_file(self, notify: bool = False) -> bool:
        """Save the current file.

        Args:
            notify: Whether to show a notification on save

        Returns:
            True if save was successful, False otherwise
        """
        if self.current_file is None:
            if notify:
                self.notify("No file to save", severity="warning")
            return False

        try:
            text_area = self.query_one("#editor-textarea", TextArea)
            content = text_area.text
            self.current_file.write_text(content, encoding="utf-8")
            self.is_modified = False
            self.update_title()
            if notify:
                self.notify(f"Saved {self.current_file.name}", severity="information")
            self.post_message(self.FileSaved(self.current_file))
            return True
        except OSError as e:
            self.notify(f"Error saving file: {e}", severity="error")
            return False

    def create_new_file(self, file_path: Path) -> None:
        """Create and open a new file.

        Args:
            file_path: Path to the new file
        """
        try:
            file_path.touch()
            self.load_file(file_path)
            # Focus the text area for immediate editing
            text_area = self.query_one("#editor-textarea", TextArea)
            text_area.focus()
        except OSError as e:
            self.notify(f"Error creating file: {e}", severity="error")

    def update_title(self) -> None:
        """Update the editor title bar."""
        title_label = self.query_one("#editor-title", Label)
        if self.current_file:
            modified = " *" if self.is_modified else ""
            title_label.update(f"📄 {self.current_file.stem}{modified}")
        else:
            title_label.update("No file open")

    def on_text_area_changed(self, event: TextArea.Changed) -> None:
        """Handle text area changes."""
        if event.text_area.id == "editor-textarea" and self.current_file:
            self.is_modified = True
            self.update_title()
            # Schedule auto-save after 2 seconds of inactivity
            self._schedule_auto_save()

    def _schedule_auto_save(self) -> None:
        """Schedule an auto-save after a delay."""
        # Cancel any existing timer
        if self._auto_save_timer is not None:
            self._auto_save_timer.stop()
        
        # Set a new timer for 2 seconds
        self._auto_save_timer = self.set_timer(2.0, self._auto_save)

    def _auto_save(self) -> None:
        """Auto-save the current file."""
        if self.current_file and self.is_modified:
            self.save_file()

    def insert_text(self, s: str) -> None:
        """Insert text at the current cursor position in the TextArea.

        Args:
            s: The string to insert
        """
        try:
            text_area = self.query_one("#editor-textarea", TextArea)
        except Exception:
            return

        # Determine cursor location and insert text
        try:
            row, col = text_area.cursor_location  # type: ignore[attr-defined]
        except Exception:
            # Fallback: append to end
            text_area.text += s
            self.is_modified = True
            self.update_title()
            self._schedule_auto_save()
            return

        lines = text_area.text.split("\n")
        if row >= len(lines):
            # Append a new line if cursor row is out of bounds
            lines.append(s)
            new_row = len(lines) - 1
            new_col = len(lines[-1])
        else:
            line = lines[row]
            lines[row] = line[:col] + s + line[col:]
            new_row = row
            new_col = col + len(s)

        text_area.text = "\n".join(lines)
        # Try to move cursor after inserted text (best effort)
        try:
            text_area.cursor_location = (new_row, new_col)  # type: ignore[attr-defined]
        except Exception:
            pass
        self.is_modified = True
        self.update_title()
        self._schedule_auto_save()

    def watch_is_modified(self, is_modified: bool) -> None:
        """Watch for modification state changes."""
        self.update_title()

    def watch_current_file(self, file_path: Optional[Path]) -> None:
        """Watch for current file changes."""
        self.update_title()

    def on_key(self, event: events.Key) -> None:
        """Handle key events.
        
        Args:
            event: Key event
        """
        # Map Option/Alt+3 to '#' for UK keyboards in terminals where Option is Meta
        try:
            is_alt = getattr(event, "alt", False) or getattr(event, "meta", False)
        except Exception:
            is_alt = False
        if event.key in ("alt+3", "meta+3") or (event.key == "3" and is_alt):
            # Insert a literal '#'
            try:
                text_area = self.query_one("#editor-textarea", TextArea)
                row, col = text_area.cursor_location  # type: ignore[attr-defined]
                lines = text_area.text.split('\n')
                if row >= len(lines):
                    lines.append("#")
                    new_row = len(lines) - 1
                    new_col = len(lines[-1])
                else:
                    line = lines[row]
                    lines[row] = line[:col] + "#" + line[col:]
                    new_row = row
                    new_col = col + 1
                text_area.text = "\n".join(lines)
                try:
                    text_area.cursor_location = (new_row, new_col)  # type: ignore[attr-defined]
                except Exception:
                    pass
                self.is_modified = True
                self.update_title()
                self._schedule_auto_save()
            except Exception:
                pass
            event.prevent_default()
            event.stop()
            return

        # Handle Cmd+Enter to follow wiki-links
        # Try multiple possible key representations
        if event.key in ("cmd+enter", "ctrl+enter", "ctrl+j"):
            self._follow_link_at_cursor()
            event.prevent_default()
            event.stop()

    def _follow_link_at_cursor(self) -> None:
        """Follow a wiki-link at the current cursor position."""
        if not self.current_file:
            return

        text_area = self.query_one("#editor-textarea", TextArea)
        cursor_location = text_area.cursor_location
        
        # Get the current line
        lines = text_area.text.split('\n')
        if cursor_location[0] >= len(lines):
            return
            
        current_line = lines[cursor_location[0]]
        cursor_col = cursor_location[1]
        
        # Find all wiki-links in the current line
        wikilink_pattern = re.compile(r'\[\[([^\]]+)\]\]')
        
        for match in wikilink_pattern.finditer(current_line):
            start, end = match.span()
            # Check if cursor is within this link
            if start <= cursor_col <= end:
                link_text = match.group(1)
                self._open_wikilink(link_text)
                return

    def _open_wikilink(self, link_text: str) -> None:
        """Open a wiki-link target file.

        Args:
            link_text: The text inside [[ ]]
        """
        if not self.current_file:
            return
            
        # Use the same directory as the current file
        notes_dir = self.current_file.parent
        
        # Add .md extension if not present
        filename = link_text.strip()
        if not filename.endswith('.md'):
            filename += '.md'
        
        target_path = notes_dir / filename
        
        # Post message to open this file
        self.post_message(self.WikiLinkClicked(target_path))

    class FileSaved(Message):
        """Message sent when a file is saved."""

        def __init__(self, file_path: Path) -> None:
            """Initialize message.

            Args:
                file_path: Path to saved file
            """
            super().__init__()
            self.file_path = file_path

    class WikiLinkClicked(Message):
        """Message sent when a wiki-link is clicked."""

        def __init__(self, file_path: Path) -> None:
            """Initialize message.

            Args:
                file_path: Path to the linked file
            """
            super().__init__()
            self.file_path = file_path
