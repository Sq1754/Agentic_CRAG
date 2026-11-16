"""
SQLAlchemy 2.0 ORM models for DocuMind.

All models use the ``mapped_column`` style and inherit from the shared
``Base`` declared in ``src.db.database``.
"""

import uuid
from datetime import datetime

from sqlalchemy import (
    DateTime,
    Float,
    ForeignKey,
    Integer,
    JSON,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.db.database import Base


# ── User ────────────────────────────────────────────────────────────────────
class User(Base):
    """Application user account."""

    __tablename__ = "users"

    id: Mapped[uuid.UUID] = mapped_column(
        primary_key=True, default=uuid.uuid4
    )
    email: Mapped[str] = mapped_column(
        String(255), unique=True, index=True, nullable=False
    )
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    hashed_password: Mapped[str] = mapped_column(String(255), nullable=False)
    avatar_url: Mapped[str | None] = mapped_column(
        String(500), nullable=True, default=None
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow
    )

    # ── Relationships ───────────────────────────────────────────────────
    owned_workspaces: Mapped[list["Workspace"]] = relationship(
        back_populates="owner", cascade="all, delete-orphan"
    )
    memberships: Mapped[list["WorkspaceMember"]] = relationship(
        back_populates="user", cascade="all, delete-orphan"
    )
    documents: Mapped[list["Document"]] = relationship(
        back_populates="uploader", cascade="all, delete-orphan"
    )
    chat_sessions: Mapped[list["ChatSession"]] = relationship(
        back_populates="user", cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return f"<User {self.email}>"


# ── Workspace ───────────────────────────────────────────────────────────────
class Workspace(Base):
    """A collaborative workspace that groups documents and chats."""

    __tablename__ = "workspaces"

    id: Mapped[uuid.UUID] = mapped_column(
        primary_key=True, default=uuid.uuid4
    )
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    slug: Mapped[str] = mapped_column(
        String(200), unique=True, index=True, nullable=False
    )
    description: Mapped[str | None] = mapped_column(
        Text, nullable=True, default=None
    )
    owner_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id"), nullable=False
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow
    )

    # ── Relationships ───────────────────────────────────────────────────
    owner: Mapped["User"] = relationship(back_populates="owned_workspaces")
    members: Mapped[list["WorkspaceMember"]] = relationship(
        back_populates="workspace", cascade="all, delete-orphan"
    )
    documents: Mapped[list["Document"]] = relationship(
        back_populates="workspace", cascade="all, delete-orphan"
    )
    chat_sessions: Mapped[list["ChatSession"]] = relationship(
        back_populates="workspace", cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return f"<Workspace {self.slug}>"


# ── WorkspaceMember ─────────────────────────────────────────────────────────
class WorkspaceMember(Base):
    """Junction model tracking which users belong to which workspaces."""

    __tablename__ = "workspace_members"
    __table_args__ = (
        UniqueConstraint("workspace_id", "user_id", name="uq_workspace_user"),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        primary_key=True, default=uuid.uuid4
    )
    workspace_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("workspaces.id"), nullable=False
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id"), nullable=False
    )
    role: Mapped[str] = mapped_column(
        String(20), nullable=False, default="member"
    )
    joined_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow
    )

    # ── Relationships ───────────────────────────────────────────────────
    workspace: Mapped["Workspace"] = relationship(back_populates="members")
    user: Mapped["User"] = relationship(back_populates="memberships")

    def __repr__(self) -> str:
        return f"<WorkspaceMember user={self.user_id} workspace={self.workspace_id} role={self.role}>"


# ── Document ────────────────────────────────────────────────────────────────
class Document(Base):
    """An uploaded document that has been (or is being) processed."""

    __tablename__ = "documents"

    id: Mapped[uuid.UUID] = mapped_column(
        primary_key=True, default=uuid.uuid4
    )
    workspace_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("workspaces.id"), nullable=False
    )
    uploaded_by: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id"), nullable=False
    )
    filename: Mapped[str] = mapped_column(String(500), nullable=False)
    file_type: Mapped[str] = mapped_column(
        String(20), nullable=False
    )  # pdf, docx, md, txt
    file_size: Mapped[int | None] = mapped_column(
        Integer, nullable=True, default=None
    )
    storage_path: Mapped[str | None] = mapped_column(
        String(1000), nullable=True, default=None
    )
    chunk_count: Mapped[int] = mapped_column(
        Integer, nullable=False, default=0
    )
    status: Mapped[str] = mapped_column(
        String(20), nullable=False, default="processing"
    )  # processing, ready, failed
    error_message: Mapped[str | None] = mapped_column(
        Text, nullable=True, default=None
    )
    metadata_json: Mapped[dict | None] = mapped_column(
        JSON, nullable=True, default=None
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow
    )

    # ── Relationships ───────────────────────────────────────────────────
    workspace: Mapped["Workspace"] = relationship(back_populates="documents")
    uploader: Mapped["User"] = relationship(back_populates="documents")

    def __repr__(self) -> str:
        return f"<Document {self.filename} ({self.status})>"


# ── ChatSession ─────────────────────────────────────────────────────────────
class ChatSession(Base):
    """A conversation session within a workspace."""

    __tablename__ = "chat_sessions"

    id: Mapped[uuid.UUID] = mapped_column(
        primary_key=True, default=uuid.uuid4
    )
    workspace_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("workspaces.id"), nullable=False
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id"), nullable=False
    )
    title: Mapped[str] = mapped_column(
        String(500), nullable=False, default="New Chat"
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow
    )

    # ── Relationships ───────────────────────────────────────────────────
    workspace: Mapped["Workspace"] = relationship(
        back_populates="chat_sessions"
    )
    user: Mapped["User"] = relationship(back_populates="chat_sessions")
    messages: Mapped[list["ChatMessage"]] = relationship(
        back_populates="session", cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return f"<ChatSession {self.title[:30]}>"


# ── ChatMessage ─────────────────────────────────────────────────────────────
class ChatMessage(Base):
    """A single message (user or assistant) within a chat session."""

    __tablename__ = "chat_messages"

    id: Mapped[uuid.UUID] = mapped_column(
        primary_key=True, default=uuid.uuid4
    )
    session_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("chat_sessions.id"), nullable=False
    )
    role: Mapped[str] = mapped_column(
        String(20), nullable=False
    )  # user, assistant
    content: Mapped[str] = mapped_column(Text, nullable=False)
    rewritten_query: Mapped[str | None] = mapped_column(
        Text, nullable=True, default=None
    )
    relevance_status: Mapped[str | None] = mapped_column(
        String(20), nullable=True, default=None
    )
    loop_count: Mapped[int] = mapped_column(
        Integer, nullable=False, default=0
    )
    citations: Mapped[dict | list | None] = mapped_column(
        JSON, nullable=True, default=None
    )
    latency_ms: Mapped[float | None] = mapped_column(
        Float, nullable=True, default=None
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow
    )

    # ── Relationships ───────────────────────────────────────────────────
    session: Mapped["ChatSession"] = relationship(back_populates="messages")

    def __repr__(self) -> str:
        return f"<ChatMessage {self.role} session={self.session_id}>"
