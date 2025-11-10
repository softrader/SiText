"""Markdown parsing utilities for extracting hashtags and wiki-links."""

import re
from pathlib import Path
from typing import List, Set


# Regex patterns
HASHTAG_PATTERN = re.compile(r"#([a-zA-Z0-9_]+)")
WIKILINK_PATTERN = re.compile(r"\[\[([^\]]+)\]\]")


def extract_hashtags(text: str) -> List[str]:
    """Extract all hashtags from markdown text.

    Args:
        text: Markdown content

    Returns:
        List of hashtags (without # prefix)
    """
    return HASHTAG_PATTERN.findall(text)


def extract_wikilinks(text: str) -> List[str]:
    """Extract all wiki-links from markdown text.

    Args:
        text: Markdown content

    Returns:
        List of linked filenames (without [[ ]])
    """
    return WIKILINK_PATTERN.findall(text)


def normalize_filename(filename: str) -> str:
    """Normalize a filename for matching.

    Removes .md extension if present and converts to lowercase.

    Args:
        filename: Filename to normalize

    Returns:
        Normalized filename
    """
    if filename.endswith(".md"):
        filename = filename[:-3]
    return filename.lower()


def find_wikilink_target(
    link_text: str,
    notes_directory: Path,
    current_file: Path | None = None,
    create_if_missing: bool = False
) -> Path | None:
    """Find the target file for a wiki-link with folder-aware matching.

    Supports both explicit folder paths (e.g., "projects/foo") and simple names ("foo").
    When multiple files match a simple name, prefers files in the same folder as current_file.

    Args:
        link_text: The text inside [[ ]]
        notes_directory: Directory containing markdown files
        current_file: The file containing the link (for relative matching)
        create_if_missing: If True, create the file if it doesn't exist

    Returns:
        Path to target file, or None if not found and not creating
    """
    link_text = link_text.strip()

    # Case 1: Explicit folder path (e.g., "projects/foo" or "projects/foo.md")
    if "/" in link_text:
        filename = link_text if link_text.endswith(".md") else f"{link_text}.md"
        target = notes_directory / filename
        if target.exists():
            return target
        elif create_if_missing:
            # Create parent directories if needed
            target.parent.mkdir(parents=True, exist_ok=True)
            return target
        return None

    # Case 2: Simple name - search all files recursively
    normalized_link = normalize_filename(link_text)
    matches: List[Path] = []

    for md_file in notes_directory.glob("**/*.md"):
        if normalize_filename(md_file.stem) == normalized_link:
            matches.append(md_file)

    # No matches found
    if not matches:
        if create_if_missing:
            # Create in same folder as current file, or root if no current file
            if current_file and current_file.parent != notes_directory:
                target_dir = current_file.parent
            else:
                target_dir = notes_directory
            filename = link_text if link_text.endswith(".md") else f"{link_text}.md"
            return target_dir / filename
        return None

    # Single match - return it
    if len(matches) == 1:
        return matches[0]

    # Multiple matches - prefer same folder as current file
    if current_file:
        current_dir = current_file.parent
        same_folder = [m for m in matches if m.parent == current_dir]
        if same_folder:
            return same_folder[0]

    # Fallback: return first match (or root-level if available)
    root_matches = [m for m in matches if m.parent == notes_directory]
    return root_matches[0] if root_matches else matches[0]


def get_hashtag_counts(notes_directory: Path) -> dict[str, int]:
    """Get hashtag counts from all markdown files.

    Args:
        notes_directory: Directory containing markdown files

    Returns:
        Dictionary mapping hashtags to their counts
    """
    from collections import Counter

    tag_counter: Counter[str] = Counter()

    if not notes_directory.exists():
        return {}

    for md_file in notes_directory.glob("**/*.md"):
        try:
            content = md_file.read_text(encoding="utf-8")
            tags = extract_hashtags(content)
            tag_counter.update(tags)
        except (OSError, UnicodeDecodeError):
            continue

    return dict(tag_counter)


def find_files_with_hashtag(notes_directory: Path, hashtag: str) -> List[Path]:
    """Find all files containing a specific hashtag.

    Args:
        notes_directory: Directory containing markdown files
        hashtag: Hashtag to search for (without # prefix)

    Returns:
        List of file paths containing the hashtag
    """
    matching_files: List[Path] = []

    if not notes_directory.exists():
        return matching_files

    for md_file in notes_directory.glob("**/*.md"):
        try:
            content = md_file.read_text(encoding="utf-8")
            tags = extract_hashtags(content)
            if hashtag in tags:
                matching_files.append(md_file)
        except (OSError, UnicodeDecodeError):
            continue

    return matching_files


def get_available_filenames(notes_directory: Path) -> List[str]:
    """Get list of available filenames for autocomplete.

    Args:
        notes_directory: Directory containing markdown files

    Returns:
        List of relative paths (without .md extension, e.g., "projects/foo")
    """
    if not notes_directory.exists():
        return []

    filenames = []
    for md_file in notes_directory.glob("**/*.md"):
        # Get relative path and remove .md extension
        rel_path = md_file.relative_to(notes_directory)
        filename = str(rel_path)[:-3] if str(rel_path).endswith('.md') else str(rel_path)
        filenames.append(filename)
    return filenames


def get_cursor_word(text: str, cursor_position: int) -> tuple[str, int, int]:
    """Get the word at cursor position.

    Args:
        text: Full text content
        cursor_position: Current cursor position

    Returns:
        Tuple of (word, start_position, end_position)
    """
    # Find word boundaries
    start = cursor_position
    end = cursor_position

    # Move start backwards to find word start
    while start > 0 and text[start - 1].isalnum() or (start > 0 and text[start - 1] in "_#["):
        start -= 1

    # Move end forwards to find word end
    while end < len(text) and (text[end].isalnum() or text[end] in "_]"):
        end += 1

    word = text[start:end]
    return word, start, end
