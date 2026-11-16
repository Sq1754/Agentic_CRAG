"""Chat session and message router."""

from datetime import datetime
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from src.api.dependencies import get_current_user
from src.db.database import get_db
from src.db.models import User, WorkspaceMember
from src.services import chat_service

router = APIRouter(
    prefix="/api/v1/workspaces/{workspace_id}/chat",
    tags=["Chat"],
)


# ── Schemas ─────────────────────────────────────────────────────────────────


class CreateSessionRequest(BaseModel):
    title: str = Field(default="New Chat", max_length=500)


class SessionResponse(BaseModel):
    id: UUID
    title: str
    created_at: datetime
    updated_at: datetime
    message_count: int = 0

    model_config = {"from_attributes": True}


class MessageResponse(BaseModel):
    id: UUID
    role: str
    content: str
    rewritten_query: str | None = None
    relevance_status: str | None = None
    loop_count: int = 0
    citations: list | None = None
    latency_ms: float | None = None
    created_at: datetime

    model_config = {"from_attributes": True}


# ── Helpers ─────────────────────────────────────────────────────────────────


def _verify_membership(db: Session, workspace_id: UUID, user_id: UUID):
    """Verify user is a workspace member, raise 403 otherwise."""
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


# ── Endpoints ───────────────────────────────────────────────────────────────


@router.post("/sessions", response_model=SessionResponse, status_code=status.HTTP_201_CREATED)
def create_chat_session(
    workspace_id: UUID,
    body: CreateSessionRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Create a new chat session in a workspace."""
    _verify_membership(db, workspace_id, current_user.id)

    session = chat_service.create_session(
        db, workspace_id=workspace_id, user_id=current_user.id, title=body.title
    )
    return SessionResponse(
        id=session.id,
        title=session.title,
        created_at=session.created_at,
        updated_at=session.updated_at,
        message_count=0,
    )


@router.get("/sessions", response_model=list[SessionResponse])
def list_sessions(
    workspace_id: UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """List chat sessions for the current user in a workspace."""
    _verify_membership(db, workspace_id, current_user.id)

    sessions = chat_service.get_workspace_sessions(
        db, workspace_id=workspace_id, user_id=current_user.id
    )
    return [
        SessionResponse(
            id=s.id,
            title=s.title,
            created_at=s.created_at,
            updated_at=s.updated_at,
            message_count=len(s.messages) if s.messages else 0,
        )
        for s in sessions
    ]


@router.get("/sessions/{session_id}", response_model=SessionResponse)
def get_session(
    workspace_id: UUID,
    session_id: UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Get a specific chat session."""
    _verify_membership(db, workspace_id, current_user.id)

    session = chat_service.get_session_by_id(db, session_id)
    if not session or session.workspace_id != workspace_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Session not found")
    if session.user_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied")

    return SessionResponse(
        id=session.id,
        title=session.title,
        created_at=session.created_at,
        updated_at=session.updated_at,
        message_count=len(session.messages) if session.messages else 0,
    )


@router.get("/sessions/{session_id}/messages", response_model=list[MessageResponse])
def get_messages(
    workspace_id: UUID,
    session_id: UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Get all messages in a chat session."""
    _verify_membership(db, workspace_id, current_user.id)

    session = chat_service.get_session_by_id(db, session_id)
    if not session or session.workspace_id != workspace_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Session not found")
    if session.user_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied")

    return chat_service.get_session_messages(db, session_id)


@router.delete("/sessions/{session_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_chat_session(
    workspace_id: UUID,
    session_id: UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Delete a chat session and all its messages."""
    _verify_membership(db, workspace_id, current_user.id)

    session = chat_service.get_session_by_id(db, session_id)
    if not session or session.workspace_id != workspace_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Session not found")
    if session.user_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied")

    chat_service.delete_session(db, session_id)
