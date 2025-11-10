"""PDF export functionality for markdown notes using FPDF2."""

from pathlib import Path
import markdown
from fpdf import FPDF
import unicodedata
import xml.etree.ElementTree as ET


class MarkdownPDF(FPDF):
    """Custom PDF class with markdown-friendly styling and Unicode support."""

    def __init__(self):
        super().__init__()
        self.set_auto_page_break(auto=True, margin=15)
        self.unicode_supported = False
        
        # Try to add Unicode fonts (DejaVu) for better character support
        try:
            self.add_font("DejaVu", "", "DejaVuSans.ttf")
            self.add_font("DejaVu", "B", "DejaVuSans-Bold.ttf")
            self.add_font("DejaVu", "I", "DejaVuSans-Oblique.ttf")
            self.add_font("DejaVuMono", "", "DejaVuSansMono.ttf")
            self.unicode_supported = True
        except Exception:
            # DejaVu fonts not available, will fall back to helvetica with sanitization
            pass

    def header(self):
        """Page header - intentionally empty for clean look."""
        pass

    def footer(self):
        """Page footer with page number."""
        self.set_y(-15)
        font_name = 'DejaVu' if self.unicode_supported else 'helvetica'
        self.set_font(font_name, 'I', 8)
        self.set_text_color(0, 0, 0)  # Black text
        self.cell(0, 10, f'Page {self.page_no()}', 0, 0, 'C')


def _sanitize_for_latin1(text: str) -> str:
    """Replace Unicode characters that can't be encoded in Latin-1 with ASCII equivalents.
    
    Args:
        text: Text to sanitize
        
    Returns:
        Text with Unicode characters replaced
    """
    # Common replacements
    replacements = {
        '\u2014': '--',  # em dash
        '\u2013': '-',   # en dash
        '\u2018': "'",   # left single quote
        '\u2019': "'",   # right single quote
        '\u201c': '"',   # left double quote
        '\u201d': '"',   # right double quote
        '\u2026': '...',  # ellipsis
        '\u00a0': ' ',   # non-breaking space
        '\u2022': '- ',  # bullet -> dash
    }
    
    for old, new in replacements.items():
        text = text.replace(old, new)
    
    # Remove any remaining non-Latin-1 characters
    result = []
    for char in text:
        try:
            char.encode('latin-1')
            result.append(char)
        except UnicodeEncodeError:
            # Try to get ASCII equivalent
            normalized = unicodedata.normalize('NFKD', char)
            ascii_char = normalized.encode('ascii', 'ignore').decode('ascii')
            result.append(ascii_char if ascii_char else '?')
    
    return ''.join(result)


def _flatten_lists(html: str) -> str:
    """Convert <ul>/<ol> lists into plain <p> paragraphs with textual prefixes.

    This avoids fpdf2's internal list rendering which styles markers (color/size)
    differently. By flattening, list items render like normal paragraphs in the
    current font/color (pure black), and we keep predictable sizing.

    Supports nested lists by prefixing two spaces per depth level.

    Args:
        html: HTML string produced by python-markdown

    Returns:
        Transformed HTML string with lists replaced by <p> elements.
    """
    # Ensure the HTML is wrapped with a root element for XML parsing
    wrapper = f"<div>{html}</div>"
    try:
        root = ET.fromstring(wrapper)
    except ET.ParseError:
        # If parsing fails, return original HTML (no transformation)
        return html

    def li_text(elem: ET.Element) -> str:
        return ''.join(elem.itertext()).strip()

    def transform(parent: ET.Element, depth: int = 0) -> None:
        i = 0
        while i < len(parent):
            child = parent[i]
            if child.tag in {"ul", "ol"}:
                # Gather replacement <p> nodes
                is_ordered = child.tag == "ol"
                start = 1
                try:
                    start_attr = child.attrib.get("start")
                    if start_attr is not None:
                        start = int(start_attr)
                except Exception:
                    start = 1

                new_nodes = []
                counter = start
                for li in list(child):
                    if li.tag != "li":
                        continue
                    txt = li_text(li)
                    indent = "  " * depth
                    prefix = f"{counter}. " if is_ordered else "• "
                    p = ET.Element("p")
                    p.text = f"{indent}{prefix}{txt}"
                    new_nodes.append(p)
                    counter += 1 if is_ordered else 0

                    # Handle any nested lists under this li
                    for sub in list(li):
                        if sub.tag in {"ul", "ol"}:
                            # recursively transform nested list into <p> nodes
                            # Temporarily attach to a container to reuse logic
                            container = ET.Element("div")
                            container.append(sub)
                            transform(container, depth + 1)
                            # Append transformed children of container to new_nodes
                            new_nodes.extend(list(container))

                # Replace the list node with the new <p> nodes
                parent.remove(child)
                for offset, node in enumerate(new_nodes):
                    parent.insert(i + offset, node)
                i += len(new_nodes)
                continue
            else:
                # Recurse
                transform(child, depth)
            i += 1

    transform(root)
    # Serialize children of wrapper back to string
    return ''.join(ET.tostring(e, encoding='unicode') for e in list(root))


