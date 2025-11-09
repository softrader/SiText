"""PDF export functionality for markdown notes using FPDF2."""

from pathlib import Path
import markdown
from fpdf import FPDF
import unicodedata


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
        self.set_text_color(128, 128, 128)
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


def export_to_pdf(markdown_file: Path, output_pdf: Path) -> bool:
    """Export a markdown file to PDF with proper formatting.

    Args:
        markdown_file: Path to the markdown file to export
        output_pdf: Path where the PDF should be saved

    Returns:
        True if export was successful, False otherwise
    """
    try:
        # Read markdown content
        content = markdown_file.read_text(encoding='utf-8')

        # Convert markdown to HTML with extensions
        md = markdown.Markdown(extensions=[
            'extra',  # Tables, fenced code blocks, etc.
            'nl2br',  # New line to <br>
            'sane_lists',  # Better list handling
        ])
        html_content = md.convert(content)

        # Create PDF
        pdf = MarkdownPDF()
        pdf.add_page()

        # Set default font
        if pdf.unicode_supported:
            # Use DejaVu for full Unicode support
            from fpdf.fonts import FontFace
            pdf.set_font('DejaVu', '', 11)
            tag_styles = {
                "code": FontFace(family="DejaVuMono", size_pt=10),
                "pre": FontFace(family="DejaVuMono", size_pt=10),
            }
        else:
            # Fall back to Helvetica with sanitized content
            from fpdf.fonts import FontFace
            pdf.set_font('helvetica', '', 11)
            html_content = _sanitize_for_latin1(html_content)
            tag_styles = {
                "code": FontFace(family="courier", size_pt=10),
                "pre": FontFace(family="courier", size_pt=10),
            }
        
        pdf.set_text_color(51, 51, 51)  # #333

        # Write HTML content to PDF (fpdf2 v2.8+ handles styling automatically)
        pdf.write_html(html_content, tag_styles=tag_styles)

        # Save PDF
        pdf.output(str(output_pdf))

        return True

    except Exception as e:
        print(f"Error exporting to PDF: {e}")
        import traceback
        traceback.print_exc()
        return False
