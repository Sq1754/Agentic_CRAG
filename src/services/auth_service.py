"""
Authentication service for DocuMind.

Handles password hashing (bcrypt via passlib), JWT token management
(python-jose), user registration, and credential verification.
"""

from datetime import datetime, timedelta
from uuid import UUID

from jose import JWTError, jwt
from passlib.context import CryptContext
from sqlalchemy.orm import Session

from src.config import settings
from src.db.models import User

# ── Password hashing context ───────────────────────────────────────────────
_pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


# ── Password helpers ────────────────────────────────────────────────────────

def hash_password(password: str) -> str:
    """Return a bcrypt hash of *password*."""
    return _pwd_context.hash(password)


def verify_password(plain: str, hashed: str) -> bool:
    """Return ``True`` if *plain* matches *hashed*."""
    return _pwd_context.verify(plain, hashed)


# ── JWT helpers ─────────────────────────────────────────────────────────────

def create_access_token(
    data: dict,
    expires_delta: timedelta | None = None,
) -> str:
    """Create a signed JWT containing *data*.

    If *expires_delta* is ``None`` the token expires after the number of
    minutes configured in ``settings.jwt_access_token_expire_minutes``.
    """
    to_encode = data.copy()
    expire = datetime.utcnow() + (
        expires_delta
        if expires_delta is not None
        else timedelta(minutes=settings.jwt_access_token_expire_minutes)
    )
    to_encode.update({"exp": expire})
    return jwt.encode(
        to_encode,
        settings.jwt_secret_key,
        algorithm=settings.jwt_algorithm,
    )


def decode_access_token(token: str) -> dict:
    """Decode and verify a JWT, returning its payload.

    Raises ``jose.JWTError`` if the token is invalid or expired.
    """
    return jwt.decode(
        token,
        settings.jwt_secret_key,
        algorithms=[settings.jwt_algorithm],
    )


# ── User CRUD / auth operations ────────────────────────────────────────────

def register_user(
    db: Session,
    email: str,
    name: str,
    password: str,
) -> User:
    """Create a new user after verifying the email is not already taken.

    Raises ``ValueError`` if the email is already registered.
    """
    existing = db.query(User).filter(User.email == email).first()
    if existing is not None:
        raise ValueError(f"A user with email '{email}' already exists")

    user = User(
        email=email,
        name=name,
        hashed_password=hash_password(password),
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def authenticate_user(
    db: Session,
    email: str,
    password: str,
) -> User | None:
    """Return the ``User`` if *email* and *password* are valid, else ``None``."""
    user = db.query(User).filter(User.email == email).first()
    if user is None:
        return None
    if not verify_password(password, user.hashed_password):
        return None
    return user


def get_user_by_id(db: Session, user_id: UUID) -> User | None:
    """Fetch a user by primary key, returning ``None`` if not found."""
    return db.query(User).filter(User.id == user_id).first()
