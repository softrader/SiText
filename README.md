# SiText

A fast, keyboard-driven note-taking application with markdown support, wiki-style linking, and a native macOS interface.

## Features

### Core Features
- **Markdown editing** with live syntax highlighting (headers, bold, italic, code, links, hashtags)
- **Wiki-style links** - `[[link to other notes]]` - click or press Ctrl/Cmd+J to follow
- **Hashtag organization** - automatic tag extraction with frequency counts, clickable to filter
- **Pin files** - keep important notes at the top of your file list
- **Keyboard-first** - designed for speed and efficiency with comprehensive shortcuts
- **Plain text files** - all notes stored as `.md` files, no database, easy to sync
- **Powerful search** - filter by filename or file content, search hashtags with `#tag`
- **Multiple themes** - macOS native, light, dark, solarized dark/light, high contrast
- **Auto-save** - changes saved automatically after 2 seconds
- **Native GUI** - PyQt6-based windowed application with macOS styling

### Navigation & Interaction
- **Clickable hashtags** - click any `#tag` in your notes to filter the file list instantly
- **Clickable wiki-links** - click `[[links]]` to open/create linked notes
- **Context menu** - right-click files to pin/unpin
- **Double ESC** - quick navigation to hashtag panel
- **Arrow keys** - navigate between search box and file list seamlessly
- **Delete key** - delete files with confirmation prompt
- **Content search** - background indexing for fast full-text search across all notes

### Customization
- **File ordering** - sort alphabetically or by last modified date
- **Theme switching** - 5 built-in themes with proper syntax highlighting adaptation
- **Configurable directory** - set your notes folder anywhere
- **ESC behavior** - toggle text selection when pressing ESC
- **Resizable panels** - drag splitters to adjust layout

## Installation

### Prerequisites
- Python 3.10 or higher
- macOS or Linux (Windows not yet tested)
- PyQt6 (installed automatically)

### Option 1: macOS App Bundle (Recommended)

Build and install as a native macOS application:

```bash
# Clone the repository
git clone https://github.com/silasslack/sitext.git
cd SiText

# Build the .app bundle
rm -rf build dist && ./build_app.sh && ./install.sh

# The app will be installed to /Applications/SiText.app
# Drag it to your Dock for easy access!
```

**First Launch:** Double-click `SiText.app` from Applications or Spotlight.

**Note for Apple Silicon (M1/M2/M3):** For optimal performance, use ARM64 Python:
```bash
# Install ARM64 Python via Homebrew
brew install python@3.12

# Rebuild with native architecture
rm -rf build dist .venv
python3.12 -m venv .venv
source .venv/bin/activate
pip install -e .
./build_app.sh && ./install.sh
```

### Option 2: Development Install

For development or if you prefer running from terminal:

```bash
# Clone the repository
git clone https://github.com/silasslack/sitext.git
cd SiText

# Create a virtual environment
python3 -m venv .venv
source .venv/bin/activate  # On macOS/Linux

# Install with dependencies
pip install -e .

# Run directly
.venv/bin/python -m sitext.main_gui
```

### Option 3: Development with Testing Tools

```bash
# Install with dev dependencies (pytest, ruff, mypy, etc.)
pip install -e ".[dev]"
```

## Quick Start

### Launch the App
- **macOS App Bundle**: Double-click `SiText.app` from Applications or launch via Spotlight
- **Development mode**: `.venv/bin/python -m sitext.main_gui`
- **Command line** (if installed): `sitext`

### First Time Setup
1. On first launch, you'll be prompted to choose a notes directory (default: `~/Documents/Notes`)
2. The app will create the directory if it doesn't exist
3. Configuration is saved to `~/.sitext/config.json`

### Basic Workflow

#### Creating & Opening Notes
- **Search box**: Type a filename to filter, press Enter to create/open
- **File list**: Double-click or press Enter to open
- **New file**: Just type a new name in search and hit Enter

#### Writing with Markdown
- Type naturally - markdown is highlighted automatically
- **Bold**: `**text**` or `__text__`
- **Italic**: `*text*` or `_text_`
- **Headers**: `# H1`, `## H2`, etc.
- **Code**: `` `inline code` ``
- **Links**: `[text](url)` or `[[wiki-link]]`
- **Hashtags**: `#projectname` (automatically extracted)

