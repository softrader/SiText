# Claude AI Instructions for SiText

## Project Identity
**SiText** - A fast, keyboard-driven note-taking application built with PyQt6 for macOS and Linux. Provides a clean windowed GUI for managing markdown notes with wiki-style linking, clickable hashtags, full-text search, and file pinning.

**Architecture**: Native GUI (PyQt6), plain `.md` file storage, background threading for performance.

## Quick Context

### What This App Does
- Manages a directory of plain markdown `.md` files
- Three-panel layout: file list (left), editor (center), hashtags (right)
- Wiki-links (`[[other note]]`) navigate between notes
- Hashtags (`#project`) are extracted, counted, and filterable
- Background content indexing for fast full-text search
- Files can be pinned to top of list
- Multiple themes with adaptive syntax highlighting
- Auto-save after 2 seconds of inactivity

### Tech Stack
- **Python 3.10+** with type hints throughout
- **PyQt6** for GUI (signals/slots pattern)
- **QThread** for background work (content indexing)
- **QSyntaxHighlighter** for markdown syntax coloring
- Plain **JSON** for config (`~/.sitext/config.json`)
- No database - filesystem is source of truth

## Critical Architecture Patterns

### Component Communication
- **Never** directly call methods across components
- **Always** use Qt signals and slots for component interaction
- MainWindow orchestrates; widgets emit signals upward
- Example:
  ```python
  # In widget
  file_selected = pyqtSignal(Path)
  self.file_selected.emit(file_path)
  
  # In MainWindow
  self.file_list.file_selected.connect(self._open_file)
  ```

### Threading Rules
- **UI thread only**: All QWidget manipulation, signal emissions
- **Background QThread**: File I/O, content indexing, heavy parsing
- **Always** support interruption via `isInterruptionRequested()`
- **Always** clean up threads in shutdown/destructor methods
- **Never** access UI from background thread - emit signals instead
- Example pattern:
  ```python
  class MyWorker(QThread):
      finished = pyqtSignal(object)
      
      def run(self):
          for item in items:
              if self.isInterruptionRequested():
                  break
              result = process(item)
          self.finished.emit(results)
  ```

### File Operations
- Use `pathlib.Path` exclusively (not string paths)
- All file reads: `path.read_text(encoding="utf-8", errors="ignore")`
- Handle OSError and UnicodeDecodeError gracefully
- Never crash on missing files - log and inform user
- Config updates: modify dict, then call `config.save()`

## Code Patterns to Follow

### Adding New Features
1. **New signal?** Define in widget class: `my_event = pyqtSignal(DataType)`
2. **New UI component?** Create QWidget subclass in `sitext/gui/`
3. **Background work?** Create QThread subclass with interruption support
4. **New setting?** Add to `config.py::DEFAULT_CONFIG`, then update SettingsDialog
5. **New shortcut?** Add QShortcut in `MainWindow._setup_shortcuts()`

### Markdown Parsing
- Precompile regex patterns in `__init__` (never in loops)
- Wiki-links: `r'\[\[([^\]]+)\]\]'` - captures link text
- Hashtags: `r'#([a-zA-Z0-9_]+)'` - alphanumeric + underscore only
- Case-insensitive filename matching via `normalize_filename()`
- Extract in `utils/markdown_parser.py`, apply in widgets

### Syntax Highlighting
- Subclass QSyntaxHighlighter, override `highlightBlock(text)`
- Precompile all regex patterns in `__init__` (major performance win)
- Support theme switching: store theme, rebuild formats, call `rehighlight()`
- Light themes need high contrast: dark blues/oranges, not pastels
- Dark themes can use bright colors: cyan, yellow-green
- Format pattern:
  ```python
  format = QTextCharFormat()
  format.setForeground(QColor("#0044cc"))
  format.setFontUnderline(True)
  self.setFormat(start, length, format)
  ```

### Theme Handling
- Themes defined in `gui/themes.py::THEMES` dict (Qt stylesheets)
- Apply via `setStyleSheet(get_stylesheet(theme_key))`
- Syntax highlighter checks `is_light = theme in ("light", "solarized_light")`
- Always test both light and dark modes when changing colors
- Update both MainWindow stylesheet AND editor highlighter on theme change

## Project Structure Deep Dive

```
sitext/
├── config.py              # Config persistence (JSON), pin management
├── main_gui.py            # Entry point: QApplication setup
├── main.py                # (deprecated TUI entry - ignore)
│
├── gui/                   # All PyQt6 UI components
│   ├── main_window.py     # Orchestrator: signals, shortcuts, theme
│   ├── editor.py          # MarkdownEditor + WikiLinkTextEdit + Highlighter
│   ├── file_list.py       # FileListWidget + ContentIndexer (QThread)
│   ├── hashtag_panel.py   # HashtagPanel (aggregates, sorts by frequency)
│   ├── themes.py          # Theme definitions (Qt stylesheets)
│   └── pinned_files.py    # (deprecated - pins now inline)
│
├── utils/
│   └── markdown_parser.py # Wiki-link & hashtag extraction functions
│
└── widgets/               # (deprecated TUI widgets - ignore)
```

