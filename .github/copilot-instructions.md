# GitHub Copilot Instructions for SiText

## Project Overview
SiText is a fast, keyboard-driven note-taking application for macOS and Linux. Built with PyQt6, it provides a native GUI with three-panel interface for managing markdown notes with wiki-style linking, clickable hashtags, full-text search, and file pinning.

**Architecture**: Native GUI application using PyQt6 for UI, plain `.md` files for storage, and background threading (QThread) for performance. Migrated from terminal UI (Textual) to native GUI for better macOS integration and keyboard handling.

**Key Files**: [README.md](../../README.md) | [PLAN.md](../../PLAN.md) | [MIGRATION.md](../../MIGRATION.md) | [GUI_CONVERSION.md](../../GUI_CONVERSION.md)

**Build Tool**: PyInstaller creates standalone macOS .app bundle (see `build_app.sh` and `SiText.spec`)

## Code Style & Conventions

### Python Standards
- Use Python 3.10+ features (type hints, match statements, structural pattern matching)
- Follow PEP 8 style guide strictly
- Use type hints for all function signatures and class attributes
- Docstrings for all public classes and methods (Google style preferred)
- Maximum line length: 100 characters
- Use `from __future__ import annotations` for forward references

### Project-Specific Guidelines
- **PyQt6 framework**: Use Qt's signal/slot mechanism for component communication
- **Threading**: Use QThread for background work (file indexing, I/O), never block UI thread
- **Async patterns**: While PyQt is callback-based, use QThread + signals for long operations
- **Error handling**: Graceful degradation with user-friendly error messages, never crash
- **Logging**: Use Python's logging module for debug info, not print statements
- **Type safety**: Leverage PyQt6's type stubs; prefer explicit types over `Any`

## Architecture Patterns

### Component Structure (PyQt6)
- Each UI component is a QWidget in `sitext/gui/`
- Components communicate via Qt signals and slots (type-safe, decoupled)
- Keep widgets focused: single responsibility principle
- Main orchestration happens in `MainWindow`, not individual widgets

### File Operations
- Use pathlib.Path for all file paths (type-safe, cross-platform)
- Background I/O via QThread to avoid blocking UI
- Validate paths before operations; handle OSError, UnicodeDecodeError gracefully
- Always use UTF-8 encoding with errors='ignore' fallback for content indexing

### Markdown Processing & Parsing
- Core parsing utilities in `utils/markdown_parser.py`
- Extract hashtags with regex: `r'#([a-zA-Z0-9_]+)'`
- Extract wiki-links with regex: `r'\[\[([^\]]+)\]\]'`
- Normalize filenames: case-insensitive, optional .md extension
- Syntax highlighting via QSyntaxHighlighter with precompiled patterns (performance)

## Key Features to Remember

### Wiki-Links
- Format: `[[filename]]` or `[[filename.md]]` (both valid)
- Clickable in editor (single click) or keyboard shortcut Cmd/Ctrl+J
- Following a link to non-existent file creates it automatically
- Links are case-insensitive for matching
- Parsed with regex: `r'\[\[([^\]]+)\]\]'`

### Hashtags
- Format: hash symbol followed by alphanumeric or underscore
- Extract from all files, count frequency, display in panel (sorted by count)
- Clickable: clicking a hashtag in editor filters file list instantly
- Clicking in hashtag panel also filters files
- Update when files are saved (via hashtag_panel.refresh_hashtags())

### File Pinning
- Pin via context menu (right-click file) or editor header button
- Pinned files stored per-directory in config: `pins.by_dir`
- Display inline at top of file list with pin emoji prefix
- Stable partitioning: pinned first, then unpinned (both maintain sort order)

### Navigation & Shortcuts
- **ESC**: Focus search box; double-tap focuses hashtag panel
- **Enter** (in search): Open selected file or create new from search text
- **Cmd/Ctrl+J**: Follow wiki-link at cursor position
- **Cmd/Ctrl+,**: Open settings dialog
- **Arrow keys**: Navigate between search input and file list seamlessly
- **Delete/Backspace**: Delete selected file (with confirmation)

### File Storage & Configuration
- All notes stored as plain `.md` files in user-chosen directory (supports nested folders)
- No database - file system is source of truth
- Config stored in `~/.sitext/config.json` with hierarchical keys (dot notation: `config.get("ui.file_order")`)
- Pins tracked per directory in `pins.by_dir` for workspace portability
- Config class provides helper methods: `get_pinned_for_dir()`, `add_pin()`, `remove_pin()`, `ensure_notes_directory()`
- Environment variable `SITEXT_DIR` overrides config setting for notes directory

### Search & Indexing
- **Filename search**: Instant substring matching
- **Content search**: Background thread (ContentIndexer) builds lowercase index
- **Hashtag search**: Type hash symbol in search to filter by tag
- Debounced at 250ms to avoid excessive re-filtering while typing
- Index rebuilds on file changes, with interruption support for clean shutdown

## Common Development Tasks

### Building & Running
```bash
# Development mode (with virtual environment)
source .venv/bin/activate
python -m sitext.main_gui

# Build standalone macOS .app bundle
./build_app.sh  # Uses PyInstaller with SiText.spec
./install.sh    # Copies to /Applications/

# Run built app
open dist/SiText.app
```

**Important**: Built app targets Apple Silicon (arm64). For Intel or cross-compilation, modify `target_arch` in `SiText.spec`.

### Adding a New GUI Component
1. Create QWidget subclass in `sitext/gui/`
2. Define pyqtSignal attributes for communication (type-safe events)
3. Implement `__init__` with UI layout (QVBoxLayout, QHBoxLayout, etc.)
4. Connect signals to slots in MainWindow for orchestration
5. Update MainWindow layout to include new component

