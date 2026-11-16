"""PDF document parser using PyMuPDF (fitz)."""

import logging

import fitz  # PyMuPDF

logger = logging.getLogger(__name__)


def parse_pdf(file_path: str) -> str:
    """Extract text content from all pages of a PDF document.

    Uses PyMuPDF (fitz) to iterate through every page and extract text.
    Empty pages are skipped gracefully. Pages are joined with double newlines.

    Args:
        file_path: Absolute or relative path to the PDF file.

    Returns:
        The full extracted text from the PDF.

    Raises:
        FileNotFoundError: If the file does not exist.
        fitz.FileDataError: If the file is not a valid PDF.
    """
    logger.info("Parsing PDF: %s", file_path)

    doc = fitz.open(file_path)
    pages: list[str] = []

    try:
        for page_num in range(len(doc)):
            page = doc.load_page(page_num)
            text = page.get_text("text")
            if text and text.strip():
                pages.append(text.strip())
            else:
                logger.debug("Page %d is empty, skipping.", page_num + 1)
    finally:
        doc.close()

    extracted = "\n\n".join(pages)
    logger.info(
        "Extracted %d characters from %d non-empty pages.", len(extracted), len(pages)
    )
    return extracted