### Key Files to Know

#### `gui/main_window.py` - The Orchestrator
- **MainWindow**: QMainWindow subclass, owns all components
- **SettingsDialog**: Modal dialog for config (directory, theme, ordering)
- Connects all signals to handlers (`_open_file`, `_on_file_saved`, etc.)
- Manages keyboard shortcuts (ESC, Cmd+J, Cmd+,)
- Applies themes to both UI and editor syntax highlighting
- Calls `file_list.shutdown()` on close for clean thread exit

#### `gui/editor.py` - Text Editing
- **WikiLinkTextEdit**: Custom QTextEdit with click detection for links/hashtags
- **MarkdownHighlighter**: Syntax highlighting with theme awareness
- **MarkdownEditor**: Container widget with header (title + pin button)
- Emits: `file_saved`, `wiki_link_clicked`, `hashtag_clicked`, `pin_toggled`
- Auto-saves via QTimer (2 second debounce)
- Precompiles 7 regex patterns in highlighter `__init__`

#### `gui/file_list.py` - File Browser & Search
- **FileListWidget**: Search input + file list + context menu
- **ContentIndexer**: QThread that builds lowercase content index
- Debounced search (250ms QTimer) to avoid excessive re-filtering
- Stable partitioning: pinned files always at top with 📌 emoji
- Supports filename search, content search, and hashtag filtering (`#tag`)
- Background indexer checks `isInterruptionRequested()` for clean shutdown

#### `gui/hashtag_panel.py` - Tag Display
- Scans all `.md` files on refresh
- Extracts hashtags, counts frequency (Counter)
- Displays sorted by frequency (most common first)
- Double-click or Enter emits `hashtag_selected` signal
- MainWindow connects to populate search with `#tag`

#### `config.py` - Settings Persistence
- JSON config at `~/.sitext/config.json`
- Dot notation access: `config.get("ui.file_order", "alphabetical")`
- Pin storage: `pins.by_dir[abs_dir_path] = ["file1.md", "file2.md"]`
- Helper methods: `get_pinned_for_dir()`, `add_pin()`, `remove_pin()`
- Always call `config.save()` after modifications

## Common Development Tasks

### Adding a New Theme
```python
# In gui/themes.py
THEMES["my_theme"] = """
    QMainWindow, QWidget { background-color: #...; color: #...; }
    QListWidget, QTextEdit, QLineEdit { ... }
    QPushButton { ... }
    ...
"""

# In gui/editor.py MarkdownHighlighter._setup_formats()
is_light = self.theme in ("light", "solarized_light", "my_theme")
# Adjust colors based on is_light
```

### Adding a New Keyboard Shortcut
```python
# In gui/main_window.py _setup_shortcuts()
my_shortcut = QShortcut(QKeySequence("Ctrl+K"), self)
my_shortcut.activated.connect(self._my_handler)

# For cross-platform Cmd/Ctrl:
my_shortcut_ctrl = QShortcut(QKeySequence("Ctrl+K"), self)
my_shortcut_ctrl.activated.connect(self._my_handler)
my_shortcut_meta = QShortcut(QKeySequence("Meta+K"), self)
my_shortcut_meta.activated.connect(self._my_handler)
```

### Adding Background Processing
```python
# Create QThread subclass
class MyProcessor(QThread):
    finished = pyqtSignal(object)
    
    def __init__(self, data):
        super().__init__()
        self._data = data
    
    def run(self):
        results = []
        for item in self._data:
            if self.isInterruptionRequested():
                break
            results.append(process(item))
        self.finished.emit(results)

# In widget
self.processor = MyProcessor(data)
self.processor.finished.connect(self._on_results)
self.processor.start()

# In widget shutdown/destructor
def shutdown(self):
    if self.processor.isRunning():
        self.processor.requestInterruption()
        self.processor.wait(500)
```

### Adding a New Signal
```python
# In widget class
from PyQt6.QtCore import pyqtSignal
from pathlib import Path

class MyWidget(QWidget):
    # Define signal with type
    something_happened = pyqtSignal(Path, str, bool)
    
    def do_something(self):
        # Emit signal
        self.something_happened.emit(path, "data", True)

# In MainWindow
self.my_widget.something_happened.connect(self._handle_something)

def _handle_something(self, path: Path, data: str, flag: bool):
    # Handle the event
    pass
```

## Performance Guidelines

### DO
- ✅ Precompile regex patterns once in `__init__`
- ✅ Use debounced timers for search inputs (250ms)
- ✅ Run file I/O in QThread background workers
- ✅ Check `isInterruptionRequested()` in loops
- ✅ Use `blockSignals(True)` when setting widget state programmatically
- ✅ Cache parsed results when possible
- ✅ Use stable partitioning (sort once, not per display)

### DON'T
- ❌ Compile regex in `highlightBlock()` or other per-call methods
- ❌ Trigger filtering on every keystroke (use debounce)
- ❌ Read files synchronously on UI thread
- ❌ Forget to wait for threads in shutdown
- ❌ Emit signals from background threads (emit from run(), not helpers)
- ❌ Re-read config on every access (cache in memory)

## Testing & Quality

