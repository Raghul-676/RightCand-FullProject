from pypdf import PdfReader
from pypdf.errors import PdfReadError


def extract_pdf_text(pdf_file) -> str:
    """Extract all text from a PDF file object or path. Returns empty string on failure."""
    try:
        reader = PdfReader(pdf_file)
        text = ""
        for page in reader.pages:
            page_text = page.extract_text()
            if page_text:
                text += page_text + "\n"
        return text.strip()
    except PdfReadError as e:
        raise ValueError(f"Invalid or corrupted PDF file: {e}")
    except Exception as e:
        raise ValueError(f"Failed to read PDF: {e}")
