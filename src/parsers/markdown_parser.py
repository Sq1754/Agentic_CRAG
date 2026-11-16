"""Markdown document parser."""

import logging
import re

logger = logging.getLogger(__name__)

# Pattern to match HTML tags (opening, closing, and self-closing)
_HTML_TAG_PATTERN = re.compile(r"<[^>]+>")


def parse_markdown(file_path: str) -> str:
    """Read a Markdown file and return its text content.

    Since Markdown is already text-based, this reads the raw content and
    strips any embedded HTML tags using a simple regex.

    Args:
        file_path: Absolute or relative path to the Markdown file.

    Returns:
        The cleaned text content of the Markdown file.

    Raises:
        FileNotFoundError: If the file does not exist.
    """
    logger.info("Parsing Markdown: %s", file_path)

    with open(file_path, "r", encoding="utf-8") as f:
        content = f.read()

    # Strip HTML tags if present
    cleaned = _HTML_TAG_PATTERN.sub("", content)

    logger.info("Extracted %d characters from Markdown file.", len(cleaned))
    return cleaned
