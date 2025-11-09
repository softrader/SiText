"""Main entry point for SiTermText application."""

import argparse
from pathlib import Path

from textual.app import App, ComposeResult
from textual.containers import Container, Horizontal, Vertical
from textual.widgets import Footer, Header, Input

from sitermtext.config import Config
from sitermtext.widgets.editor import MarkdownEditor
from sitermtext.widgets.file_list import FileList
from sitermtext.widgets.hashtag_panel import HashtagPanel
from sitermtext.widgets.settings_screen import SettingsScreen


class SiTermTextApp(App):
    """A terminal-based note-taking application."""

    BINDINGS = [
        ("ctrl+c", "quit", "Quit"),
        ("ctrl+j", "follow_link", "Follow Link"),
        ("ctrl+comma", "show_settings", "Settings"),
        ("escape", "focus_file_list", "Files"),
        ("ctrl+3", "insert_hash", "# Fallback"),
    ]
    
    _last_escape_time: float = 0.0

    CSS = """
    Screen {
        layout: horizontal;
        background: black;
    }

    #left-panel {
        width: 35;
        layout: vertical;
        background: black;
    }

    #file-list-container {
        height: 1fr;
        background: black;
    }

    #hashtag-container {
        height: 12;
        background: black;
    }

    #editor-container {
        width: 1fr;
        background: black;
    }

    /* Classic terminal theme */
    * {
        scrollbar-background: black;
        scrollbar-color: green;
        scrollbar-color-hover: #00ff00;
        color: green;
        background: black;
    }
    
    Input {
        background: black;
        color: green;
        border: solid green;
    }
    
    Input:focus {
        border: solid #00ff00;
    }
    
    ListView {
        background: black;
        color: green;
    }
    
    ListItem {
        background: black;
        color: green;
    }
    
    ListItem.--highlight {
        background: green !important;
        color: black !important;
    }
    
    ListItem:hover {
        background: #003300;
        color: #00ff00;
    }
    
    ListView:focus ListItem.--highlight {
        background: green !important;
        color: black !important;
    }
    
    ListItem.--highlight Label {
        background: green !important;
        color: black !important;
    }
    
    ListView:focus ListItem.--highlight Label {
        background: green !important;
        color: black !important;
    }
    
    Label {
        background: black;
        color: green;
    }
    
    TextArea {
        background: black;
        color: green;
    }
    """

    def __init__(self, config: Config, **kwargs) -> None:
        """Initialize the application.

        Args:
            config: Application configuration
            **kwargs: Additional app arguments
        """
        super().__init__(**kwargs)
        self.config = config
        self.notes_directory = config.ensure_notes_directory()

    def compose(self) -> ComposeResult:
        """Compose the application layout."""
        yield Header()

        with Horizontal():
            with Vertical(id="left-panel"):
                with Container(id="file-list-container"):
                    yield FileList(self.notes_directory, id="file-list")
                with Container(id="hashtag-container"):
                    yield HashtagPanel(self.notes_directory, id="hashtag-panel")

            with Container(id="editor-container"):
                yield MarkdownEditor(id="editor")

        yield Footer()

    def on_mount(self) -> None:
        """Called when the app is mounted."""
        self.title = "SiTermText"
        self.sub_title = f"Notes: {self.notes_directory}"

        # Focus the search box on startup
        self.call_after_refresh(self._focus_search)

    def _focus_search(self) -> None:
        """Focus the search input box."""
        file_list = self.query_one("#file-list", FileList)
        search_input = file_list.query_one("#file-search", Input)
        search_input.focus()

    def on_file_list_file_selected(self, message: FileList.FileSelected) -> None:
        """Handle file selection from file list.

        Args:
            message: File selected message
        """
        editor = self.query_one("#editor", MarkdownEditor)
        
        # If file doesn't exist, create it
        if not message.file_path.exists():
            editor.create_new_file(message.file_path)
            # Refresh file list to show the new file
            file_list = self.query_one("#file-list", FileList)
            file_list.refresh_files()
        else:
            editor.load_file(message.file_path)

    def on_markdown_editor_file_saved(self, message: MarkdownEditor.FileSaved) -> None:
        """Handle file saved event.

        Args:
            message: File saved message
        """
        # Refresh file list and hashtags
        file_list = self.query_one("#file-list", FileList)
        file_list.refresh_files()

        hashtag_panel = self.query_one("#hashtag-panel", HashtagPanel)
        hashtag_panel.refresh_hashtags()

    def on_markdown_editor_wiki_link_clicked(
        self, message: MarkdownEditor.WikiLinkClicked
    ) -> None:
        """Handle wiki-link click event.

        Args:
            message: Wiki-link clicked message
        """
        editor = self.query_one("#editor", MarkdownEditor)
        
        # Save current file before switching
        if editor.is_modified:
            editor.save_file(notify=False)
        
        # If file doesn't exist, create it
        if not message.file_path.exists():
            editor.create_new_file(message.file_path)
            # Refresh file list to show the new file
            file_list = self.query_one("#file-list", FileList)
            file_list.refresh_files()
        else:
            editor.load_file(message.file_path)

    def on_hashtag_panel_hashtag_selected(
        self, message: HashtagPanel.HashtagSelected
    ) -> None:
        """Handle hashtag selection.

        Args:
            message: Hashtag selected message
        """
        # Put the hashtag in the search box to filter files
        file_list = self.query_one("#file-list", FileList)
        search_input = file_list.query_one("#file-search", Input)
        search_input.value = f"#{message.hashtag}"
        
        # Focus the search box so user can see the filter
        search_input.focus()

    def action_focus_file_list(self) -> None:
        """Focus the search box or hashtags (ESC key handler).
        
        Single ESC: Focus file search
        Double ESC (within 0.5s): Focus hashtags
        """
        import time
        
        current_time = time.time()
        time_since_last = current_time - self._last_escape_time
        
        # Save the current file before switching focus
        editor = self.query_one("#editor", MarkdownEditor)
        if editor.is_modified:
            editor.save_file(notify=False)
        
        # Check if this is a double-tap (within 0.5 seconds)
        if time_since_last < 0.5:
            # Double ESC: Focus hashtags
            hashtag_panel = self.query_one("#hashtag-panel", HashtagPanel)
            list_view = hashtag_panel.query_one("#hashtag-list-view")
            list_view.focus()
            self._last_escape_time = 0.0  # Reset timer
        else:
            # Single ESC: Focus file search
            file_list = self.query_one("#file-list", FileList)
            search_input = file_list.query_one("#file-search", Input)
            search_input.focus()
            self._last_escape_time = current_time

    def action_follow_link(self) -> None:
        """Follow wiki-link at cursor (Ctrl+J handler)."""
        editor = self.query_one("#editor", MarkdownEditor)
        editor._follow_link_at_cursor()

    def action_show_settings(self) -> None:
        """Show settings screen (Ctrl+, handler)."""
        def handle_settings(new_directory: Path | None) -> None:
            """Handle settings dialog result."""
            if new_directory and new_directory != self.notes_directory:
                # Update configuration
                self.config.set("notes_directory", str(new_directory))
                self.config.save()
                
                # Update app state
                self.notes_directory = new_directory
                self.sub_title = f"Notes: {self.notes_directory}"
                
                # Refresh all widgets
                file_list = self.query_one("#file-list", FileList)
                file_list.notes_directory = new_directory
                file_list.refresh_files()
                
                hashtag_panel = self.query_one("#hashtag-panel", HashtagPanel)
                hashtag_panel.notes_directory = new_directory
                hashtag_panel.refresh_hashtags()
                
                # Clear editor
                editor = self.query_one("#editor", MarkdownEditor)
                editor.current_file = None
                editor.update_title()

        self.push_screen(SettingsScreen(self.notes_directory), handle_settings)

    def action_quit(self) -> None:
        """Quit the application (Ctrl+C handler)."""
        self.exit()

    def action_insert_hash(self) -> None:
        """Insert a '#' at the cursor (fallback for keyboards where Option+3 yields £)."""
        # Prefer focused editor
        try:
            editor = self.query_one("#editor", MarkdownEditor)
            editor.insert_text("#")
            return
        except Exception:
            pass
        # If search input focused
        try:
            file_list = self.query_one("#file-list", FileList)
            search_input = file_list.query_one("#file-search", Input)
            if search_input.has_focus:
                pos = getattr(search_input, "cursor_position", len(search_input.value))
                val = search_input.value
                search_input.value = val[:pos] + "#" + val[pos:]
                try:
                    search_input.cursor_position = pos + 1  # type: ignore[attr-defined]
                except Exception:
                    pass
        except Exception:
            pass


def run() -> None:
    """Run the SiTermText application."""
    parser = argparse.ArgumentParser(description="SiTermText - Terminal Note-Taking App")
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

    # Run the app
    app = SiTermTextApp(config)
    app.run()


if __name__ == "__main__":
    run()
