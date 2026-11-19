"""
DocuMind — AI Knowledge Base for Teams.

FastAPI application entry point. Loads the CRAG engine at startup,
registers all API routers, and initializes the database.
"""

import logging

from contextlib import asynccontextmanager

from fastapi import FastAPI, status
from fastapi.middleware.cors import CORSMiddleware

from src.config import settings
from src.db.database import create_tables
from src.graph.nodes import CRAGNodes
from src.graph.workflow import build_crag_graph
from src.retrieval.reranker import CrossEncoderReranker
from src.retrieval.vector_store import HybridRetriever

# ── Logging ─────────────────────────────────────────────────────────────────
logging.basicConfig(
    level=logging.DEBUG if settings.debug else logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)

# ── Global application state ───────────────────────────────────────────────
app_state: dict = {}


# ── Lifespan ────────────────────────────────────────────────────────────────
@asynccontextmanager
async def lifespan(app: FastAPI):
    """Load neural models and compiled state graph once at startup."""
    logger.info("[Startup] Creating database tables if needed...")
    create_tables()

    logger.info("[Startup] Initializing Hybrid Retriever & Cross-Encoder...")
    retriever = HybridRetriever(
        qdrant_host=settings.qdrant_host,
        qdrant_port=settings.qdrant_port,
        qdrant_url=settings.qdrant_url,
        qdrant_api_key=settings.qdrant_api_key,
        collection_name=settings.qdrant_collection,
        dense_model_name=settings.dense_model,
    )
    reranker = CrossEncoderReranker(model_name=settings.reranker_model)

    logger.info("[Startup] Compiling CRAG Graph with model: %s...", settings.groq_model)
    nodes = CRAGNodes(
        retriever=retriever,
        reranker=reranker,
        model_name=settings.groq_model,
    )
    graph = build_crag_graph(nodes)

    app_state["retriever"] = retriever
    app_state["reranker"] = reranker
    app_state["nodes"] = nodes
    app_state["graph"] = graph
    logger.info("[Startup] Initialization complete. DocuMind is ready.")

    yield

    logger.info("[Shutdown] Cleaning up resources.")
    app_state.clear()


# ── App ─────────────────────────────────────────────────────────────────────
app = FastAPI(
    title="DocuMind API",
    description="Self-correcting AI Knowledge Base with Agentic CRAG",
    version="2.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origin_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ── Register Routers ───────────────────────────────────────────────────────
from src.api.routers import auth, chat, documents, query, workspaces  # noqa: E402

app.include_router(auth.router)
app.include_router(workspaces.router)
app.include_router(documents.router)
app.include_router(chat.router)
app.include_router(query.router)


# ── Health Check ────────────────────────────────────────────────────────────
@app.get("/health", status_code=status.HTTP_200_OK, tags=["Health"])
def health_check():
    """Service health check."""
    return {
        "status": "healthy",
        "service": settings.app_name,
        "models_loaded": "graph" in app_state,
        "engine": settings.groq_model,
    }
