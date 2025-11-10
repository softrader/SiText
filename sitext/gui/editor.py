"""Markdown editor widget with syntax highlighting and auto-save."""

import re
from pathlib import Path
from typing import Optional

from PyQt6.QtCore import Qt, QTimer, pyqtSignal, QUrl, QRect, QPoint
from PyQt6.QtGui import QColor, QFont, QMouseEvent, QSyntaxHighlighter, QTextCharFormat, QTextCursor, QImage, QTextDocument, QPainter, QPixmap
from PyQt6.QtWidgets import (
    QApplication,
    QLabel,
    QPushButton,
    QHBoxLayout,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)


class WikiLinkTextEdit(QTextEdit):
    """Custom QTextEdit that handles clicking on wiki-links and hyperlinks."""

    link_clicked = pyqtSignal(str)  # Emits the link text when clicked
    hashtag_clicked = pyqtSignal(str)  # Emits hashtag text (without leading #)
    url_clicked = pyqtSignal(str)  # Emits URL when shift+clicked

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setMouseTracking(True)
        self.setAcceptDrops(True)  # Enable drag and drop
        self.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.customContextMenuRequested.connect(self._show_context_menu)
        
        # Store notes directory for image saving (will be set by parent)
        self.notes_directory = None
        
        # Image preview overlay
        self._image_preview_label = None
        self._preview_timer = QTimer()
        self._preview_timer.setSingleShot(True)
        self._preview_timer.timeout.connect(self._show_image_preview)
        self._current_hover_image = None

        # Autocomplete setup
        from PyQt6.QtWidgets import QCompleter
        from PyQt6.QtCore import QStringListModel

        self.completer = QCompleter(self)
        self.completer.setWidget(self)
        self.completer.setCaseSensitivity(Qt.CaseSensitivity.CaseInsensitive)
        self.completer_model = QStringListModel(self)
        self.completer.setModel(self.completer_model)
        self.completer.activated.connect(self._insert_completion)

        # Track what we're completing (wikilink or hashtag)
        self._completion_mode = None  # "wikilink" or "hashtag"
        self._completion_start = 0

        # Lists for completion
        self._available_files = []
        self._available_hashtags = []

    def mousePressEvent(self, event: QMouseEvent):
        """Handle mouse clicks to detect wiki-link, hashtag, and URL clicks."""
        if event.button() == Qt.MouseButton.LeftButton:
            cursor = self.cursorForPosition(event.pos())
            cursor_pos = cursor.position()
            full_text = self.toPlainText()

            # Shift+Click: Check for hyperlinks (markdown links and bare URLs)
            if event.modifiers() & Qt.KeyboardModifier.ShiftModifier:
                # Check markdown links [text](url)
                markdown_link_pattern = re.compile(r'\[([^\]]+)\]\(([^\)]+)\)')
                for match in markdown_link_pattern.finditer(full_text):
                    start, end = match.span()
                    if start <= cursor_pos < end:
                        url = match.group(2)
                        self.url_clicked.emit(url)
                        event.accept()
                        return

                # Check bare URLs (http:// or https://)
                url_pattern = re.compile(r'https?://[^\s\)\]]+')
                for match in url_pattern.finditer(full_text):
                    start, end = match.span()
                    if start <= cursor_pos < end:
                        url = match.group(0)
                        self.url_clicked.emit(url)
                        event.accept()
                        return

            # Regular click: Check wiki-links
            wikilink_pattern = re.compile(r'\[\[([^\]]+)\]\]')
            for match in wikilink_pattern.finditer(full_text):
                start, end = match.span()
                if start <= cursor_pos < end:
                    link_text = match.group(1)
                    self.link_clicked.emit(link_text)
                    event.accept()
                    return

            # Regular click: Check hashtags
            hashtag_pattern = re.compile(r'#([a-zA-Z0-9_]+)')
            for match in hashtag_pattern.finditer(full_text):
                start, end = match.span()
                if start <= cursor_pos < end:
                    tag = match.group(1)
                    self.hashtag_clicked.emit(tag)
                    event.accept()
                    return

            # Regular click: Check checkboxes to toggle
            checkbox_pattern = re.compile(r'(\[ \]|\[\*\]|\[x\]|\[X\])')
            for match in checkbox_pattern.finditer(full_text):
                start, end = match.span()
                if start <= cursor_pos < end:
                    # Toggle checkbox state
                    current_state = match.group(1)
                    if current_state == '[ ]':
                        new_state = '[*]'
                    else:
                        new_state = '[ ]'
                    
                    # Replace in document
                    cursor.setPosition(start)
                    cursor.setPosition(end, QTextCursor.MoveMode.KeepAnchor)
                    cursor.insertText(new_state)
                    event.accept()
                    return

        # Default behavior
        super().mousePressEvent(event)

    def mouseMoveEvent(self, event: QMouseEvent):
        """Handle mouse move to show pointer cursor over clickable elements and image previews."""
        cursor = self.cursorForPosition(event.pos())
        cursor_pos = cursor.position()
        full_text = self.toPlainText()

        # Check if cursor is over any clickable element
        is_clickable = False

        # Check wiki-links
        wikilink_pattern = re.compile(r'\[\[([^\]]+)\]\]')
        for match in wikilink_pattern.finditer(full_text):
            start, end = match.span()
            if start <= cursor_pos < end:
                is_clickable = True
                break

        # Check hashtags
        if not is_clickable:
            hashtag_pattern = re.compile(r'#([a-zA-Z0-9_]+)')
            for match in hashtag_pattern.finditer(full_text):
                start, end = match.span()
                if start <= cursor_pos < end:
                    is_clickable = True
                    break

        # Check checkboxes
        if not is_clickable:
            checkbox_pattern = re.compile(r'(\[ \]|\[\*\]|\[x\]|\[X\])')
            for match in checkbox_pattern.finditer(full_text):
                start, end = match.span()
                if start <= cursor_pos < end:
                    is_clickable = True
                    break

        # Check URLs (with shift modifier visible hint)
        if not is_clickable:
            url_pattern = re.compile(r'https?://[^\s\)\]]+|\[([^\]]+)\]\(([^\)]+)\)')
            for match in url_pattern.finditer(full_text):
                start, end = match.span()
                if start <= cursor_pos < end:
                    is_clickable = True
                    break

        # Check for image markdown syntax and show preview
        image_pattern = re.compile(r'!\[([^\]]*)\]\(([^\)]+)\)')
        hovering_image = None
        for match in image_pattern.finditer(full_text):
            start, end = match.span()
            if start <= cursor_pos < end:
                hovering_image = match.group(2)
                break
        
        if hovering_image:
            if self._current_hover_image != hovering_image:
                self._current_hover_image = hovering_image
                self._preview_timer.start(500)  # Show preview after 500ms hover
        else:
            self._current_hover_image = None
            self._preview_timer.stop()
            self._hide_image_preview()

        # Set cursor shape
        from PyQt6.QtGui import QCursor
        if is_clickable:
            self.viewport().setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        else:
            self.viewport().setCursor(QCursor(Qt.CursorShape.IBeamCursor))

        # Default behavior
        super().mouseMoveEvent(event)

    def set_available_files(self, files: list[str]):
        """Set the list of available files for autocomplete."""
        self._available_files = files

    def set_available_hashtags(self, hashtags: list[str]):
        """Set the list of available hashtags for autocomplete."""
        self._available_hashtags = hashtags

    def set_notes_directory(self, notes_directory: Path):
        """Set the notes directory for image saving."""
        self.notes_directory = notes_directory

    def _show_image_preview(self):
        """Show image preview overlay."""
        if not self._current_hover_image or not self.notes_directory:
            return
        
        # Resolve image path
        image_path = self.notes_directory / self._current_hover_image
        if not image_path.exists():
            return
        
        # Load image
        pixmap = QPixmap(str(image_path))
        if pixmap.isNull():
            return
        
        # Scale image if too large (max 400px wide)
        if pixmap.width() > 400:
            pixmap = pixmap.scaledToWidth(400, Qt.TransformationMode.SmoothTransformation)
        
        # Create or update preview label
        if not self._image_preview_label:
            self._image_preview_label = QLabel(self)
            self._image_preview_label.setStyleSheet("""
                QLabel {
                    background-color: white;
                    border: 2px solid #333;
                    border-radius: 4px;
                    padding: 4px;
                }
            """)
            self._image_preview_label.setWindowFlags(Qt.WindowType.ToolTip)
        
        self._image_preview_label.setPixmap(pixmap)
        self._image_preview_label.adjustSize()
        
        # Position preview near cursor
        cursor_rect = self.cursorRect()
        global_pos = self.mapToGlobal(cursor_rect.bottomRight())
        self._image_preview_label.move(global_pos.x() + 10, global_pos.y() + 10)
        self._image_preview_label.show()
        self._image_preview_label.raise_()
    
    def _hide_image_preview(self):
        """Hide image preview overlay."""
        if self._image_preview_label:
            self._image_preview_label.hide()

    def _show_context_menu(self, position):
        """Show context menu for images."""
        from PyQt6.QtWidgets import QMenu
        
        cursor = self.cursorForPosition(position)
        cursor_pos = cursor.position()
        full_text = self.toPlainText()
        
        # Check if cursor is on an image
        image_pattern = re.compile(r'!\[([^\]]*)\]\(([^\)]+)\)')
        for match in image_pattern.finditer(full_text):
            start, end = match.span()
            if start <= cursor_pos < end:
                image_path = match.group(2)
                menu = QMenu(self)
                ocr_action = menu.addAction("OCR with OpenAI Vision API")
                action = menu.exec(self.mapToGlobal(position))
                
                if action == ocr_action:
                    self._ocr_image(match, image_path)
                return
    
    def _ocr_image(self, match, image_path_str):
        """OCR an image using OpenAI Vision API and replace with text."""
        from PyQt6.QtWidgets import QMessageBox
        import base64
        import json
        
        if not self.notes_directory:
            return
        
        # Get API key from config
        from sitext.config import Config
        config = Config()
        api_key = config.get("openai.api_key", "").strip()
        
        if not api_key:
            QMessageBox.warning(
                self,
                "API Key Required",
                "Please set your OpenAI API key in Settings first."
            )
            return
        
        # Resolve image path
        image_path = self.notes_directory / image_path_str
        if not image_path.exists():
            QMessageBox.warning(
                self,
                "Image Not Found",
                f"Image file not found: {image_path_str}"
            )
            return
        
        # Get parent window for notifications
        parent_window = self.window()
        
        # Show progress notification
        if hasattr(parent_window, 'notifications'):
            parent_window.notifications.show("📸 Sending image to OpenAI Vision API...", duration=5000)
        
        try:
            # Read and encode image
            with open(image_path, 'rb') as img_file:
                image_data = base64.b64encode(img_file.read()).decode('utf-8')
            
            # Determine image format
            ext = image_path.suffix.lower()
            mime_types = {
                '.png': 'image/png',
                '.jpg': 'image/jpeg',
                '.jpeg': 'image/jpeg',
                '.gif': 'image/gif',
                '.webp': 'image/webp'
            }
            mime_type = mime_types.get(ext, 'image/png')
            
            # Call OpenAI Vision API
            import urllib.request
            import ssl
            
            url = "https://api.openai.com/v1/chat/completions"
            headers = {
                "Content-Type": "application/json",
                "Authorization": f"Bearer {api_key}"
            }
            
            data = {
                "model": "gpt-4o-mini",
                "messages": [
                    {
                        "role": "user",
                        "content": [
                            {
                                "type": "text",
                                "text": "Please extract all text from this image. Return only the extracted text, nothing else."
                            },
                            {
                                "type": "image_url",
                                "image_url": {
                                    "url": f"data:{mime_type};base64,{image_data}"
                                }
                            }
                        ]
                    }
                ],
                "max_tokens": 1000
            }
            
            req = urllib.request.Request(
                url,
                data=json.dumps(data).encode('utf-8'),
                headers=headers
            )
            
            # Create SSL context with certifi CA bundle
            try:
                import certifi
                ssl_context = ssl.create_default_context(cafile=certifi.where())
            except ImportError:
                # Fallback: create unverified context (less secure but works)
                ssl_context = ssl._create_unverified_context()
            
            with urllib.request.urlopen(req, timeout=30, context=ssl_context) as response:
                result = json.loads(response.read().decode('utf-8'))
                extracted_text = result['choices'][0]['message']['content']
            
            # Insert extracted text after the image (keep image for reference)
            cursor = self.textCursor()
            cursor.setPosition(match.end())
            cursor.insertText(f"\n\n{extracted_text}\n")
            
            # Show success notification
            if hasattr(parent_window, 'notifications'):
                parent_window.notifications.show("✅ Text extracted and inserted below image!", duration=3000)
            
        except Exception as e:
            QMessageBox.critical(
                self,
                "OCR Failed",
                f"Failed to extract text from image:\n{str(e)}"
            )

    def canInsertFromMimeData(self, source):
        """Check if we can insert from mime data (for paste/drop)."""
        if source.hasImage() or source.hasUrls():
            return True
        return super().canInsertFromMimeData(source)

    def insertFromMimeData(self, source):
        """Handle pasting images."""
        if source.hasImage():
            image = source.imageData()
            if image and self.notes_directory:
                self._insert_image(image)
                return
        elif source.hasUrls():
            # Handle dropped image files
            for url in source.urls():
                if url.isLocalFile():
                    file_path = Path(url.toLocalFile())
                    if file_path.suffix.lower() in ('.png', '.jpg', '.jpeg', '.gif', '.bmp', '.svg'):
                        self._insert_image_from_file(file_path)
                        return
        
        # Default behavior for text
        super().insertFromMimeData(source)

    def _insert_image(self, image):
        """Save pasted image and insert markdown syntax."""
        from PyQt6.QtGui import QImage
        from datetime import datetime
        
        if not self.notes_directory:
            return
        
        # Create images directory if it doesn't exist
        images_dir = self.notes_directory / "images"
        images_dir.mkdir(exist_ok=True)
        
        # Generate filename with timestamp
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"pasted_{timestamp}.png"
        filepath = images_dir / filename
        
        # Save the image
        if isinstance(image, QImage):
            image.save(str(filepath), "PNG")
        
        # Insert markdown syntax
        cursor = self.textCursor()
        cursor.insertText(f"![image](images/{filename})\n")

    def _insert_image_from_file(self, source_path: Path):
        """Copy dropped image file and insert markdown syntax."""
        from shutil import copy2
        
        if not self.notes_directory:
            return
        
        # Create images directory if it doesn't exist
        images_dir = self.notes_directory / "images"
        images_dir.mkdir(exist_ok=True)
        
        # Copy file to images directory
        dest_path = images_dir / source_path.name
        
        # If file exists, add number to make unique
        counter = 1
        while dest_path.exists():
            stem = source_path.stem
            suffix = source_path.suffix
            dest_path = images_dir / f"{stem}_{counter}{suffix}"
            counter += 1
        
        copy2(source_path, dest_path)
        
        # Insert markdown syntax
        cursor = self.textCursor()
        cursor.insertText(f"![image](images/{dest_path.name})\n")

    def keyPressEvent(self, event):
        """Handle key press events for autocomplete."""
        # Let completer handle its own keys
        if self.completer.popup().isVisible():
            if event.key() in (Qt.Key.Key_Enter, Qt.Key.Key_Return, Qt.Key.Key_Escape, Qt.Key.Key_Tab):
                event.ignore()
                return

        # Handle Enter key for checkbox/bullet/numbered list auto-continuation
        if event.key() in (Qt.Key.Key_Enter, Qt.Key.Key_Return):
            cursor = self.textCursor()
            block_text = cursor.block().text()
            
            # Check if current line starts with a checkbox
            checkbox_match = re.match(r'^(\s*)(\[ \]|\[\*\]|\[x\]|\[X\])\s*(.*)$', block_text)
            if checkbox_match:
                indent = checkbox_match.group(1)
                checkbox_type = checkbox_match.group(2)
                content = checkbox_match.group(3)
                
                # If there's no content after the checkbox, remove the checkbox on current line
                if not content.strip():
                    # Move to start of line
                    cursor.movePosition(QTextCursor.MoveOperation.StartOfBlock)
                    # Select to end of line
                    cursor.movePosition(QTextCursor.MoveOperation.EndOfBlock, QTextCursor.MoveMode.KeepAnchor)
                    # Delete the checkbox line
                    cursor.removeSelectedText()
                    # Insert newline
                    super().keyPressEvent(event)
                    return
                
                # Otherwise, insert newline with new unchecked checkbox
                super().keyPressEvent(event)
                cursor = self.textCursor()
                cursor.insertText(f"{indent}[ ] ")
                return
            
            # Check if current line starts with a bullet point (- or * or •)
            bullet_match = re.match(r'^(\s*)([-*•])\s+(.*)$', block_text)
            if bullet_match:
                indent = bullet_match.group(1)
                bullet_char = bullet_match.group(2)
                content = bullet_match.group(3)
                
                # If there's no content after the bullet, remove the bullet on current line
                if not content.strip():
                    cursor.movePosition(QTextCursor.MoveOperation.StartOfBlock)
                    cursor.movePosition(QTextCursor.MoveOperation.EndOfBlock, QTextCursor.MoveMode.KeepAnchor)
                    cursor.removeSelectedText()
                    super().keyPressEvent(event)
                    return
                
                # Otherwise, insert newline with new bullet
                super().keyPressEvent(event)
                cursor = self.textCursor()
                cursor.insertText(f"{indent}{bullet_char} ")
                return
            
            # Check if current line starts with a numbered list (1. 2. etc.)
            numbered_match = re.match(r'^(\s*)(\d+)\.\s+(.*)$', block_text)
            if numbered_match:
                indent = numbered_match.group(1)
                current_num = int(numbered_match.group(2))
                content = numbered_match.group(3)
                
                # If there's no content after the number, remove the number on current line
                if not content.strip():
                    cursor.movePosition(QTextCursor.MoveOperation.StartOfBlock)
                    cursor.movePosition(QTextCursor.MoveOperation.EndOfBlock, QTextCursor.MoveMode.KeepAnchor)
                    cursor.removeSelectedText()
                    super().keyPressEvent(event)
                    return
                
                # Otherwise, insert newline with next number
                super().keyPressEvent(event)
                cursor = self.textCursor()
                cursor.insertText(f"{indent}{current_num + 1}. ")
                return

        # Default behavior
        super().keyPressEvent(event)

        # Check if we should trigger autocomplete
        cursor = self.textCursor()
        text = self.toPlainText()
        pos = cursor.position()

        # Look backwards to find if we're in a wikilink or hashtag context
        if pos >= 2:
            # Check for wikilink context [[
            if text[max(0, pos-2):pos] == "[[" or (pos >= 3 and text[pos-2:pos-1] == "[["):
                self._start_wikilink_completion(cursor, pos)
            # Check if we're continuing a wikilink
            elif "[[" in text[:pos]:
                last_open = text[:pos].rfind("[[")
                last_close = text[:pos].rfind("]]")
                if last_open > last_close:  # We're inside a wikilink
                    self._update_wikilink_completion(cursor, text, last_open + 2, pos)

        # Check for hashtag context
        if pos >= 1 and text[pos-1:pos] == "#":
            # Make sure previous char is whitespace or start of line
            if pos == 1 or text[pos-2:pos-1] in (' ', '\n', '\t'):
                self._start_hashtag_completion(cursor, pos)
        # Check if we're continuing a hashtag
        elif "#" in text[:pos]:
            # Find the last hashtag start
            for i in range(pos-1, -1, -1):
                if text[i] == '#' and (i == 0 or text[i-1] in (' ', '\n', '\t')):
                    # Check if we're still in this hashtag (no whitespace after #)
                    hashtag_text = text[i+1:pos]
                    if ' ' not in hashtag_text and '\n' not in hashtag_text:
                        self._update_hashtag_completion(cursor, text, i + 1, pos)
                    break

    def _start_wikilink_completion(self, cursor, pos):
        """Start autocomplete for wiki-links."""
        self._completion_mode = "wikilink"
        self._completion_start = pos
        self.completer_model.setStringList(self._available_files)
        self.completer.setCompletionPrefix("")

        rect = self.cursorRect(cursor)
        rect.setWidth(self.completer.popup().sizeHintForColumn(0)
                     + self.completer.popup().verticalScrollBar().sizeHint().width())
        self.completer.complete(rect)

    def _update_wikilink_completion(self, cursor, text, start, pos):
        """Update autocomplete for wiki-links as user types."""
        prefix = text[start:pos]
        self._completion_mode = "wikilink"
        self._completion_start = start
        self.completer_model.setStringList(self._available_files)
        self.completer.setCompletionPrefix(prefix)

        if len(prefix) > 0:
            rect = self.cursorRect(cursor)
            rect.setWidth(self.completer.popup().sizeHintForColumn(0)
                         + self.completer.popup().verticalScrollBar().sizeHint().width())
            self.completer.complete(rect)

    def _start_hashtag_completion(self, cursor, pos):
        """Start autocomplete for hashtags."""
        self._completion_mode = "hashtag"
        self._completion_start = pos
        self.completer_model.setStringList(self._available_hashtags)
        self.completer.setCompletionPrefix("")

        rect = self.cursorRect(cursor)
        rect.setWidth(self.completer.popup().sizeHintForColumn(0)
                     + self.completer.popup().verticalScrollBar().sizeHint().width())
        self.completer.complete(rect)

    def _update_hashtag_completion(self, cursor, text, start, pos):
        """Update autocomplete for hashtags as user types."""
        prefix = text[start:pos]
        self._completion_mode = "hashtag"
        self._completion_start = start
        self.completer_model.setStringList(self._available_hashtags)
        self.completer.setCompletionPrefix(prefix)

        if len(prefix) > 0:
            rect = self.cursorRect(cursor)
            rect.setWidth(self.completer.popup().sizeHintForColumn(0)
                         + self.completer.popup().verticalScrollBar().sizeHint().width())
            self.completer.complete(rect)

    def _insert_completion(self, completion):
        """Insert the selected completion."""
        cursor = self.textCursor()

        # Remove the partial text that was typed
        current_pos = cursor.position()
        chars_to_remove = current_pos - self._completion_start

        for _ in range(chars_to_remove):
            cursor.deletePreviousChar()

        # Insert the completion
        cursor.insertText(completion)

        # For wikilinks, also add the closing ]]
        if self._completion_mode == "wikilink":
            cursor.insertText("]]")

        self.setTextCursor(cursor)


