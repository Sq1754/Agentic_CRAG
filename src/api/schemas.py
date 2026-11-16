"""Enhanced Pydantic schemas for DocuMind API requests and responses."""

from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel, Field


# ─── Document Ingestion (Legacy, still supported) ────────────────────────────


class IngestDocumentRequest(BaseModel):
    """Legacy: Ingest raw text documents into a workspace's vector index."""

    workspace_id: str = Field(..., description="Workspace identifier for data isolation")
    documents: list[str] = Field(..., description="List of raw text documents/paragraphs")
    metadata: dict[str, Any] = Field(default_factory=dict)


class IngestResponse(BaseModel):
    status: str
    workspace_id: str
    chunks_indexed: int


# ─── Document Upload ─────────────────────────────────────────────────────────


class DocumentResponse(BaseModel):
    id: UUID
    filename: str
    file_type: str
    file_size: int | None
    chunk_count: int
    status: str
    error_message: str | None = None
    created_at: datetime

    model_config = {"from_attributes": True}


# ─── Query & CRAG Pipeline ───────────────────────────────────────────────────


class QueryRequest(BaseModel):
    """Execute a CRAG query against a workspace's knowledge base."""

    query: str = Field(..., description="User's natural language question")
    session_id: UUID | None = Field(None, description="Chat session ID for history tracking")
    max_retries: int = Field(default=2, ge=0, le=4)


class DocumentCitation(BaseModel):
    chunk_id: str
    doc_id: str
    source: str
    score: float
    preview: str


class QueryResponse(BaseModel):
    answer: str
    query: str
    rewritten_query: str | None
    relevance_status: str
    loop_count: int
    citations: list[DocumentCitation]
    latency_ms: float
    session_id: UUID | None = None
