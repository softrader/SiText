# SiText - Complete Project Context

**For: ChatGPT Memory / Mobile Brainstorming**
**Last Updated:** November 9, 2025

---

## Project Overview

**SiText** is a fast, keyboard-driven note-taking application for macOS/Linux. It's built with PyQt6 and provides a native GUI with a three-panel interface for managing markdown notes with wiki-style linking, clickable hashtags, full-text search, and file pinning.

**Core Philosophy:**
- Plain `.md` files (no database)
- Keyboard-first workflow
- Fast and responsive (background threading)
- Clean, distraction-free interface
- Native macOS integration

---

## Current Features (v1.0.0)

### Editor & Markdown
- Live syntax highlighting (headers, bold, italic, code, links, hashtags, wiki-links)
- Auto-save (2-second debounce)
- Click hashtags to filter files
- Click wiki-links to open/create linked notes
- `Cmd/Ctrl+J` to follow link under cursor
- Theme-aware syntax colors (5 themes)

### File Management
- Three-panel layout: search/file-list | editor | hashtag-panel
- Pin files (right-click menu or editor button)
- Pinned files always at top of list
- Delete with confirmation (Delete/Backspace key)
- Sort by alphabetical or last modified
- Background content indexing for fast search

### Search & Navigation
- Instant filename filtering
- Full-text content search (2+ chars)
- Hashtag search: type `#tag` to filter
- ESC to focus search (double-tap for hashtag panel)
- Arrow keys navigate between search and file list

### Themes
- Dark (default), Light, Solarized Dark/Light, High Contrast
- macOS-native scrollbar styling
- Theme-aware link/hashtag colors

### Export
- **PDF Export** (Cmd+E)
  - All text pure black
  - Lists flattened to avoid red/oversized markers
  - Emoji replaced/stripped to avoid `?` characters
  - Unicode support (DejaVu fonts) with Latin-1 fallback

### Configuration
- Settings dialog (Cmd+,)
- Stored in `~/.sitext/config.json`
- Notes directory, theme, file order, ESC behavior
- Per-directory pin storage

---

## Architecture & Tech Stack

### Stack
- **Python 3.10+**
- **PyQt6 >= 6.6.0** (GUI framework)
- **markdown >= 3.5** (markdown-to-HTML conversion)
- **fpdf2 >= 2.7.0** (PDF export)
- **pathlib** (file operations)
- **watchdog** (future: file system monitoring)

### Key Design Patterns
- **Signal/Slot Communication**: All widgets emit Qt signals, MainWindow connects them
- **Background Threading**: QThread for content indexing, never block UI
- **Precompiled Regex**: Syntax highlighter compiles patterns once in `__init__`
- **Stable Partitioning**: Pinned files sorted separately, maintain order
- **Config System**: Hierarchical JSON with dot-notation access (`config.get("ui.file_order")`)

### File Structure
```
sitext/
├── config.py              # JSON config management
├── main_gui.py            # Entry point
├── gui/
│   ├── main_window.py     # Orchestration layer
│   ├── editor.py          # Markdown editor + highlighter
│   ├── file_list.py       # File browser + content indexer
│   ├── hashtag_panel.py   # Hashtag extraction/display
│   └── themes.py          # Theme stylesheets
├── utils/
│   ├── markdown_parser.py # Wiki-link/hashtag regex parsing
│   └── pdf_export.py      # PDF generation with fpdf2
└── widgets/               # (deprecated TUI components)
```

### Build & Distribution
- **PyInstaller** creates standalone `.app` bundle
- `build_app_m2.sh` for ARM64 (Apple Silicon)
- `build_app.sh` for legacy (uses system PyInstaller)
- Output: `dist/SiText.app` (~91MB)
- DMG distribution: `SiText-macOS-ARM64.dmg` (41MB compressed)

---

## Current State & Known Issues

### Completed Recently
✅ PDF export with black text and normal-sized lists  
✅ Emoji stripping/replacement to avoid `?` in PDFs  
✅ App icon integration (images/icon.icns)  
✅ Button padding matches hashtag panel  
✅ Git repo with v1.0.0 tag and DMG ready for release  

