from typing import Any
from pydantic import BaseModel, Field


class DocumentChunk(BaseModel):
    chunk_id: str
    doc_id: str
    tenant_id: str
    content: str
    metadata: dict[str, Any] = Field(default_factory=dict)


class SearchResult(BaseModel):
    chunk_id: str
    doc_id: str
    content: str
    score: float
    source: str  # 'dense', 'sparse', or 'hybrid_reranked'
    metadata: dict[str, Any] = Field(default_factory=dict)