import hashlib
import json
import time
from contextlib import asynccontextmanager
from typing import AsyncGenerator

from fastapi import FastAPI, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from sse_starlette.sse import EventSourceResponse

from src.api.schemas import (
    DocumentCitation,
    IngestDocumentRequest,
    IngestResponse,
    QueryRequest,
    QueryResponse,
)
from src.config import settings
from src.graph.nodes import CRAGNodes
from src.graph.workflow import build_crag_graph
from src.models import DocumentChunk
from src.retrieval.reranker import CrossEncoderReranker
from src.retrieval.vector_store import HybridRetriever

# Global application state container
app_state = {}


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Load neural models and compiled state graph once at startup."""
    print("[Startup] Initializing Hybrid Retriever & Cross-Encoder...")
    retriever = HybridRetriever(
        qdrant_host=settings.qdrant_host,
        qdrant_port=settings.qdrant_port,
        collection_name=settings.qdrant_collection,
        dense_model_name=settings.dense_model,
    )
    reranker = CrossEncoderReranker(model_name=settings.reranker_model)

    print(f"[Startup] Compiling CRAG Graph using model: {settings.groq_model}...")
    nodes = CRAGNodes(
        retriever=retriever,
        reranker=reranker,
        model_name=settings.groq_model,
    )
    graph = build_crag_graph(nodes)

    app_state["retriever"] = retriever
    app_state["reranker"] = reranker
    app_state["graph"] = graph
    print("[Startup] Initialization complete.")

    yield
    print("[Shutdown] Cleaning up resources.")
    app_state.clear()


app = FastAPI(
    title="Self-Correcting Agentic CRAG API",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health", status_code=status.HTTP_200_OK)
def health_check():
    return {
        "status": "healthy",
        "models_loaded": "graph" in app_state,
        "engine": settings.groq_model,
    }


@app.post("/api/v1/documents/index", response_model=IngestResponse)
async def index_documents(payload: IngestDocumentRequest):
    """Batch-indexes documents with deterministic chunk hashing for multi-tenant isolation."""
    retriever: HybridRetriever = app_state["retriever"]

    chunks = []
    for i, doc_text in enumerate(payload.documents):
        # Deterministic hash prevents duplicate chunks on re-indexing
        chunk_id = hashlib.sha256(f"{payload.tenant_id}_{doc_text}".encode()).hexdigest()[:16]
        chunks.append(
            DocumentChunk(
                chunk_id=chunk_id,
                doc_id=f"doc_{i}",
                tenant_id=payload.tenant_id,
                content=doc_text,
                metadata=payload.metadata,
            )
        )

    retriever.index_chunks(payload.tenant_id, chunks)

    return IngestResponse(
        status="success",
        tenant_id=payload.tenant_id,
        chunks_indexed=len(chunks),
    )


@app.post("/api/v1/query", response_model=QueryResponse)
async def execute_query(req: QueryRequest):
    """Executes synchronous CRAG query with latency metrics and citations."""
    graph = app_state["graph"]

    initial_state = {
        "query": req.query,
        "rewritten_query": "",
        "tenant_id": req.tenant_id,
        "documents": [],
        "generation": "",
        "relevance_status": "",
        "loop_count": 0,
        "max_retries": req.max_retries,
    }

    t0 = time.perf_counter()
    final_state = graph.invoke(initial_state)
    latency_ms = (time.perf_counter() - t0) * 1000

    citations = [
        DocumentCitation(
            chunk_id=d.chunk_id,
            source=d.source,
            score=round(d.score, 4),
            preview=d.content[:150] + ("..." if len(d.content) > 150 else ""),
        )
        for d in final_state.get("documents", [])
    ]

    return QueryResponse(
        answer=final_state.get("generation", "No generation produced."),
        query=req.query,
        rewritten_query=final_state.get("rewritten_query") or None,
        relevance_status=final_state.get("relevance_status", "unknown"),
        loop_count=final_state.get("loop_count", 0),
        citations=citations,
        latency_ms=round(latency_ms, 2),
    )


@app.get("/api/v1/query/stream")
async def stream_query(tenant_id: str, query: str, max_retries: int = 2):
    """Streams graph node execution events and final answer via Server-Sent Events (SSE)."""
    graph = app_state["graph"]

    initial_state = {
        "query": query,
        "rewritten_query": "",
        "tenant_id": tenant_id,
        "documents": [],
        "generation": "",
        "relevance_status": "",
        "loop_count": 0,
        "max_retries": max_retries,
    }

    async def event_generator() -> AsyncGenerator[str, None]:
        for step in graph.stream(initial_state):
            for node_name, state_delta in step.items():
                event_payload = {
                    "node": node_name,
                    "relevance_status": state_delta.get("relevance_status"),
                    "loop_count": state_delta.get("loop_count"),
                    "rewritten_query": state_delta.get("rewritten_query"),
                    "generation": state_delta.get("generation"),
                }
                yield json.dumps(event_payload)

    return EventSourceResponse(event_generator())