class MarkdownHighlighter(QSyntaxHighlighter):
    """Syntax highlighter for markdown."""

    def __init__(self, parent=None, theme="dark"):
        super().__init__(parent)
        
        self.theme = theme
        self.formats = {}
        
        # Precompile regex patterns once to avoid per-line recompilation cost
        self._re_header = re.compile(r'^(#{1,6})\s+(.*)$')
        self._re_bold = [re.compile(r'\*\*(.+?)\*\*'), re.compile(r'__(.+?)__')]
        self._re_italic = [re.compile(r'\*(.+?)\*'), re.compile(r'_(.+?)_')]
        self._re_code = re.compile(r'`([^`]+)`')
        self._re_wikilink = re.compile(r'\[\[([^\]]+)\]\]')
        self._re_link = re.compile(r'\[([^\]]+)\]\(([^\)]+)\)')
        self._re_url = re.compile(r'https?://[^\s\)\]]+')  # Bare URLs
        self._re_hashtag = re.compile(r'#([a-zA-Z0-9_]+)')
        self._re_checkbox_unchecked = re.compile(r'(\[ \])')
        self._re_checkbox_checked = re.compile(r'(\[\*\]|\[x\]|\[X\])')
        
        self._setup_formats()
    
    def _setup_formats(self):
        """Configure text formats based on current theme."""
        # Determine if we're using a light or dark theme
        is_light = self.theme in ("light", "solarized_light", "macos_native")

        # Headers - more subtle green
        header_format = QTextCharFormat()
        header_format.setForeground(QColor("#2d7a2d" if is_light else "#5da65d"))
        header_format.setFontWeight(QFont.Weight.Bold)
        self.formats['header'] = header_format

        # Bold - darker, less neon
        bold_format = QTextCharFormat()
        bold_format.setForeground(QColor("#1d5d1d" if is_light else "#4d8d4d"))
        bold_format.setFontWeight(QFont.Weight.Bold)
        self.formats['bold'] = bold_format

        # Italic - muted green
        italic_format = QTextCharFormat()
        italic_format.setForeground(QColor("#3d6d3d" if is_light else "#6d9d6d"))
        italic_format.setFontItalic(True)
        self.formats['italic'] = italic_format

        # Code - brownish instead of bright yellow-green
        code_format = QTextCharFormat()
        code_format.setForeground(QColor("#8b6914" if is_light else "#b8923d"))
        code_format.setFontFamily("Monaco")
        self.formats['code'] = code_format

        # Links (markdown and bare URLs) - blue
        link_format = QTextCharFormat()
        link_format.setForeground(QColor("#0066cc" if is_light else "#4da6ff"))
        link_format.setFontUnderline(True)
        self.formats['link'] = link_format

        # Wiki-links - purple
        wikilink_format = QTextCharFormat()
        wikilink_format.setForeground(QColor("#9933cc" if is_light else "#cc99ff"))
        wikilink_format.setFontUnderline(True)
        self.formats['wikilink'] = wikilink_format

        # Hashtags - orange instead of yellow-green
        hashtag_format = QTextCharFormat()
        hashtag_format.setForeground(QColor("#cc6600" if is_light else "#e68a00"))
        hashtag_format.setFontWeight(QFont.Weight.Bold)
        self.formats['hashtag'] = hashtag_format

        # Checkboxes - unchecked (gray)
        checkbox_unchecked_format = QTextCharFormat()
        checkbox_unchecked_format.setForeground(QColor("#888888"))
        checkbox_unchecked_format.setFontWeight(QFont.Weight.Bold)
        self.formats['checkbox_unchecked'] = checkbox_unchecked_format

        # Checkboxes - checked (green)
        checkbox_checked_format = QTextCharFormat()
        checkbox_checked_format.setForeground(QColor("#2d7a2d" if is_light else "#5da65d"))
        checkbox_checked_format.setFontWeight(QFont.Weight.Bold)
        self.formats['checkbox_checked'] = checkbox_checked_format
    
    def update_theme(self, theme):
        """Update highlighting colors when theme changes."""
        self.theme = theme
        self._setup_formats()
        self.rehighlight()

    def highlightBlock(self, text: str):
        """Highlight a single block of text."""
        # Headers (# ## ###)
        match = self._re_header.match(text)
        if match:
            self.setFormat(0, len(text), self.formats['header'])
            return

        # Inline code (`code`) - apply early to avoid conflicts
        for match in self._re_code.finditer(text):
            self.setFormat(match.start(), match.end() - match.start(), self.formats['code'])

        # Bold (**text** or __text__)
        for pattern in self._re_bold:
            for match in pattern.finditer(text):
                self.setFormat(match.start(), match.end() - match.start(), self.formats['bold'])

        # Italic (*text* or _text_)
        for pattern in self._re_italic:
            for match in pattern.finditer(text):
                self.setFormat(match.start(), match.end() - match.start(), self.formats['italic'])

        # Hashtags (#tag)
        for match in self._re_hashtag.finditer(text):
            self.setFormat(match.start(), match.end() - match.start(), self.formats['hashtag'])

        # Checkboxes - unchecked [ ]
        for match in self._re_checkbox_unchecked.finditer(text):
            self.setFormat(match.start(), match.end() - match.start(), self.formats['checkbox_unchecked'])

        # Checkboxes - checked [*] [x] [X]
        for match in self._re_checkbox_checked.finditer(text):
            self.setFormat(match.start(), match.end() - match.start(), self.formats['checkbox_checked'])

        # Links should be applied last to override other formatting
        # Wiki-links ([[link]]) - purple
        for match in self._re_wikilink.finditer(text):
            self.setFormat(match.start(), match.end() - match.start(), self.formats['wikilink'])

        # Markdown links ([text](url)) - blue
        for match in self._re_link.finditer(text):
            self.setFormat(match.start(), match.end() - match.start(), self.formats['link'])

        # Bare URLs (http:// or https://) - blue
        for match in self._re_url.finditer(text):
            self.setFormat(match.start(), match.end() - match.start(), self.formats['link'])


