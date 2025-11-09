# GitHub Copilot Instructions for SiTermText

## Project Overview
SiTermText is a PyQt6-based note-taking application for macOS and Linux. It provides a windowed GUI with three-panel interface for managing markdown notes with wiki-style linking, clickable hashtags, full-text search, and file pinning.

**Architecture**: Native GUI application (not terminal-based), using PyQt6 for UI, plain `.md` files for storage, and background threading for performance.

**Full project plan**: [PLAN.md](../../PLAN.md)  
**Comprehensive docs**: [README.md](../../README.md)

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
- Each UI component is a QWidget in `sitermtext/gui/`
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

### File Storage
- All notes stored as plain `.md` files in user-chosen directory
- No database - file system is source of truth
- Config stored in `~/.sitermtext/config.json` with hierarchical keys
- Pins tracked per directory for portability

### Search & Indexing
- **Filename search**: Instant substring matching
- **Content search**: Background thread (ContentIndexer) builds lowercase index
- **Hashtag search**: Type hash symbol in search to filter by tag
- Debounced at 250ms to avoid excessive re-filtering while typing
- Index rebuilds on file changes, with interruption support for clean shutdown

## Common Tasks

### Adding a New GUI Component
1. Create QWidget subclass in `sitermtext/gui/`
2. Define pyqtSignal attributes for communication (type-safe events)
3. Implement `__init__` with UI layout (QVBoxLayout, QHBoxLayout, etc.)
4. Connect signals to slots in MainWindow for orchestration
5. Update MainWindow layout to include new component

### Adding a New Theme
1. Add entry to `gui/themes.py::THEMES` dict with stylesheet string
2. Include all widget selectors (QMainWindow, QListWidget, QPushButton, etc.)
3. Test with both light and dark syntax highlighting colors
4. Consider updating MarkdownHighlighter if special syntax colors needed

### Adding Keyboard Shortcuts
1. Add QShortcut in `gui/main_window.py::_setup_shortcuts()`
2. Use QKeySequence for cross-platform compatibility (Cmd vs Ctrl)
3. Connect to existing slot or create new handler method
4. Document in README.md keyboard shortcuts table

### Extending Syntax Highlighting
1. Add new QTextCharFormat in `gui/editor.py::MarkdownHighlighter._setup_formats()`
2. Consider light vs dark theme variants (use `is_light` check)
3. Add precompiled regex pattern to `__init__` for performance
4. Implement detection logic in `highlightBlock()` method

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
