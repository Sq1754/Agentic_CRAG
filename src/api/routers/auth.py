"""
Authentication router for DocuMind.

Provides user registration, login (OAuth2-compatible token endpoint),
and a ``/me`` route for retrieving the currently authenticated user.
"""

from datetime import datetime
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from pydantic import BaseModel, EmailStr, Field
from sqlalchemy.orm import Session

from src.db.database import get_db
from src.db.models import User
from src.api.dependencies import get_current_user
from src.services.auth_service import (
    authenticate_user,
    create_access_token,
    register_user,
)

# ── Router ──────────────────────────────────────────────────────────────────
router = APIRouter(prefix="/api/v1/auth", tags=["Authentication"])


# ── Request / Response schemas ──────────────────────────────────────────────

class RegisterRequest(BaseModel):
    """Payload for creating a new user account."""

    email: EmailStr
    name: str = Field(..., min_length=1, max_length=100)
    password: str = Field(..., min_length=6, max_length=128)


class LoginRequest(BaseModel):
    """Payload for username/password login (non-OAuth2 form)."""

    email: EmailStr
    password: str


class TokenResponse(BaseModel):
    """JWT access-token response."""

    access_token: str
    token_type: str = "bearer"


class UserResponse(BaseModel):
    """Public-facing user representation."""

    id: UUID
    email: str
    name: str
    avatar_url: str | None = None
    created_at: datetime

    model_config = {"from_attributes": True}


# ── Endpoints ───────────────────────────────────────────────────────────────

@router.post(
    "/register",
    response_model=UserResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Register a new user",
)
def register(body: RegisterRequest, db: Session = Depends(get_db)) -> User:
    """Create a new user account.

    Returns the created user on success.  Raises **400** if the email is
    already registered.
    """
    try:
        user = register_user(
            db,
            email=body.email,
            name=body.name,
            password=body.password,
        )
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        )
    return user


@router.post(
    "/login",
    response_model=TokenResponse,
    summary="Obtain an access token",
)
def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db),
) -> dict:
    """Authenticate with email (as ``username``) and password.

    Returns a bearer token on success.  Raises **401** if credentials are
    invalid.

    This endpoint accepts ``application/x-www-form-urlencoded`` bodies so
    it is compatible with the OAuth2 password flow used by Swagger UI.
    """
    user = authenticate_user(db, email=form_data.username, password=form_data.password)
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    access_token = create_access_token(data={"sub": str(user.id)})
    return {"access_token": access_token, "token_type": "bearer"}


@router.get(
    "/me",
    response_model=UserResponse,
    summary="Get the current authenticated user",
)
def get_me(current_user: User = Depends(get_current_user)) -> User:
    """Return the profile of the currently authenticated user.

    Requires a valid bearer token in the ``Authorization`` header.
    """
    return current_user
