"""Document upload, parsing, chunking, and indexing service."""

import hashlib
import logging
import os
import uuid

from sqlalchemy.orm import Session

from src.db.models import Document
from src.models import DocumentChunk
from src.parsers.chunker import DocumentChunker
from src.parsers.docx_parser import parse_docx
from src.parsers.markdown_parser import parse_markdown
from src.parsers.pdf_parser import parse_pdf
from src.parsers.txt_parser import parse_txt

logger = logging.getLogger(__name__)

_PARSERS = {
    "pdf": parse_pdf,
    "docx": parse_docx,
    "md": parse_markdown,
    "txt": parse_txt,
}


class DocumentService:
    """Handles saving uploads, parsing files, chunking text, and indexing."""

    def __init__(self, upload_dir: str = "./uploads") -> None:
        self.upload_dir = upload_dir
        os.makedirs(upload_dir, exist_ok=True)
        self.chunker = DocumentChunker(chunk_size=512, chunk_overlap=64)

    def save_upload_bytes(
        self, content: bytes, filename: str, workspace_id: str
    ) -> str:
        """Save raw bytes to disk under ``{upload_dir}/{workspace_id}/``.

        Returns the full path of the saved file.
        """
        workspace_dir = os.path.join(self.upload_dir, workspace_id)
        os.makedirs(workspace_dir, exist_ok=True)

        safe_name = f"{uuid.uuid4().hex[:8]}_{filename}"
        file_path = os.path.join(workspace_dir, safe_name)

        with open(file_path, "wb") as f:
            f.write(content)

        logger.info("Saved upload to %s (%d bytes)", file_path, len(content))
        return file_path

    def parse_document(self, file_path: str, file_type: str) -> str:
        """Dispatch to the correct parser based on file type.

        Raises ``ValueError`` for unsupported file types.
        """
        parser = _PARSERS.get(file_type)
        if parser is None:
            raise ValueError(
                f"Unsupported file type '{file_type}'. "
                f"Supported: {', '.join(_PARSERS)}"
            )
        return parser(file_path)

    def process_and_index(
        self,
        db: Session,
        retriever,  # HybridRetriever — import avoided to prevent circular deps
        document_id: str,
        workspace_id: str,
        file_path: str,
        file_type: str,
    ) -> int:
        """Parse → chunk → index a document, then update the DB record.

        The *workspace_id* is used as the ``tenant_id`` in the CRAG retrieval
        layer, mapping each workspace to an isolated vector namespace.

        Returns the number of chunks indexed.
        """
        doc_record = db.query(Document).filter(Document.id == document_id).first()

        try:
            # 1. Parse the file into raw text
            text = self.parse_document(file_path, file_type)
            if not text.strip():
                raise ValueError("Document is empty after parsing")

            # 2. Chunk the text
            chunks: list[DocumentChunk] = self.chunker.chunk_text(
                text=text,
                doc_id=document_id,
                tenant_id=workspace_id,
            )

            # 3. Index into Qdrant + BM25 via the hybrid retriever
            retriever.index_chunks(workspace_id, chunks)

            # 4. Update DB record
            if doc_record:
                doc_record.chunk_count = len(chunks)
                doc_record.status = "ready"
                doc_record.error_message = None
                db.commit()

            logger.info(
                "Indexed document %s: %d chunks into workspace %s",
                document_id,
                len(chunks),
                workspace_id,
            )
            return len(chunks)

        except Exception as e:
            logger.error("Failed to process document %s: %s", document_id, e)
            if doc_record:
                doc_record.status = "failed"
                doc_record.error_message = str(e)[:500]
                db.commit()
            raise