**Example Signal Pattern**:
```python
# In widget (sitext/gui/my_widget.py)
from PyQt6.QtCore import pyqtSignal
class MyWidget(QWidget):
    something_happened = pyqtSignal(Path, str)  # Typed signals

    def _do_something(self):
        self.something_happened.emit(file_path, "data")

# In MainWindow (sitext/gui/main_window.py)
self.my_widget.something_happened.connect(self._handle_event)

def _handle_event(self, path: Path, data: str):
    # Handle in main thread, coordinate with other widgets
    pass
```

### Adding a New Theme
1. Add entry to `gui/themes.py::THEMES` dict with Qt stylesheet (QSS) string
2. Include all widget selectors: `QMainWindow`, `QListWidget`, `QTextEdit`, `QLineEdit`, `QPushButton`, `QDialog`, `QComboBox`, `QStatusBar`, `QSplitter::handle`, `QScrollBar`
3. Update `gui/editor.py::MarkdownHighlighter._setup_formats()` to detect your theme:
   ```python
   is_light = self.theme in ("light", "solarized_light", "macos_native", "your_theme")
   ```
4. Test both light and dark syntax highlighting variants (links, hashtags, headers)
5. Consider macOS-style scrollbars if targeting native look (see `macos_native` theme)

**Theme Detection**: Light themes use dark blue links (`#0044cc`), dark themes use cyan (`#00ffff`)

### Adding Keyboard Shortcuts
1. Add QShortcut in `gui/main_window.py::_setup_shortcuts()`
2. Use QKeySequence for cross-platform compatibility (Cmd vs Ctrl)
3. Connect to existing slot or create new handler method
4. Document in README.md keyboard shortcuts table

### Extending Syntax Highlighting
1. Add new QTextCharFormat in `gui/editor.py::MarkdownHighlighter._setup_formats()`
2. Theme-aware colors: check `is_light` boolean, provide light/dark variants
3. **Critical**: Precompile regex pattern in `__init__` (NEVER in `highlightBlock()`):
   ```python
   def __init__(self, ...):
       self.my_pattern = re.compile(r'pattern')  # Compile ONCE
   
   def highlightBlock(self, text: str):
       for match in self.my_pattern.finditer(text):  # Reuse compiled pattern
           self.setFormat(match.start(), match.end() - match.start(), self.my_format)
   ```
4. Current patterns: headers (6 levels), bold, italic, code, links, URLs, wiki-links, hashtags
5. Call `self.rehighlight()` when theme changes to reapply all formats

### Adding Background Work
1. Create QThread subclass (similar to ContentIndexer)
2. Emit signals for results (never manipulate UI from thread)
3. Support interruption: check `isInterruptionRequested()` in loops
4. Clean up in parent widget's `shutdown()` method or destructor
5. Request interruption and `wait()` before starting new instance

## Testing Guidelines
- Test widgets independently with mock signals
- Test markdown parsing with edge cases (nested brackets, special chars)
- Test file operations with temporary directories (use pytest fixtures)
- Test threading: verify clean shutdown without "QThread: Destroyed" warnings
- Integration tests for full workflows (create → edit → save → search → delete)

## Dependencies
- **PyQt6**: GUI framework (>=6.6.0)
- **markdown**: Markdown utilities (>=3.5) - minimal usage
- **pathlib**: File path operations (stdlib)
- **re**: Regex for parsing (stdlib)
- **json**: Config persistence (stdlib)

## Don't
- ❌ Use print() - use logging module or Qt debug messages
- ❌ Block the UI thread - use QThread for I/O, never time.sleep() on main thread
- ❌ Hardcode paths - use config system and pathlib.Path
- ❌ Crash on errors - handle gracefully with try/except and user messages
- ❌ Forget thread cleanup - always stop and wait for QThreads on shutdown
- ❌ Recompile regex in loops - precompile patterns in __init__
- ❌ Use bare except clauses - catch specific exceptions
- ❌ Manipulate UI from background threads - always emit signals instead

## Do
- ✅ Use Qt signals/slots for loose coupling between components
- ✅ Handle keyboard shortcuts consistently (Cmd on macOS, Ctrl elsewhere)
- ✅ Validate user input before file operations
- ✅ Keep widgets focused and single-purpose
- ✅ Use QThread + signals for background I/O operations
- ✅ Test edge cases (empty files, missing directories, unicode, large files)
- ✅ Precompile regex patterns for syntax highlighting performance
- ✅ Support interruption in long-running thread operations
- ✅ Use type hints and leverage PyQt6's type stubs
- ✅ Apply consistent theme colors (light vs dark variants)

## Code Quality Checklist
Before committing changes, verify:
- [ ] No syntax errors (`get_errors` tool)
- [ ] Type hints on all new functions
- [ ] Docstrings for public APIs (Google style)
- [ ] No blocking operations on UI thread
- [ ] Signals properly connected in MainWindow
- [ ] Theme-aware colors if adding UI elements
- [ ] Clean thread shutdown if adding background work
- [ ] Updated README.md if adding user-facing features
- [ ] Keyboard shortcuts documented

## Performance Considerations
- **Regex compilation**: Compile once in __init__, not per-call
- **Search debouncing**: Use QTimer with 250ms delay for search inputs
- **Background indexing**: Use QThread for file content scanning
- **Stable partitioning**: Sort pinned/unpinned lists once, not per display
- **Signal blocking**: Use blockSignals() when programmatically setting widget state
- **Lazy loading**: Don't load all file contents upfront (use indexing instead)

## References & Resources
- [PyQt6 Documentation](https://www.riverbankcomputing.com/static/Docs/PyQt6/)
- [Qt for Python](https://doc.qt.io/qtforpython/)
- [Project Plan](../../PLAN.md)
- [README.md](../../README.md)
