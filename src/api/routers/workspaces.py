"""Workspace management router."""

from datetime import datetime
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from src.api.dependencies import get_current_user
from src.db.database import get_db
from src.db.models import User, WorkspaceMember
from src.services import workspace_service

router = APIRouter(prefix="/api/v1/workspaces", tags=["Workspaces"])


# ── Schemas ─────────────────────────────────────────────────────────────────


class CreateWorkspaceRequest(BaseModel):
    name: str = Field(..., min_length=1, max_length=200)
    description: str = Field(default="", max_length=2000)


class WorkspaceResponse(BaseModel):
    id: UUID
    name: str
    slug: str
    description: str | None = None
    owner_id: UUID
    created_at: datetime
    member_count: int = 0

    model_config = {"from_attributes": True}


class AddMemberRequest(BaseModel):
    email: str
    role: str = Field(default="member", pattern="^(admin|member|viewer)$")


class MemberResponse(BaseModel):
    id: UUID
    user_id: UUID
    email: str
    name: str
    role: str
    joined_at: datetime


# ── Helpers ─────────────────────────────────────────────────────────────────


def _to_workspace_response(ws) -> WorkspaceResponse:
    """Convert a Workspace ORM object to its response model."""
    return WorkspaceResponse(
        id=ws.id,
        name=ws.name,
        slug=ws.slug,
        description=ws.description,
        owner_id=ws.owner_id,
        created_at=ws.created_at,
        member_count=len(ws.members) if ws.members else 0,
    )


def _verify_admin(db: Session, workspace_id: UUID, user_id: UUID) -> WorkspaceMember:
    """Ensure the user is an admin of the workspace."""
    member = (
        db.query(WorkspaceMember)
        .filter(
            WorkspaceMember.workspace_id == workspace_id,
            WorkspaceMember.user_id == user_id,
        )
        .first()
    )
    if not member:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not a workspace member")
    if member.role != "admin":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Admin access required")
    return member


# ── Endpoints ───────────────────────────────────────────────────────────────


@router.post("/", response_model=WorkspaceResponse, status_code=status.HTTP_201_CREATED)
def create_workspace(
    body: CreateWorkspaceRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Create a new workspace. The creator becomes the admin."""
    ws = workspace_service.create_workspace(
        db, owner_id=current_user.id, name=body.name, description=body.description
    )
    return _to_workspace_response(ws)


@router.get("/", response_model=list[WorkspaceResponse])
def list_workspaces(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """List all workspaces the current user belongs to."""
    workspaces = workspace_service.get_user_workspaces(db, user_id=current_user.id)
    return [_to_workspace_response(ws) for ws in workspaces]


@router.get("/{workspace_id}", response_model=WorkspaceResponse)
def get_workspace(
    workspace_id: UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Get workspace details (requires membership)."""
    # Verify membership
    member = (
        db.query(WorkspaceMember)
        .filter(
            WorkspaceMember.workspace_id == workspace_id,
            WorkspaceMember.user_id == current_user.id,
        )
        .first()
    )
    if not member:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not a workspace member")

    ws = workspace_service.get_workspace_by_id(db, workspace_id)
    if not ws:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Workspace not found")
    return _to_workspace_response(ws)


@router.post("/{workspace_id}/members", response_model=MemberResponse, status_code=status.HTTP_201_CREATED)
def add_member(
    workspace_id: UUID,
    body: AddMemberRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Add a member to a workspace (admin only)."""
    _verify_admin(db, workspace_id, current_user.id)

    try:
        member = workspace_service.add_member(db, workspace_id, body.email, body.role)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

    user = db.query(User).filter(User.id == member.user_id).first()
    return MemberResponse(
        id=member.id,
        user_id=member.user_id,
        email=user.email if user else "",
        name=user.name if user else "",
        role=member.role,
        joined_at=member.joined_at,
    )


@router.delete("/{workspace_id}/members/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
def remove_member(
    workspace_id: UUID,
    user_id: UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Remove a member from a workspace (admin only, cannot remove owner)."""
    _verify_admin(db, workspace_id, current_user.id)

    try:
        removed = workspace_service.remove_member(db, workspace_id, user_id)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

    if not removed:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Member not found")


@router.delete("/{workspace_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_workspace(
    workspace_id: UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Delete a workspace (owner only)."""
    try:
        deleted = workspace_service.delete_workspace(db, workspace_id, current_user.id)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(e))

    if not deleted:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Workspace not found")