### Known Limitations
- No file renaming (must rename in Finder/terminal)
- No multi-cursor editing
- No fuzzy search (only substring matching)
- No backlinks panel (can't see what links TO a file)
- No tabs or split view
- No iOS app (macOS/Linux only)

### Technical Debt
- Legacy TUI code in `sitext/widgets/` (unused, can be removed)
- ContentIndexer doesn't handle file changes after startup (manual refresh needed)
- No automated tests
- No CI/CD pipeline

---

## Future Features (Prioritized)

### High Priority
1. **File Rename** - Right-click or Shift+Enter to rename in place
2. **Smart Cursor Navigation** - Down arrow at start of bottom line moves to end
3. **Remember Cursor Position** - Restore last cursor location when reopening file
4. **Backlinks Panel** - Show which files link TO current file
5. **Checklist Clickable** - Click `[ ]` to toggle `[x]` in editor

### Medium Priority
6. **Fuzzy File Search** - Cmd+P quick switcher
7. **In-File Search** - Cmd+F for search within current file
8. **Multi-Cursor Editing** - Cmd+D for next occurrence
9. **Git Integration** - Commit/diff from within app
10. **Daily Notes** - Cmd+D to open/create today's note
11. **Tabs** - Open multiple files in tabs
12. **Word Count** - Status bar display
13. **Line Numbers** - Optional gutter toggle

### Long-Term
14. **iOS App** - Native iOS companion with sync
    - Touch-optimized interface
    - Swipe gestures
    - Share extension
    - Offline-first with sync
15. **HTML Export** - Static site generation
16. **Image Paste** - Clipboard images into notes
17. **Encryption** - AES encryption for sensitive notes
18. **Table Editor** - WYSIWYG table mode
19. **Lazy Loading** - For large note collections (1000+ files)
20. **Plugin System** - Community extensions

---

## Development Workflow

### Running Development Version
```bash
source .venv/bin/activate  # or .venv-arm64 for ARM64
python -m sitext.main_gui
```

### Building macOS App
```bash
./build_app_m2.sh          # ARM64 (recommended)
./install.sh               # Copy to /Applications
```

### Creating Release
```bash
# Build app
./build_app_m2.sh

# Create DMG
cd dist
hdiutil create -volname "SiText" -srcfolder SiText.app \
  -ov -format UDZO SiText-macOS-ARM64.dmg

# Tag and push
git tag v1.0.1 -m "Release notes"
git push origin v1.0.1

# Upload DMG to GitHub Releases
```

---

## Code Guidelines

### Do's
✅ Use Qt signals/slots for component communication  
✅ Type hints on all functions  
✅ Docstrings (Google style) for public APIs  
✅ Handle keyboard shortcuts consistently (Cmd on macOS, Ctrl elsewhere)  
✅ Validate user input before file operations  
✅ Use QThread + signals for background I/O  
✅ Precompile regex patterns for performance  
✅ Support interruption in long-running threads  
✅ Theme-aware colors (light vs dark variants)  

### Don'ts
❌ Use `print()` - use logging or Qt debug  
❌ Block UI thread - always use QThread for I/O  
❌ Hardcode paths - use config system  
❌ Crash on errors - handle gracefully  
❌ Forget thread cleanup on shutdown  
❌ Recompile regex in loops  
❌ Use bare `except` clauses  
❌ Manipulate UI from background threads  

---

## Key Files to Reference

- **README.md** - User documentation, installation, usage
- **PLAN.md** - Original development plan and architecture decisions
- **MIGRATION.md** - TUI → GUI migration notes
- **GUI_CONVERSION.md** - GUI implementation details
- **FUTURE_FEATURES.md** - Feature wishlist (user-edited)
- **.github/copilot-instructions.md** - AI agent guidance for this codebase

---

## Questions to Brainstorm

### UX & Design
- How should file renaming work? Modal dialog vs inline edit?
- Should we show backlinks inline or in a separate panel?
- What's the best way to visualize daily notes? Calendar? List?
- How to handle conflicts in iOS sync? (for future iOS app)

### Technical
- Should we use watchdog for live file system monitoring?
- How to implement fuzzy search efficiently? (fzf algorithm? Levenshtein?)
- Best approach for remembering cursor positions? (separate JSON? in-memory cache?)
- Plugin system architecture: Python modules? Sandboxed? API surface?

### Feature Priority
- What features would make the biggest productivity impact?
- Should we focus on mobile (iOS) or more desktop features first?
- Is Git integration essential or nice-to-have?
- How important is multi-cursor editing vs other features?

---

## Contributing

This project is open source (MIT License). Feature requests and PRs welcome!

**Repo:** https://github.com/softrader/SiText  
**Release:** v1.0.0 (DMG available at GitHub Releases)

---

**Use this document to:**
- Understand the full project context
- Brainstorm new features
- Discuss architecture decisions
- Plan implementation strategies
- Keep ChatGPT informed about the project state