### Before Committing
- [ ] No syntax errors (`get_errors` tool in VS Code)
- [ ] Type hints on all new functions/methods
- [ ] Google-style docstrings for public APIs
- [ ] No blocking operations on UI thread
- [ ] Clean thread shutdown (no "QThread: Destroyed" warnings)
- [ ] Theme-aware colors if touching UI
- [ ] Updated README.md if user-facing feature
- [ ] Keyboard shortcut documented if added

### Manual Testing Checklist
- [ ] Light and dark themes both work
- [ ] Pasting large text doesn't hang
- [ ] App quits cleanly without thread warnings
- [ ] Wiki-links work (click and Cmd+J)
- [ ] Hashtags are clickable and filter correctly
- [ ] Pin/unpin via context menu and header button
- [ ] Search finds content (not just filenames)
- [ ] Settings persist across restarts
- [ ] File deletion works with confirmation

## Edge Cases to Handle

### File Operations
- Directory doesn't exist → create it
- File encoding errors → use `errors="ignore"`
- Permission denied → show error dialog, don't crash
- File deleted externally → remove from list gracefully
- File renamed externally → refresh list

### Wiki-Links
- `[[NonExistent]]` → create file automatically
- `[[file with spaces]]` → handle correctly
- `[[UPPERCASE]]` → case-insensitive matching
- `[[already open]]` → just switch focus, don't reload
- Nested brackets → regex should handle via non-greedy match

### Hashtags
- Multiple `#tags #in #one #line` → extract all
- `#123numbers` → valid (alphanumeric allowed)
- `#with-dash` → invalid (stops at dash)
- `#end.` → captures "end" only (no punctuation)
- Empty file → no hashtags, show "No hashtags found"

### Threading
- App closes during indexing → request interruption, wait briefly
- Multiple rapid refreshes → cancel previous, start new
- Thread never finishes → timeout after reasonable period
- Memory leaks → ensure threads are properly deleted

## Gotchas & Common Mistakes

1. **Forgetting to emit signals upward** - Widgets should emit, not call MainWindow methods directly
2. **Accessing UI from background thread** - Always emit signal from `run()`, handle in main thread
3. **Not checking interruption** - Long-running threads must check `isInterruptionRequested()`
4. **Hardcoded paths** - Use pathlib.Path and config system, never string literals
5. **Recompiling regex in loops** - Compile once in `__init__`, reuse in methods
6. **Forgetting theme variants** - Test both light and dark, adjust colors accordingly
7. **Not calling blockSignals()** - Programmatic widget updates can trigger unwanted signal cascades
8. **Direct file path access** - Always go through config for notes_directory, never assume location

## Debugging Tips

### UI Not Updating?
- Check if signal is emitted: add `print()` before `emit()`
- Check if slot is connected: search for `.connect(` in MainWindow
- Check if slot is called: add `print()` in handler method
- Use `blockSignals()` if recursive signal issues

### Thread Issues?
- Add `print(f"Thread {QThread.currentThread()}")` to identify which thread
- Check if `isInterruptionRequested()` is being checked
- Verify `wait()` is called before app exit
- Look for "QThread: Destroyed while thread is still running" warning

### Search Not Working?
- Check if ContentIndexer is running: `self._index_ready` flag
- Verify files are `.md` extension
- Ensure search query is lowercase (index is lowercased)
- Check debounce timer hasn't blocked recent keystroke

### Syntax Highlighting Broken?
- Verify regex patterns compile without errors
- Check if `highlightBlock()` is being called (add debug print)
- Test light vs dark theme variants
- Ensure `rehighlight()` called after theme change

## Resources & References

- **PyQt6 Docs**: https://www.riverbankcomputing.com/static/Docs/PyQt6/
- **Qt for Python**: https://doc.qt.io/qtforpython/
- **Project README**: [README.md](README.md) - User-facing documentation
- **Project Plan**: [PLAN.md](PLAN.md) - Original design document (may be outdated)
- **Python Type Hints**: Use `from __future__ import annotations` for forward refs

## Philosophy & Design Principles

### User Experience
- **Keyboard-first**: Every action should have a keyboard shortcut
- **Fast & responsive**: Use background threads, never block UI
- **Forgiving**: Create missing files, handle errors gracefully, no data loss
- **Plain text**: Users own their data, no proprietary formats
- **Portable**: Config + notes = fully portable between machines

### Code Quality
- **Type safety**: Use type hints everywhere, leverage PyQt6 stubs
- **Signal-driven**: Components communicate via signals, not direct calls
- **Single responsibility**: Each widget does one thing well
- **Testable**: Pure functions in utils/, widgets mockable via signals
- **Maintainable**: Clear names, docstrings, consistent patterns

### Performance
- **Lazy loading**: Don't load all file contents upfront
- **Background indexing**: Build search index in separate thread
- **Debouncing**: Wait for user to pause before filtering
- **Caching**: Parse once, cache results (hashtag counts, etc.)
- **Precompilation**: Compile regex/patterns once, not per-use

---

**Remember**: This is a notes app for *power users*. It should be blazing fast, keyboard-driven, and never lose data. When in doubt, favor simplicity and reliability over features.
