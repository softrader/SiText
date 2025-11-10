# Migration from TUI to GUI

SiText has been upgraded from a terminal-based interface (Textual) to a native GUI application (PyQt6).

## What Changed

### Improvements
- **Native window**: Runs in its own application window instead of terminal
- **Better keyboard support**: Native handling of Cmd/Ctrl keys, no more #/£ issues
- **Resizable panels**: Drag panel dividers to customize your layout
- **Better text editing**: Full native text editing with proper cursor, selection, and keyboard shortcuts
- **macOS integration**: Appears in Dock, supports native window management
- **No terminal quirks**: No more locale/encoding issues with special characters

### What Stayed the Same
- **Same features**: File list, markdown editor, hashtag panel, wiki-links
- **Same shortcuts**: Ctrl+J for links, Ctrl+, for settings, etc.
- **Same look**: Black/green terminal aesthetic preserved
- **Same data**: Plain `.md` files in your notes directory
- **Same config**: Uses `~/.sitext/config.json`
- **Auto-save**: Still saves 2 seconds after you stop typing

## For Existing Users

Your notes and configuration are **100% compatible**. Just install the new version:

```bash
cd ~/Development/SiText
git pull
./build_app.sh
./install.sh
```

Or copy the .app to Applications:
```bash
cp -r dist/SiText.app /Applications/
```

## Dependencies Changed

**Before (TUI):**
- textual
- rich
- pygments

**After (GUI):**
- PyQt6
- PyQt6-QScintilla (optional, not currently used)

To reinstall:
```bash
pip uninstall textual rich pygments
pip install PyQt6
```

## Old Terminal Version

The old TUI version is still available in git history:
```bash
git checkout <commit-before-gui>
```

But the GUI version is recommended for better UX and fewer keyboard issues.
