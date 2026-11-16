"""
Database engine, session factory, and base model for SQLAlchemy 2.0.

Uses synchronous psycopg2 driver.  All FastAPI routes obtain a session via the
``get_db`` dependency, which yields a scoped session and guarantees cleanup.
"""

from collections.abc import Generator

from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

from src.config import settings

# ── Engine ──────────────────────────────────────────────────────────────────
engine = create_engine(
    settings.database_url,
    pool_pre_ping=True,
    pool_size=10,
    max_overflow=20,
    echo=settings.debug,
)

# ── Session factory ─────────────────────────────────────────────────────────
SessionLocal = sessionmaker(
    bind=engine,
    autocommit=False,
    autoflush=False,
    expire_on_commit=False,
)


# ── Declarative base ────────────────────────────────────────────────────────
class Base(DeclarativeBase):
    """Application-wide declarative base for all ORM models."""

    pass


# ── Dependency ──────────────────────────────────────────────────────────────
def get_db() -> Generator[Session, None, None]:
    """FastAPI dependency that provides a database session per request.

    Yields a ``Session`` and ensures it is closed after the request completes,
    regardless of whether an exception occurred.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# ── Table creation helper ──────────────────────────────────────────────────
def create_tables() -> None:
    """Create all tables defined on ``Base.metadata``.

    Intended for development / first-run bootstrapping.  In production
    environments, prefer Alembic migrations.
    """
    Base.metadata.create_all(bind=engine)
