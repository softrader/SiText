"""Settings screen widget for configuring the application."""

from pathlib import Path

from textual.app import ComposeResult
from textual.containers import Container, Vertical
from textual.message import Message
from textual.screen import ModalScreen
from textual.widgets import Button, Input, Label, Static


class SettingsScreen(ModalScreen):
    """Modal screen for application settings."""

    DEFAULT_CSS = """
    SettingsScreen {
        align: center middle;
    }

    SettingsScreen > Container {
        width: 80;
        height: auto;
        background: black;
        border: thick green;
        padding: 2;
    }

    SettingsScreen Label {
        color: green;
        background: black;
        margin-bottom: 1;
    }

    SettingsScreen .title {
        text-style: bold;
        color: green;
        background: black;
        text-align: center;
        margin-bottom: 2;
    }

    SettingsScreen Input {
        margin-bottom: 2;
        background: black;
        color: green;
        border: solid green;
    }

    SettingsScreen Input:focus {
        border: solid #00ff00;
    }

    SettingsScreen Button {
        margin: 1 2;
        background: green;
        color: black;
        border: none;
    }

    SettingsScreen Button:hover {
        background: #00ff00;
    }

    SettingsScreen Button:focus {
        background: #00ff00;
        text-style: bold;
    }

    SettingsScreen .button-container {
        layout: horizontal;
        align: center middle;
        height: auto;
        margin-top: 1;
    }

    SettingsScreen Static {
        color: green;
        background: black;
        margin-bottom: 1;
    }
    """

    def __init__(self, current_directory: Path, **kwargs) -> None:
        """Initialize settings screen.

        Args:
            current_directory: Current notes directory
            **kwargs: Additional screen arguments
        """
        super().__init__(**kwargs)
        self.current_directory = current_directory

    def compose(self) -> ComposeResult:
        """Compose the settings screen."""
        with Container():
            yield Label("⚙️  Settings", classes="title")
            yield Static("Notes Directory:")
            yield Input(
                value=str(self.current_directory),
                placeholder="Enter notes directory path",
                id="notes-dir-input",
            )
            yield Static("Press Enter to save, Escape to cancel")
            with Vertical(classes="button-container"):
                yield Button("Save", variant="primary", id="save-button")
                yield Button("Cancel", variant="default", id="cancel-button")

    def on_mount(self) -> None:
        """Called when screen is mounted."""
        # Focus the input field
        input_field = self.query_one("#notes-dir-input", Input)
        input_field.focus()
        input_field.cursor_position = len(input_field.value)

    def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle button presses.

        Args:
            event: Button pressed event
        """
        if event.button.id == "save-button":
            self._save_settings()
        elif event.button.id == "cancel-button":
            self.dismiss(None)

    def on_input_submitted(self, event: Input.Submitted) -> None:
        """Handle input submission (Enter key).

        Args:
            event: Input submitted event
        """
        if event.input.id == "notes-dir-input":
            self._save_settings()

    def on_key(self, event) -> None:
        """Handle key presses.

        Args:
            event: Key event
        """
        if event.key == "escape":
            self.dismiss(None)

    def _save_settings(self) -> None:
        """Save settings and dismiss screen."""
        input_field = self.query_one("#notes-dir-input", Input)
        new_path = Path(input_field.value.strip()).expanduser()

        # Validate path
        if not new_path.exists():
            try:
                new_path.mkdir(parents=True, exist_ok=True)
            except OSError:
                # TODO: Show error message
                return

        self.dismiss(new_path)

    class SettingsSaved(Message):
        """Message sent when settings are saved."""

        def __init__(self, notes_directory: Path) -> None:
            """Initialize message.

            Args:
                notes_directory: New notes directory path
            """
            super().__init__()
            self.notes_directory = notes_directory
