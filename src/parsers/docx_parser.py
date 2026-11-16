"""DOCX document parser using python-docx."""

import logging

from docx import Document

logger = logging.getLogger(__name__)


def parse_docx(file_path: str) -> str:
    """Extract text content from a DOCX document.

    Extracts text from all paragraphs and all table cells. Paragraph text and
    table text are combined with double newlines.

    Args:
        file_path: Absolute or relative path to the DOCX file.

    Returns:
        The full extracted text from the document.

    Raises:
        FileNotFoundError: If the file does not exist.
        docx.opc.exceptions.PackageNotFoundError: If the file is not a valid DOCX.
    """
    logger.info("Parsing DOCX: %s", file_path)

    doc = Document(file_path)
    parts: list[str] = []

    # Extract paragraph text
    for paragraph in doc.paragraphs:
        text = paragraph.text.strip()
        if text:
            parts.append(text)

    # Extract table text
    for table in doc.tables:
        for row in table.rows:
            row_text = "\t".join(cell.text.strip() for cell in row.cells)
            if row_text.strip():
                parts.append(row_text)

    extracted = "\n\n".join(parts)
    logger.info(
        "Extracted %d characters from %d paragraphs and %d tables.",
        len(extracted),
        len(doc.paragraphs),
        len(doc.tables),
    )
    return extracted