#### Linking Notes
1. Type `[[other note]]` to create a wiki-link
2. Click the link or press Ctrl/Cmd+J when cursor is on it
3. If the note doesn't exist, it will be created automatically

#### Finding Notes
- **By filename**: Just start typing in the search box
- **By content**: Type any text (2+ chars) to search file contents
- **By hashtag**: Type `#tag` to filter files containing that tag
- **From hashtag panel**: Double-click any hashtag to filter

#### Organizing Notes
- **Pin important files**: Right-click a file and select Pin (or use the pin button in editor)
- **Pinned files** appear at the top of your file list
- **File ordering**: Settings → choose Alphabetical or Last Modified
- **Delete files**: Select file → press Delete/Backspace → confirm

## Keyboard Shortcuts

### Essential
| Key | Action |
|-----|--------|
| `Cmd/Ctrl + Q` | Quit application |
| `Cmd/Ctrl + W` | Close window |
| `Cmd/Ctrl + ,` | Open settings dialog |
| `ESC` | Focus search box (press twice for hashtag panel) |
| `Enter` | Open selected file or create new file from search |

### Navigation
| Key | Action |
|-----|--------|
| `Cmd/Ctrl + J` | Follow wiki-link under cursor |
| `↓` (in search) | Move to file list (first item) |
| `↑` (in search) | Move to file list (last item) |
| `Delete/Backspace` | Delete selected file (with confirmation) |
| Double-click | Open file, follow link, or filter by hashtag |

### Editing
| Key | Action |
|-----|--------|
| `Cmd/Ctrl + 3` | Insert `#` character |
| Auto-save | Triggered 2 seconds after you stop typing |
| Click hashtag | Filter files by that tag |
| Click wiki-link | Open/create linked note |

## Configuration

### Settings Dialog
Press `Cmd/Ctrl + ,` to open settings where you can configure:
- **Notes Directory**: Choose where your `.md` files are stored
- **Theme**: Select from 5 themes (dark, light, solarized dark/light, high contrast)
- **File Order**: Alphabetical or Last Modified
- **ESC Behavior**: Whether ESC selects all text in search box

### Configuration File
Settings are automatically saved to: `~/.sitext/config.json`

Example configuration:
```json
{
  "notes_directory": "/Users/you/Documents/Notes",
  "theme": "light",
  "ui": {
    "select_search_on_escape": true,
    "file_order": "last_modified"
  },
  "pins": {
    "by_dir": {
      "/Users/you/Documents/Notes": [
        "Important.md",
        "TODO.md"
      ]
    }
  }
}
```

### Themes

#### Available Themes
1. **dark** (default) - Classic green terminal on black
2. **light** - Clean white background with high-contrast syntax colors
3. **solarized_dark** - Ethan Schoonover's solarized dark palette
4. **solarized_light** - Solarized light variant
5. **high_contrast** - Maximum contrast black & white

#### Theme-Aware Syntax Highlighting
- Wiki-links and hashtags automatically adjust colors for readability
- Light themes use dark blue links (`#0044cc`) and orange hashtags (`#cc6600`)
- Dark themes use cyan links (`#00ffff`) and yellow-green hashtags (`#ccff00`)

## Architecture

### Project Structure
```
sitext/
├── __init__.py
├── config.py              # Configuration management & JSON persistence
├── main_gui.py            # GUI entry point (PyQt6 application)
├── main.py                # Legacy TUI entry point (deprecated)
├── gui/
│   ├── __init__.py
│   ├── main_window.py     # Main application window & orchestration
│   ├── editor.py          # Markdown editor with syntax highlighting
│   ├── file_list.py       # File browser with search & content indexing
│   ├── hashtag_panel.py   # Hashtag extraction & display
│   ├── themes.py          # Theme definitions & stylesheets
│   └── pinned_files.py    # (deprecated - pins now inline)
├── utils/
│   └── markdown_parser.py # Wiki-link & hashtag extraction utilities
└── widgets/
    └── (legacy TUI widgets - not used in GUI mode)
```

