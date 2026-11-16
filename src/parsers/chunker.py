"""Recursive text chunker for document indexing."""

import hashlib
import logging

from langchain_text_splitters import RecursiveCharacterTextSplitter

from src.models import DocumentChunk

logger = logging.getLogger(__name__)


class DocumentChunker:
    """Splits raw document text into overlapping chunks for vector indexing.

    Uses LangChain's ``RecursiveCharacterTextSplitter`` with a hierarchy of
    separators (paragraph → line → sentence → word → character) to produce
    semantically coherent chunks.

    Each chunk receives a deterministic ``chunk_id`` derived from a SHA-256
    hash of its tenant, document, index, and leading content — ensuring
    idempotent re-indexing.
    """

    def __init__(self, chunk_size: int = 512, chunk_overlap: int = 64) -> None:
        """Initialise the chunker with size and overlap parameters.

        Args:
            chunk_size: Maximum number of characters per chunk.
            chunk_overlap: Number of overlapping characters between consecutive
                chunks to preserve context across boundaries.
        """
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        self._splitter = RecursiveCharacterTextSplitter(
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
            separators=["\n\n", "\n", ". ", " ", ""],
            length_function=len,
        )

    def chunk_text(
        self, text: str, doc_id: str, tenant_id: str
    ) -> list[DocumentChunk]:
        """Split text into a list of ``DocumentChunk`` objects.

        Args:
            text: The full document text to split.
            doc_id: Unique identifier of the source document.
            tenant_id: Tenant / workspace identifier for multi-tenant isolation.

        Returns:
            An ordered list of ``DocumentChunk`` objects ready for indexing.
        """
        if not text or not text.strip():
            logger.warning("Empty text provided for doc_id=%s, returning no chunks.", doc_id)
            return []

        raw_chunks: list[str] = self._splitter.split_text(text)
        total_chunks = len(raw_chunks)

        chunks: list[DocumentChunk] = []
        for i, chunk_text in enumerate(raw_chunks):
            # Deterministic chunk ID using SHA-256
            hash_input = f"{tenant_id}_{doc_id}_{i}_{chunk_text[:50]}"
            chunk_id = hashlib.sha256(hash_input.encode("utf-8")).hexdigest()

            chunks.append(
                DocumentChunk(
                    chunk_id=chunk_id,
                    doc_id=doc_id,
                    tenant_id=tenant_id,
                    content=chunk_text,
                    metadata={"chunk_index": i, "total_chunks": total_chunks},
                )
            )

        logger.info(
            "Chunked doc_id=%s into %d chunks (size=%d, overlap=%d).",
            doc_id,
            total_chunks,
            self.chunk_size,
            self.chunk_overlap,
        )
        return chunks
