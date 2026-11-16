"""
FastAPI dependency functions for authentication and authorisation.

``get_current_user``
    Extracts and validates the JWT bearer token, returning the active
    ``User`` ORM instance.

``get_workspace_member``
    Ensures the authenticated user is a member of the requested workspace
    and returns the ``WorkspaceMember`` record.
"""

from uuid import UUID

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError
from sqlalchemy.orm import Session

from src.db.database import get_db
from src.db.models import User, WorkspaceMember
from src.services.auth_service import decode_access_token

# ── OAuth2 scheme ───────────────────────────────────────────────────────────
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login")


# ── Current user dependency ─────────────────────────────────────────────────
def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db),
) -> User:
    """Resolve the current authenticated user from the bearer token.

    Raises ``HTTPException(401)`` if the token is missing, expired,
    malformed, or references a non-existent user.
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

    try:
        payload = decode_access_token(token)
        user_id_str: str | None = payload.get("sub")
        if user_id_str is None:
            raise credentials_exception
        user_id = UUID(user_id_str)
    except (JWTError, ValueError):
        raise credentials_exception

    user = db.query(User).filter(User.id == user_id).first()
    if user is None:
        raise credentials_exception

    return user


# ── Workspace member dependency ─────────────────────────────────────────────
def get_workspace_member(
    workspace_id: UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> WorkspaceMember:
    """Verify the current user is a member of the given workspace.

    Raises ``HTTPException(403)`` if the user does not belong to the
    workspace.
    """
    membership = (
        db.query(WorkspaceMember)
        .filter(
            WorkspaceMember.workspace_id == workspace_id,
            WorkspaceMember.user_id == current_user.id,
        )
        .first()
    )

    if membership is None:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You are not a member of this workspace",
        )

    return membership
