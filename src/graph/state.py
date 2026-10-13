from typing import Annotated, Any, TypedDict
from src.models import SearchResult


class GraphState(TypedDict):
    """Represents the mutable state of our agentic RAG pipeline."""

    query: str
    rewritten_query: str
    tenant_id: str
    documents: list[SearchResult]
    generation: str
    relevance_status: str  # 'relevant', 'insufficient', 'fallback'
    loop_count: int
    max_retries: int