def _replace_emoji(text: str) -> str:
    """Replace unsupported emoji with simple black-and-white symbols or nothing.

    DejaVu fonts do not include color emoji, so many emoji render as '?'. We
    map common emoji used in headings to monochrome equivalents that DejaVu can
    display, or drop them entirely to keep PDFs clean and black-only.

    Args:
        text: Raw markdown text

    Returns:
        Text with emoji replaced by ASCII/Unicode monospace-friendly symbols.
    """
    replacements = {
        # Checks
        '✅': '✓', '☑️': '☑', '✔️': '✔', '✔': '✔', '☑': '☑',
        # Tools / icons used as section markers -> remove
        '🔍': '', '🧾': '', '🛠️': '', '🛠': '', '⚙️': '', '⚙': '', '🧪': '', '🧭': '',
        '🚀': '', '📦': '', '📌': '', '📁': '', '📄': '', '📝': '', '📋': '', '📊': '',
        '📈': '', '📎': '', '🔧': '', '🔨': '', '🔗': '', '🔒': '', '🔓': '', '⛵️': '', '⛵': '',
        # Info/alerts
        '❗': '!', 'ℹ️': 'i', '➡️': '→', '➡': '→',
        # Misc invisible selectors
        '\ufe0f': '',  # VARIATION SELECTOR-16
        '\u200d': '',  # ZERO WIDTH JOINER
    }

    for old, new in replacements.items():
        text = text.replace(old, new)
    return text


def export_to_pdf(markdown_file: Path, output_pdf: Path) -> bool:
    """Export a markdown file to PDF with proper formatting.

    Args:
        markdown_file: Path to the markdown file to export
        output_pdf: Path where the PDF should be saved

    Returns:
        True if export was successful, False otherwise
    """
    # Read markdown content
    try:
        content = markdown_file.read_text(encoding='utf-8')
    except Exception:
        return False

    # Convert markdown to HTML with extensions
    # First, replace emoji so they don't render as '?'
    content = _replace_emoji(content)
    
    # Remove image markdown syntax (images not supported in PDF export)
    import re
    content = re.sub(r'!\[([^\]]*)\]\(([^\)]+)\)', r'[Image: \1]', content)
    md = markdown.Markdown(extensions=[
        'extra',  # Tables, fenced code blocks, etc.
        'nl2br',  # New line to <br>
    ])
    html_content = md.convert(content)
    html_content = _flatten_lists(html_content)

    # Create PDF
    pdf = MarkdownPDF()
    pdf.add_page()

    from fpdf.fonts import FontFace
    if pdf.unicode_supported:
        pdf.set_font('DejaVu', '', 11)
        tag_styles = {
            "code": FontFace(family="DejaVuMono", size_pt=10, color=(0, 0, 0)),
            "pre": FontFace(family="DejaVuMono", size_pt=10, color=(0, 0, 0)),
            "h1": FontFace(family="DejaVu", emphasis="BOLD", size_pt=18, color=(0, 0, 0)),
            "h2": FontFace(family="DejaVu", emphasis="BOLD", size_pt=16, color=(0, 0, 0)),
            "h3": FontFace(family="DejaVu", emphasis="BOLD", size_pt=14, color=(0, 0, 0)),
            "h4": FontFace(family="DejaVu", emphasis="BOLD", size_pt=12, color=(0, 0, 0)),
            "h5": FontFace(family="DejaVu", emphasis="BOLD", size_pt=11, color=(0, 0, 0)),
            "h6": FontFace(family="DejaVu", emphasis="BOLD", size_pt=11, color=(0, 0, 0)),
            "a": FontFace(family="DejaVu", size_pt=11, color=(0, 0, 0)),
            "p": FontFace(family="DejaVu", size_pt=11, color=(0, 0, 0)),
            "strong": FontFace(family="DejaVu", emphasis="BOLD", size_pt=11, color=(0, 0, 0)),
            "b": FontFace(family="DejaVu", emphasis="BOLD", size_pt=11, color=(0, 0, 0)),
        }
    else:
        pdf.set_font('helvetica', '', 11)
        html_content = _sanitize_for_latin1(html_content)
        tag_styles = {
            "code": FontFace(family="courier", size_pt=10, color=(0, 0, 0)),
            "pre": FontFace(family="courier", size_pt=10, color=(0, 0, 0)),
            "h1": FontFace(family="helvetica", emphasis="BOLD", size_pt=18, color=(0, 0, 0)),
            "h2": FontFace(family="helvetica", emphasis="BOLD", size_pt=16, color=(0, 0, 0)),
            "h3": FontFace(family="helvetica", emphasis="BOLD", size_pt=14, color=(0, 0, 0)),
            "h4": FontFace(family="helvetica", emphasis="BOLD", size_pt=12, color=(0, 0, 0)),
            "h5": FontFace(family="helvetica", emphasis="BOLD", size_pt=11, color=(0, 0, 0)),
            "h6": FontFace(family="helvetica", emphasis="BOLD", size_pt=11, color=(0, 0, 0)),
            "a": FontFace(family="helvetica", size_pt=11, color=(0, 0, 0)),
            "p": FontFace(family="helvetica", size_pt=11, color=(0, 0, 0)),
            "strong": FontFace(family="helvetica", emphasis="BOLD", size_pt=11, color=(0, 0, 0)),
            "b": FontFace(family="helvetica", emphasis="BOLD", size_pt=11, color=(0, 0, 0)),
        }

    pdf.set_text_color(0, 0, 0)
    pdf.set_draw_color(0, 0, 0)
    pdf.set_fill_color(0, 0, 0)
    try:
        pdf.write_html(html_content, tag_styles=tag_styles)
        pdf.output(str(output_pdf))
        return True
    except Exception:
        return False
