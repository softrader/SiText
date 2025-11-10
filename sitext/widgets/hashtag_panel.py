"""Hashtag panel widget for displaying tags from all notes."""

from collections import Counter
from pathlib import Path
from typing import Dict, List

from textual.app import ComposeResult
from textual.containers import VerticalScroll
from textual.message import Message
from textual.reactive import reactive
from textual.widget import Widget
from textual.widgets import Label, ListItem, ListView


class HashtagPanel(Widget):
    """Widget for displaying hashtags with frequency counts."""

    DEFAULT_CSS = """
    HashtagPanel {
        height: 12;
        background: $panel;
        border-top: thick $primary;
    }

    HashtagPanel Label#hashtag-title {
        padding: 1 2;
        color: $text;
        background: $accent;
        text-style: bold;
    }

    HashtagPanel ListView {
        height: 1fr;
        background: $panel;
        padding: 0 1;
    }

    HashtagPanel ListView > ListItem {
        padding: 0 1;
        background: black;
        color: green;
    }

    HashtagPanel ListView > ListItem:hover {
        background: green;
        color: black;
    }

    HashtagPanel ListView > ListItem.--highlight {
        background: green !important;
        color: black !important;
    }
    
    HashtagPanel ListView:focus > ListItem.--highlight {
        background: green !important;
        color: black !important;
    }
    
    HashtagPanel ListView > ListItem.--highlight > * {
        background: green !important;
        color: black !important;
    }
    
    HashtagPanel ListView:focus > ListItem.--highlight > * {
        background: green !important;
        color: black !important;
    }
    """

    hashtags: reactive[Dict[str, int]] = reactive(dict, init=False)
    notes_directory: reactive[Path] = reactive(Path.home(), init=False)

    def __init__(self, notes_directory: Path, **kwargs) -> None:
        """Initialize the hashtag panel.

        Args:
            notes_directory: Directory containing markdown files
            **kwargs: Additional widget arguments
        """
        super().__init__(**kwargs)
        self.notes_directory = notes_directory

    def compose(self) -> ComposeResult:
        """Compose the hashtag panel widget."""
        yield Label("🏷️  Hashtags", id="hashtag-title")
        yield ListView(id="hashtag-list-view")

    def on_mount(self) -> None:
        """Called when widget is mounted."""
        # Defer refresh until after widgets are ready
        self.call_after_refresh(self.refresh_hashtags)

    def refresh_hashtags(self) -> None:
        """Scan all files and extract hashtags."""
        import re

        if not self.notes_directory.exists():
            self.hashtags = {}
            self.update_list_view()
            return

        # Extract hashtags from all .md files
        tag_counter: Counter[str] = Counter()
        hashtag_pattern = re.compile(r"#([a-zA-Z0-9_]+)")

        for md_file in self.notes_directory.glob("*.md"):
            try:
                content = md_file.read_text(encoding="utf-8")
                tags = hashtag_pattern.findall(content)
                tag_counter.update(tags)
            except (OSError, UnicodeDecodeError):
                # Skip files that can't be read
                continue

        # Convert to dict sorted by frequency
        self.hashtags = dict(tag_counter.most_common())
        self.update_list_view()

    def update_list_view(self) -> None:
        """Update the ListView with hashtags."""
        try:
            list_view = self.query_one("#hashtag-list-view", ListView)
        except Exception:
            # Widget not ready yet
            return
            
        list_view.clear()

        if not self.hashtags:
            list_view.append(ListItem(Label("No hashtags found")))
            return

        for tag, count in self.hashtags.items():
            list_view.append(ListItem(Label(f"#{tag} ({count})")))

    def watch_notes_directory(self, new_directory: Path) -> None:
        """Watch for changes to notes directory."""
        self.refresh_hashtags()

    def on_list_view_selected(self, event: ListView.Selected) -> None:
        """Handle hashtag selection."""
        if event.list_view.id == "hashtag-list-view":
            index = event.list_view.index
            if index is not None and 0 <= index < len(self.hashtags):
                selected_tag = list(self.hashtags.keys())[index]
                self.post_message(self.HashtagSelected(selected_tag))

    class HashtagSelected(Message):
        """Message sent when a hashtag is selected."""

        def __init__(self, hashtag: str) -> None:
            """Initialize message.

            Args:
                hashtag: Selected hashtag (without # prefix)
            """
            super().__init__()
            self.hashtag = hashtag
