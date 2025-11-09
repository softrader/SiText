"""Configuration management for SiTermText."""

import json
import os
from pathlib import Path
from typing import Any, Dict, Optional


class Config:
    """Manages application configuration."""

    DEFAULT_CONFIG = {
        "notes_directory": "~/Documents/Notes",
        "theme": "macos_native",
        "editor": {
            "auto_save": True,
            "auto_save_delay": 2,
            "word_wrap": True,
            "line_numbers": True,
            "tab_size": 2,
        },
        "ui": {
            "file_list_width": 30,
            "hashtag_panel_height": 10,
            "select_search_on_escape": True,
            "file_order": "alphabetical",  # or 'last_modified'
        },
        # Pinned files are stored per-notes-directory to avoid collisions across different workspaces
        # Structure: { "by_dir": { "/abs/path/to/notes": ["File1.md", "File2.md"] } }
        "pins": {
            "by_dir": {}
        },
    }

    def __init__(self, config_path: Optional[Path] = None) -> None:
        """Initialize configuration.

        Args:
            config_path: Optional path to config file. Defaults to ~/.sitermtext/config.json
        """
        if config_path is None:
            config_path = Path.home() / ".sitermtext" / "config.json"

        self.config_path = config_path
        self._config: Dict[str, Any] = {}
        self.load()

    def load(self) -> None:
        """Load configuration from file, or create default if it doesn't exist."""
        if self.config_path.exists():
            try:
                with open(self.config_path, "r") as f:
                    self._config = json.load(f)
                # Merge with defaults for any missing keys
                self._config = self._merge_with_defaults(self._config)
            except (json.JSONDecodeError, OSError) as e:
                print(f"Error loading config: {e}. Using defaults.")
                self._config = self.DEFAULT_CONFIG.copy()
        else:
            self._config = self.DEFAULT_CONFIG.copy()
            self.save()

    def save(self) -> None:
        """Save configuration to file."""
        self.config_path.parent.mkdir(parents=True, exist_ok=True)
        try:
            with open(self.config_path, "w") as f:
                json.dump(self._config, f, indent=2)
        except OSError as e:
            print(f"Error saving config: {e}")

    def _merge_with_defaults(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """Merge user config with defaults."""
        result = self.DEFAULT_CONFIG.copy()
        for key, value in config.items():
            if key in result and isinstance(result[key], dict) and isinstance(value, dict):
                result[key] = {**result[key], **value}
            else:
                result[key] = value
        return result

    def get(self, key: str, default: Any = None) -> Any:
        """Get a configuration value.

        Args:
            key: Configuration key (supports dot notation like 'editor.auto_save')
            default: Default value if key doesn't exist

        Returns:
            Configuration value or default
        """
        keys = key.split(".")
        value = self._config
        for k in keys:
            if isinstance(value, dict) and k in value:
                value = value[k]
            else:
                return default
        return value

    def set(self, key: str, value: Any) -> None:
        """Set a configuration value.

        Args:
            key: Configuration key (supports dot notation like 'editor.auto_save')
            value: Value to set
        """
        keys = key.split(".")
        config = self._config
        for k in keys[:-1]:
            if k not in config:
                config[k] = {}
            config = config[k]
        config[keys[-1]] = value

    # ----- Pinned files helpers -----
    def _dir_key(self, notes_dir: Path) -> str:
        """Normalize notes directory path for use as a JSON key."""
        return str(notes_dir.expanduser().resolve())

    def get_pinned_for_dir(self, notes_dir: Path) -> list[str]:
        """Return list of pinned filenames (with extension) for a notes directory."""
        pins = self.get("pins.by_dir", {}) or {}
        return list(pins.get(self._dir_key(notes_dir), []))

    def set_pinned_for_dir(self, notes_dir: Path, filenames: list[str]) -> None:
        """Replace pinned list for a directory and persist in-memory structure (call save() to persist)."""
        pins = self.get("pins.by_dir", {}) or {}
        pins[self._dir_key(notes_dir)] = list(dict.fromkeys(filenames))  # dedupe & keep order
        self.set("pins.by_dir", pins)

    def add_pin(self, notes_dir: Path, filename: str) -> None:
        """Add a filename to pins for a directory (idempotent)."""
        current = self.get_pinned_for_dir(notes_dir)
        if filename not in current:
            current.append(filename)
            self.set_pinned_for_dir(notes_dir, current)

    def remove_pin(self, notes_dir: Path, filename: str) -> None:
        """Remove a filename from pins for a directory (no-op if absent)."""
        current = self.get_pinned_for_dir(notes_dir)
        new_list = [f for f in current if f != filename]
        if len(new_list) != len(current):
            self.set_pinned_for_dir(notes_dir, new_list)

    @property
    def notes_directory(self) -> Path:
        """Get the notes directory path.

        Checks in order:
        1. Environment variable SITERMTEXT_DIR
        2. Config file setting
        3. Default ~/Documents/Notes

        Returns:
            Path to notes directory
        """
        # Check environment variable first
        env_dir = os.environ.get("SITERMTEXT_DIR")
        if env_dir:
            return Path(env_dir).expanduser()

        # Then check config
        config_dir = self.get("notes_directory")
        if config_dir:
            return Path(config_dir).expanduser()

        # Fall back to default
        return Path.home() / "Documents" / "Notes"

    def ensure_notes_directory(self) -> Path:
        """Ensure the notes directory exists.

        Returns:
            Path to notes directory

        Raises:
            OSError: If directory cannot be created
        """
        notes_dir = self.notes_directory
        notes_dir.mkdir(parents=True, exist_ok=True)
        return notes_dir
