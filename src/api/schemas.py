from typing import Any
from pydantic import BaseModel, Field


class IngestDocumentRequest(BaseModel):
    tenant_id: str = Field(..., description="Unique tenant identifier for data isolation")
    documents: list[str] = Field(..., description="List of raw text documents/paragraphs")
    metadata: dict[str, Any] = Field(default_factory=dict)


class IngestResponse(BaseModel):
    status: str
    tenant_id: str
    chunks_indexed: int


class QueryRequest(BaseModel):
    tenant_id: str = Field(..., description="Tenant identifier to query against")
    query: str = Field(..., description="User's natural language question")
    max_retries: int = Field(default=2, ge=0, le=4)


class DocumentCitation(BaseModel):
    chunk_id: str
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