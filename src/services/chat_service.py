"""Chat session and message persistence service."""

from datetime import datetime
from uuid import UUID

from sqlalchemy.orm import Session

from src.db.models import ChatMessage, ChatSession


def create_session(
    db: Session, workspace_id: UUID, user_id: UUID, title: str = "New Chat"
) -> ChatSession:
    """Create a new chat session in a workspace."""
    session = ChatSession(
        workspace_id=workspace_id,
        user_id=user_id,
        title=title,
    )
    db.add(session)
    db.commit()
    db.refresh(session)
    return session


def get_workspace_sessions(
    db: Session, workspace_id: UUID, user_id: UUID, limit: int = 50
) -> list[ChatSession]:
    """Return chat sessions for a user in a workspace, newest first."""
    return (
        db.query(ChatSession)
        .filter(
            ChatSession.workspace_id == workspace_id,
            ChatSession.user_id == user_id,
        )
        .order_by(ChatSession.updated_at.desc())
        .limit(limit)
        .all()
    )


def get_session_by_id(db: Session, session_id: UUID) -> ChatSession | None:
    """Fetch a single chat session by ID."""
    return db.query(ChatSession).filter(ChatSession.id == session_id).first()


def get_session_messages(
    db: Session, session_id: UUID, limit: int = 100
) -> list[ChatMessage]:
    """Return messages in a session, oldest first."""
    return (
        db.query(ChatMessage)
        .filter(ChatMessage.session_id == session_id)
        .order_by(ChatMessage.created_at.asc())
        .limit(limit)
        .all()
    )


def save_user_message(db: Session, session_id: UUID, content: str) -> ChatMessage:
    """Persist a user message to a chat session."""
    message = ChatMessage(
        session_id=session_id,
        role="user",
        content=content,
    )
    db.add(message)

    # Update session title from first user message if still default
    session = db.query(ChatSession).filter(ChatSession.id == session_id).first()
    if session and session.title == "New Chat":
        session.title = content[:80] + ("..." if len(content) > 80 else "")
    if session:
        session.updated_at = datetime.utcnow()

    db.commit()
    db.refresh(message)
    return message


def save_assistant_message(
    db: Session,
    session_id: UUID,
    content: str,
    rewritten_query: str | None = None,
    relevance_status: str = "unknown",
    loop_count: int = 0,
    citations: list[dict] | None = None,
    latency_ms: float = 0.0,
) -> ChatMessage:
    """Persist an assistant (CRAG) response with full metadata."""
    message = ChatMessage(
        session_id=session_id,
        role="assistant",
        content=content,
        rewritten_query=rewritten_query,
        relevance_status=relevance_status,
        loop_count=loop_count,
        citations=citations or [],
        latency_ms=latency_ms,
    )
    db.add(message)

    # Update session timestamp
    session = db.query(ChatSession).filter(ChatSession.id == session_id).first()
    if session:
        session.updated_at = datetime.utcnow()

    db.commit()
    db.refresh(message)
    return message


def delete_session(db: Session, session_id: UUID) -> bool:
    """Delete a chat session and all its messages."""
    session = db.query(ChatSession).filter(ChatSession.id == session_id).first()
    if session is None:
        return False
    db.delete(session)  # cascade deletes messages
    db.commit()
    return True
