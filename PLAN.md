# SiTermText - Terminal Note-Taking App Plan

## Overview
A terminal-based note-taking application for macOS/Linux with markdown support, wiki-style linking, and smart organization features.

## Technology Stack
- **Language**: Python 3.10+
- **TUI Framework**: Textual (modern terminal UI with rich features)
- **Markdown**: python-markdown for rendering/parsing
- **Syntax Highlighting**: Pygments
- **File Handling**: watchdog for file system monitoring

## Core Features

### 1. Three-Panel Layout
```
┌─────────────────────┬──────────────────────────────┐
│ Search: [______]    │                              │
│                     │                              │
│ Files:              │   Markdown Editor            │
│ - note1.md          │   # Title                    │
│ - note2.md          │                              │
│ - project.md        │   Content with [[links]]     │
│ - ideas.md          │   and **markdown** support   │
│                     │                              │
│ ─────────────────── │                              │
│ Hashtags:           │                              │
│ #important (12)     │                              │
│ #work (8)           │                              │
│ #personal (5)       │                              │
└─────────────────────┴──────────────────────────────┘
```

### 2. File List (Left Panel - Top)
- Display all `.md` files from custom directory
- Search box at top (filter files as you type)
- Keyboard navigation (up/down arrows)
- Enter to open file
- ESC always returns focus here
- Auto-refresh when files change

### 3. Hashtag Panel (Left Panel - Bottom)
- Extract hashtags from all markdown files
- Display frequency count
- Sort by usage (most used at top)
- Click or select to filter files by tag
- Real-time updates as files are edited

### 4. Markdown Editor (Right Panel)
- Full markdown syntax highlighting
- Auto-completion for:
  - Markdown syntax (`#`, `**`, `*`, `-`, etc.)
  - Wiki-links `[[filename]]` - shows list of available files
  - Hashtags `#` - shows existing tags
- Wiki-link navigation:
  - `[[filename]]` creates link to other note
  - Click or Ctrl+Enter to follow link
  - Creates new file if doesn't exist
- Save on Ctrl+S (or auto-save option)
- Line numbers (optional)
- Word wrap

### 5. File Storage
- Files stored as plain `.md` files
- Custom directory configurable via:
  - Config file (`~/.sitermtext/config.json`)
  - Command line argument (`--notes-dir /path/to/notes`)
  - Environment variable (`SITERMTEXT_DIR`)
- Default: `~/Documents/Notes`

## Technical Architecture

### Project Structure
```
sitermtext/
├── sitermtext/
│   ├── __init__.py
│   ├── main.py              # Entry point, Textual app
│   ├── config.py            # Configuration management
│   ├── widgets/
│   │   ├── __init__.py
│   │   ├── file_list.py     # File browser widget
│   │   ├── hashtag_panel.py # Hashtag display widget
│   │   └── editor.py        # Markdown editor widget
│   ├── models/
│   │   ├── __init__.py
│   │   ├── note.py          # Note file model
│   │   └── hashtag.py       # Hashtag extraction/management
│   └── utils/
│       ├── __init__.py
│       ├── markdown_parser.py  # Parse markdown, extract links/tags
│       └── file_watcher.py     # Monitor file system changes
├── tests/
│   └── ...
├── pyproject.toml
├── README.md
└── requirements.txt
```

### Key Components

#### 1. Main Application (`main.py`)
- Textual App class
- Layout management (grid/horizontal/vertical)
- Keyboard shortcuts (ESC, Ctrl+S, Ctrl+Q, etc.)
- Focus management between panels

#### 2. FileList Widget (`widgets/file_list.py`)
- Display `.md` files from directory
- Search/filter functionality
- File selection handling
- File creation/deletion

#### 3. HashtagPanel Widget (`widgets/hashtag_panel.py`)
- Scan all files for `#hashtag` patterns
- Count and sort by frequency
- Filter files by selected tag
- Update on file changes

#### 4. Editor Widget (`widgets/editor.py`)
- TextArea with markdown syntax highlighting
- Autocomplete provider for:
  - Markdown syntax
  - `[[wiki-links]]` - file suggestions
  - `#hashtags` - existing tag suggestions
- Link detection and navigation
- Save functionality

#### 5. MarkdownParser (`utils/markdown_parser.py`)
- Extract hashtags from content
- Parse `[[wiki-links]]`
- Syntax validation

#### 6. Config Management (`config.py`)
- Load/save configuration
- Notes directory setting
- Theme preferences
- Editor settings (auto-save, word wrap, etc.)

## Implementation Phases

### Phase 1: Project Setup ✓
- Create project structure
- Setup dependencies (Textual, watchdog, etc.)
- Configuration system
- Basic app shell

### Phase 2: Basic Layout
- Three-panel layout
- File list display (no search yet)
- Basic text editor (no highlighting)
- File loading/saving

### Phase 3: File Management
- Search box with filtering
- File creation/deletion
- File watcher integration
- ESC key navigation

### Phase 4: Markdown Features
- Syntax highlighting
- Markdown autocomplete
- Preview rendering (optional)

### Phase 5: Wiki Links
- `[[link]]` detection
- Autocomplete for filenames
- Navigation between notes
- Create new notes from links

### Phase 6: Hashtag System
- Hashtag extraction
- Hashtag panel display
- Frequency counting
- Filter by tag

### Phase 7: Polish
- Themes/colors
- Configuration UI
- Help screen
- Error handling
- Testing

## Dependencies

```toml
[project]
dependencies = [
    "textual>=0.40.0",           # TUI framework
    "markdown>=3.5",             # Markdown parsing
    "pygments>=2.16",            # Syntax highlighting
    "watchdog>=3.0",             # File system monitoring
    "rich>=13.0",                # Rich text formatting
]
```

## Configuration Format

```json
{
  "notes_directory": "~/Documents/Notes",
  "theme": "dark",
  "editor": {
    "auto_save": true,
    "auto_save_delay": 2,
    "word_wrap": true,
    "line_numbers": true,
    "tab_size": 2
  },
  "ui": {
    "file_list_width": 30,
    "hashtag_panel_height": 10
  }
}
```

## Keyboard Shortcuts

| Key | Action |
|-----|--------|
| `ESC` | Return to file list |
| `Ctrl+S` | Save current file |
| `Ctrl+N` | New file |
| `Ctrl+Q` | Quit application |
| `Ctrl+F` | Focus search box |
| `Ctrl+O` | Open file selector |
| `Ctrl+Enter` | Follow wiki link |
| `Tab` | Next panel |
| `Shift+Tab` | Previous panel |

## Future Enhancements
- [ ] Full-text search across all notes
- [ ] Export to HTML/PDF
- [ ] Git integration for versioning
- [ ] Encrypted notes
- [ ] Note templates
- [ ] Task list support with checkboxes
- [ ] Daily note quick access
- [ ] Graph view of note connections
- [ ] Sync with cloud storage
- [ ] Mobile app companion

## Success Criteria
- Fast startup (<500ms)
- Smooth navigation between notes
- Reliable autocomplete
- No data loss (auto-save/backup)
- Intuitive keyboard-first workflow
- Cross-platform compatibility (macOS/Linux)
