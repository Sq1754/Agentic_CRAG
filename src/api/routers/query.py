"""CRAG query execution router with chat history integration."""

import json
import time
from typing import AsyncGenerator
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sse_starlette.sse import EventSourceResponse

from src.api.dependencies import get_current_user
from src.api.schemas import DocumentCitation, QueryRequest, QueryResponse
from src.db.database import get_db
from src.db.models import User, WorkspaceMember
from src.services import chat_service

router = APIRouter(
    prefix="/api/v1/workspaces/{workspace_id}",
    tags=["Query"],
)


def _verify_membership(db: Session, workspace_id: UUID, user_id: UUID):
    """Verify the user is a member of the workspace."""
    member = (
        db.query(WorkspaceMember)
        .filter(
            WorkspaceMember.workspace_id == workspace_id,
            WorkspaceMember.user_id == user_id,
        )
        .first()
    )
    if not member:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You are not a member of this workspace",
        )
    return member


@router.post("/query", response_model=QueryResponse)
def execute_query(
    workspace_id: UUID,
    req: QueryRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Execute a CRAG query against a workspace's knowledge base.

    Optionally persists the conversation to a chat session when
    ``session_id`` is provided in the request body.
    """
    _verify_membership(db, workspace_id, current_user.id)

    from src.api.main import app_state

    graph = app_state.get("graph")
    if not graph:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="CRAG engine not initialized. Server is starting up.",
        )

    # Use workspace_id as tenant_id for multi-tenant isolation
    initial_state = {
        "query": req.query,
        "rewritten_query": "",
        "tenant_id": str(workspace_id),
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
            doc_id=d.doc_id,
            source=d.source,
            score=round(d.score, 4),
            preview=d.content[:200] + ("..." if len(d.content) > 200 else ""),
        )
        for d in final_state.get("documents", [])
    ]

    answer = final_state.get("generation", "No generation produced.")
    rewritten = final_state.get("rewritten_query") or None
    rel_status = final_state.get("relevance_status", "unknown")
    loop_count = final_state.get("loop_count", 0)

    # Persist to chat session if session_id provided
    session_id = req.session_id
    if session_id:
        try:
            chat_service.save_user_message(db, session_id, req.query)
            chat_service.save_assistant_message(
                db,
                session_id=session_id,
                content=answer,
                rewritten_query=rewritten,
                relevance_status=rel_status,
                loop_count=loop_count,
                citations=[c.model_dump() for c in citations],
                latency_ms=round(latency_ms, 2),
            )
        except Exception:
            pass  # Don't fail the query if chat persistence fails

    return QueryResponse(
        answer=answer,
        query=req.query,
        rewritten_query=rewritten,
        relevance_status=rel_status,
        loop_count=loop_count,
        citations=citations,
        latency_ms=round(latency_ms, 2),
        session_id=session_id,
    )


@router.get("/query/stream")
def stream_query(
    workspace_id: UUID,
    query: str,
    max_retries: int = 2,
    session_id: UUID | None = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Stream CRAG graph execution via Server-Sent Events (SSE).

    Each graph node emits an event with its state delta, and the final
    event contains the generated answer.
    """
    _verify_membership(db, workspace_id, current_user.id)

    from src.api.main import app_state

    graph = app_state.get("graph")
    if not graph:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="CRAG engine not initialized.",
        )

    initial_state = {
        "query": query,
        "rewritten_query": "",
        "tenant_id": str(workspace_id),
        "documents": [],
        "generation": "",
        "relevance_status": "",
        "loop_count": 0,
        "max_retries": max_retries,
    }

    async def event_generator() -> AsyncGenerator[str, None]:
        final_generation = ""
        final_rewritten = None
        final_status = "unknown"
        final_loop = 0
        t0 = time.perf_counter()

        for step in graph.stream(initial_state):
            for node_name, state_delta in step.items():
                if state_delta.get("generation"):
                    final_generation = state_delta["generation"]
                if state_delta.get("rewritten_query"):
                    final_rewritten = state_delta["rewritten_query"]
                if state_delta.get("relevance_status"):
                    final_status = state_delta["relevance_status"]
                if state_delta.get("loop_count"):
                    final_loop = state_delta["loop_count"]

                event_payload = {
                    "node": node_name,
                    "relevance_status": state_delta.get("relevance_status"),
                    "loop_count": state_delta.get("loop_count"),
                    "rewritten_query": state_delta.get("rewritten_query"),
                    "generation": state_delta.get("generation"),
                }
                yield json.dumps(event_payload)

        latency_ms = (time.perf_counter() - t0) * 1000

        # Persist to chat session if requested
        if session_id and final_generation:
            try:
                chat_service.save_user_message(db, session_id, query)
                chat_service.save_assistant_message(
                    db,
                    session_id=session_id,
                    content=final_generation,
                    rewritten_query=final_rewritten,
                    relevance_status=final_status,
                    loop_count=final_loop,
                    citations=[],
                    latency_ms=round(latency_ms, 2),
                )
            except Exception:
                pass

    return EventSourceResponse(event_generator())
