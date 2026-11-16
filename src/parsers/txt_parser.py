"""Plain text document parser."""

import logging

logger = logging.getLogger(__name__)


def parse_txt(file_path: str) -> str:
    """Read a plain text file and return its content.

    Attempts to read the file with UTF-8 encoding first. If a
    ``UnicodeDecodeError`` occurs, falls back to Latin-1 encoding which
    can decode any byte sequence.

    Args:
        file_path: Absolute or relative path to the text file.

    Returns:
        The full text content of the file.

    Raises:
        FileNotFoundError: If the file does not exist.
    """
    logger.info("Parsing TXT: %s", file_path)

    try:
        with open(file_path, "r", encoding="utf-8") as f:
            content = f.read()
    except UnicodeDecodeError:
        logger.warning(
            "UTF-8 decode failed for %s, falling back to latin-1.", file_path
        )
        with open(file_path, "r", encoding="latin-1") as f:
            content = f.read()

    logger.info("Extracted %d characters from text file.", len(content))
    return content
