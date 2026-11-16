"""Workspace and member management service."""

import re
import secrets
from uuid import UUID

from sqlalchemy.orm import Session

from src.db.models import User, Workspace, WorkspaceMember


def _generate_slug(name: str) -> str:
    """Generate a URL-safe slug from a workspace name.

    Lowercases, replaces whitespace with hyphens, strips non-alphanumeric
    characters, and appends a 4-character random suffix for uniqueness.
    """
    slug = name.lower().strip()
    slug = re.sub(r"\s+", "-", slug)
    slug = re.sub(r"[^a-z0-9\-]", "", slug)
    slug = slug.strip("-") or "workspace"
    suffix = secrets.token_hex(2)  # 4 hex chars
    return f"{slug}-{suffix}"


def create_workspace(
    db: Session, owner_id: UUID, name: str, description: str = ""
) -> Workspace:
    """Create a new workspace and add the owner as an admin member."""
    workspace = Workspace(
        name=name,
        slug=_generate_slug(name),
        description=description or None,
        owner_id=owner_id,
    )
    db.add(workspace)
    db.flush()  # Populate workspace.id before creating the member

    member = WorkspaceMember(
        workspace_id=workspace.id,
        user_id=owner_id,
        role="admin",
    )
    db.add(member)
    db.commit()
    db.refresh(workspace)
    return workspace


def get_user_workspaces(db: Session, user_id: UUID) -> list[Workspace]:
    """Return all workspaces where *user_id* is a member."""
    return (
        db.query(Workspace)
        .join(WorkspaceMember, WorkspaceMember.workspace_id == Workspace.id)
        .filter(WorkspaceMember.user_id == user_id)
        .order_by(Workspace.created_at.desc())
        .all()
    )


def get_workspace_by_id(db: Session, workspace_id: UUID) -> Workspace | None:
    """Fetch a single workspace by its primary key."""
    return db.query(Workspace).filter(Workspace.id == workspace_id).first()


def add_member(
    db: Session, workspace_id: UUID, email: str, role: str = "member"
) -> WorkspaceMember:
    """Add a user (looked up by email) to a workspace.

    Raises ``ValueError`` if the user is not found or is already a member.
    """
    user = db.query(User).filter(User.email == email).first()
    if user is None:
        raise ValueError(f"No user found with email '{email}'")

    existing = (
        db.query(WorkspaceMember)
        .filter(
            WorkspaceMember.workspace_id == workspace_id,
            WorkspaceMember.user_id == user.id,
        )
        .first()
    )
    if existing is not None:
        raise ValueError(f"User '{email}' is already a member of this workspace")

    member = WorkspaceMember(
        workspace_id=workspace_id,
        user_id=user.id,
        role=role,
    )
    db.add(member)
    db.commit()
    db.refresh(member)
    return member


def remove_member(db: Session, workspace_id: UUID, user_id: UUID) -> bool:
    """Remove a member from a workspace.

    The workspace owner cannot be removed.  Returns ``True`` on success.
    Raises ``ValueError`` if trying to remove the owner.
    """
    workspace = db.query(Workspace).filter(Workspace.id == workspace_id).first()
    if workspace and workspace.owner_id == user_id:
        raise ValueError("Cannot remove the workspace owner")

    member = (
        db.query(WorkspaceMember)
        .filter(
            WorkspaceMember.workspace_id == workspace_id,
            WorkspaceMember.user_id == user_id,
        )
        .first()
    )
    if member is None:
        return False

    db.delete(member)
    db.commit()
    return True


def delete_workspace(db: Session, workspace_id: UUID, user_id: UUID) -> bool:
    """Delete a workspace.  Only the owner may delete.

    Raises ``ValueError`` if the requesting user is not the owner.
    """
    workspace = db.query(Workspace).filter(Workspace.id == workspace_id).first()
    if workspace is None:
        return False
    if workspace.owner_id != user_id:
        raise ValueError("Only the workspace owner can delete this workspace")

    db.delete(workspace)
    db.commit()
    return True
