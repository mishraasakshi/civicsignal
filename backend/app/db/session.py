"""Database connection: one engine for the app, one session per request."""

from collections.abc import Iterator

from app.core.config import settings
from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker


def database_url() -> str:
    """Use the psycopg2 driver (installed) - SQLAlchemy 2.1 defaults 'postgresql://' to psycopg 3."""
    url = settings.DATABASE_URL
    if url.startswith("postgresql://"):
        url = "postgresql+psycopg2://" + url.removeprefix("postgresql://")
    return url


engine = create_engine(database_url(), pool_pre_ping=True)
SessionLocal = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)


class Base(DeclarativeBase):
    """Parent class for all tables."""


def get_db() -> Iterator[Session]:
    """FastAPI dependency: open a session for one request, always close it."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