class MarkdownEditor(QWidget):
    """Widget for editing markdown files with syntax highlighting."""

    file_saved = pyqtSignal(Path)
    wiki_link_clicked = pyqtSignal(Path)
    hashtag_clicked = pyqtSignal(str)  # Emits tag (without #)
    pin_toggled = pyqtSignal(Path, bool)
    export_requested = pyqtSignal(Path)  # Emits current file to export

    def __init__(self, notes_directory: Path, config=None, parent=None):
        super().__init__(parent)
        self.notes_directory = notes_directory
        self.config = config
        self.current_file: Optional[Path] = None
        self._is_modified = False
        self._auto_save_timer = QTimer()
        self._auto_save_timer.setSingleShot(True)
        self._auto_save_timer.timeout.connect(self._auto_save)

        layout = QVBoxLayout()
        layout.setContentsMargins(5, 5, 5, 5)
        layout.setSpacing(5)

        # Title bar with pin toggle
        header = QHBoxLayout()
        header.setContentsMargins(0, 0, 0, 0)
        header.setSpacing(6)
        self.title_label = QLabel("No file open")
        self.title_label.setStyleSheet("font-weight: bold; padding: 5px;")
        header.addWidget(self.title_label)
        header.addStretch()

        # Export PDF button
        self.export_button = QPushButton("Export PDF")
        self.export_button.setToolTip("Export this note to PDF (Ctrl+E)")
        self.export_button.setEnabled(False)
        self.export_button.clicked.connect(self._on_export_clicked)
        header.addWidget(self.export_button)

        # Pin button
        self.pin_button = QPushButton("📌")
        self.pin_button.setCheckable(True)
        self.pin_button.setToolTip("Pin this file (shows at top of file list)")
        self.pin_button.setEnabled(False)
        self.pin_button.clicked.connect(self._on_pin_clicked)
        header.addWidget(self.pin_button)

        layout.addLayout(header)

        # Text editor with wiki-link support
        self.text_edit = WikiLinkTextEdit()
        self.text_edit.setAcceptRichText(False)  # Plain text mode, images shown as overlay preview
        self.text_edit.set_notes_directory(notes_directory)
        
        # Set monospace font
        font = QFont("Monaco", 13)
        if not font.exactMatch():
            font = QFont("Menlo", 13)
        if not font.exactMatch():
            font = QFont("Courier New", 13)
        self.text_edit.setFont(font)
        
        self.text_edit.textChanged.connect(self._on_text_changed)
        self.text_edit.link_clicked.connect(self._open_wikilink)
        self.text_edit.hashtag_clicked.connect(self.hashtag_clicked.emit)
        self.text_edit.url_clicked.connect(self._open_url)
        layout.addWidget(self.text_edit)

        self.setLayout(layout)

        # Setup syntax highlighting (theme will be set after initialization)
        self.highlighter = MarkdownHighlighter(self.text_edit.document(), theme="dark")

    def set_notes_directory(self, directory: Path):
        """Change the notes directory."""
        self.notes_directory = directory
        self.text_edit.set_notes_directory(directory)
    
    def set_theme(self, theme: str):
        """Update editor theme for syntax highlighting."""
        self.highlighter.update_theme(theme)
    
    def load_file(self, file_path: Path):
        """Load a file into the editor."""
        # Save current file if it has unsaved changes
        if self.current_file and self._is_modified:
            self.save_file()
        
        # Save cursor position of current file before loading new one
        if self.current_file and self.config:
            cursor = self.text_edit.textCursor()
            file_key = str(self.current_file.resolve())
            cursor_positions = self.config.get("editor.cursor_positions", {})
            cursor_positions[file_key] = cursor.position()
            self.config.set("editor.cursor_positions", cursor_positions)
            self.config.save()

        try:
            content = file_path.read_text(encoding="utf-8")
            self.text_edit.setPlainText(content)
            self.current_file = file_path

            # Restore cursor position if available
            if self.config:
                file_key = str(file_path.resolve())
                cursor_positions = self.config.get("editor.cursor_positions", {})
                saved_position = cursor_positions.get(file_key, 0)
                cursor = self.text_edit.textCursor()
                cursor.setPosition(min(saved_position, len(content)))
                self.text_edit.setTextCursor(cursor)

            # Update autocomplete lists
            self._update_autocomplete_lists()
            self._is_modified = False
            self._update_title()
            self.text_edit.setFocus()
            self.pin_button.setEnabled(True)
            self.export_button.setEnabled(True)
        except (OSError, UnicodeDecodeError) as e:
            self.title_label.setText(f"Error loading file: {e}")

    def save_file(self) -> bool:
        """Save the current file."""
        if self.current_file is None:
            return False

        try:
            content = self.text_edit.toPlainText()
            self.current_file.write_text(content, encoding="utf-8")
            self._is_modified = False
            self._update_title()
            self.file_saved.emit(self.current_file)

            # Update autocomplete lists after save (hashtags may have changed)
            self._update_autocomplete_lists()

            return True
        except OSError as e:
            self.title_label.setText(f"Error saving file: {e}")
            return False

    def close_file(self):
        """Close the current file."""
        self.current_file = None
        self.text_edit.clear()
        self._is_modified = False
        self._update_title()
        self.pin_button.setEnabled(False)
        self.pin_button.setChecked(False)
        self.export_button.setEnabled(False)

    def is_modified(self) -> bool:
        """Check if the file has unsaved changes."""
        return self._is_modified

    def _on_text_changed(self):
        """Handle text changes."""
        if self.current_file:
            self._is_modified = True
            self._update_title()
            # Schedule auto-save after 2 seconds
            self._auto_save_timer.start(2000)

    def _auto_save(self):
        """Auto-save the current file."""
        if self.current_file and self._is_modified:
            self.save_file()

    def _update_title(self):
        """Update the editor title bar."""
        if self.current_file:
            modified = " *" if self._is_modified else ""
            self.title_label.setText(f"{self.current_file.stem}{modified}")
        else:
            self.title_label.setText("No file open")

    # --- Pin UI helpers ---
    def set_pin_checked(self, checked: bool) -> None:
        """Programmatically set pin checkbox state (does not emit signal)."""
        was_blocked = self.pin_button.blockSignals(True)
        try:
            self.pin_button.setChecked(bool(checked))
        finally:
            self.pin_button.blockSignals(was_blocked)

    def _on_pin_clicked(self, checked: bool):
        if self.current_file is not None:
            self.pin_toggled.emit(self.current_file, bool(checked))

    def _on_export_clicked(self):
        """Handle export button click."""
        if self.current_file is not None:
            self.export_requested.emit(self.current_file)

    def _update_autocomplete_lists(self):
        """Update autocomplete lists for wiki-links and hashtags."""
        if not self.notes_directory.exists():
            return

        # Get available files (relative paths without .md)
        from sitext.utils.markdown_parser import get_available_filenames, get_hashtag_counts

        files = get_available_filenames(self.notes_directory)
        self.text_edit.set_available_files(files)

        # Get available hashtags
        hashtag_counts = get_hashtag_counts(self.notes_directory)
        hashtags = list(hashtag_counts.keys())
        self.text_edit.set_available_hashtags(hashtags)

    def follow_link_at_cursor(self):
        """Follow a wiki-link at the current cursor position."""
        if not self.current_file:
            return

        # Get current cursor and its position
        cursor = self.text_edit.textCursor()
        cursor_pos = cursor.position()
        
        # Get the entire text
        full_text = self.text_edit.toPlainText()
        
        # Find all wiki-links in the entire document
        wikilink_pattern = re.compile(r'\[\[([^\]]+)\]\]')
        
        for match in wikilink_pattern.finditer(full_text):
            start, end = match.span()
            # Check if cursor is within this wiki-link (end is exclusive)
            if start <= cursor_pos < end:
                link_text = match.group(1)
                self._open_wikilink(link_text)
                return

    def _open_wikilink(self, link_text: str):
        """Open a wiki-link target file with folder-aware resolution."""
        if not self.current_file:
            return

        # Use smart wiki-link resolution that supports folders
        from sitext.utils.markdown_parser import find_wikilink_target

        target_path = find_wikilink_target(
            link_text,
            self.notes_directory,
            current_file=self.current_file,
            create_if_missing=True  # Create file if it doesn't exist
        )

        if target_path:
            self.wiki_link_clicked.emit(target_path)

    def _open_url(self, url: str):
        """Open a URL in the default web browser."""
        import webbrowser
        try:
            webbrowser.open(url)
        except Exception:
            pass  # Silently ignore errors opening URLs