### Key Components

#### MainWindow (`gui/main_window.py`)
- Orchestrates all UI components with signal/slot connections
- Handles keyboard shortcuts and global application state
- Manages theme application and settings persistence
- Coordinates pin state between file list, config, and editor

#### MarkdownEditor (`gui/editor.py`)
- Custom QTextEdit with wiki-link and hashtag click detection
- Theme-aware syntax highlighter with precompiled regex patterns
- Auto-save with 2-second debounce timer
- Pin toggle button in header

#### FileListWidget (`gui/file_list.py`)
- Background content indexing (QThread) for fast full-text search
- Debounced search input (250ms) to avoid excessive filtering
- Stable partitioning: pinned files always at top
- Context menu for pin/unpin actions

#### ContentIndexer (`gui/file_list.py`)
- Background thread that reads all `.md` files and caches lowercased content
- Supports interruption for clean shutdown
- Enables instant substring matching across thousands of notes

### Performance Optimizations
- **Precompiled regex patterns**: Highlighter compiles patterns once, not per-line
- **Background indexing**: File content indexed in separate thread, non-blocking
- **Debounced search**: 250ms delay prevents excessive re-filtering while typing
- **Stable partitioning**: Pinned files sorted once, not on every display update
- **Thread cleanup**: ContentIndexer stops gracefully on app close to prevent warnings

## Development

### Setup Development Environment
```bash
# Clone and set up
git clone https://github.com/silasslack/sitext.git
cd SiText
python3 -m venv .venv
source .venv/bin/activate

# Install with dev tools
pip install -e ".[dev]"
```

### Development Commands
```bash
# Run from source
.venv/bin/python -m sitext.main_gui

# Build macOS app
./build_app.sh

# Install to /Applications
./install.sh

# Run tests (when implemented)
pytest

# Lint code
ruff check sitext/

# Format code
black sitext/

# Type check
mypy sitext/
```

### Code Style & Guidelines
- Follow PEP 8 (max line length: 100 characters)
- Use type hints for all function signatures
- Document public classes and methods with Google-style docstrings
- Use async patterns for I/O operations
- Never block the UI thread - use QThread for long operations
- Handle errors gracefully - log, don't crash

### Adding New Features
See [PLAN.md](PLAN.md) for the development roadmap and architecture details.

Common extension points:
- **New themes**: Add to `gui/themes.py::THEMES` dict
- **New shortcuts**: Add to `gui/main_window.py::_setup_shortcuts()`
- **Syntax highlighting**: Extend `gui/editor.py::MarkdownHighlighter._setup_formats()`
- **Settings**: Update `config.py::DEFAULT_CONFIG` and `gui/main_window.py::SettingsDialog`

## Troubleshooting

### App won't launch
- **Check Python version**: Requires Python 3.10+
  ```bash
  python3 --version
  ```
- **Reinstall dependencies**:
  ```bash
  pip uninstall PyQt6
  pip install PyQt6>=6.6.0
  ```
- **Run from terminal** to see error messages:
  ```bash
  .venv/bin/python -m sitext.main_gui
  ```

### Paste hangs or is slow
- Fixed in latest version with precompiled regex patterns
- Update to latest code: `git pull && pip install -e .`

### QThread warning on quit
- Fixed in latest version with proper thread shutdown
- Ensure you're running the latest code

### Files not appearing
- Check notes directory in Settings (Cmd/Ctrl+,)
- Ensure directory exists and contains `.md` files
- Try refreshing: close and reopen the app

### Search not finding content
- Wait a few seconds for initial indexing to complete
- Search requires at least 2 characters
- Content search works only on indexed files (auto-indexes on startup)

### Wiki-links or hashtags not working
- Links must be formatted as `[[filename]]` or `[[filename.md]]`
- Hashtags must be `#alphanumeric_` (no spaces or special chars)
- Click directly on the text or press Cmd/Ctrl+J when cursor is inside

## License

MIT License - see LICENSE file for details.

## Credits

Created by Silas Slack
Built with PyQt6 and Python
