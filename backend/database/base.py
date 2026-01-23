"""Database base configuration."""

from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from sqlalchemy.exc import OperationalError
from typing import Optional
from backend.core.config import settings

# Lazy initialization - only create engine when needed
_engine: Optional[object] = None
_SessionLocal: Optional[sessionmaker] = None

# Base class for models
Base = declarative_base()


def _get_engine():
    """Lazy initialization of database engine."""
    global _engine
    if _engine is None:
        try:
            _engine = create_engine(
                settings.DATABASE_URL,
                pool_pre_ping=True,
                pool_size=10,
                max_overflow=20,
                echo=settings.DEBUG,
                connect_args={"connect_timeout": 5}
            )
        except Exception as e:
            # If database is not available, create a dummy engine
            # This allows the app to start without PostgreSQL
            print(f"Warning: Database connection failed: {e}")
            print("Continuing without database connection (some features may be limited)")
            # Use SQLite as fallback for development
            _engine = create_engine(
                "sqlite:///./antenna_twin_dev.db",
                pool_pre_ping=True,
                echo=settings.DEBUG
            )
    return _engine


def _get_session_local():
    """Lazy initialization of session factory."""
    global _SessionLocal
    if _SessionLocal is None:
        engine = _get_engine()
        _SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    return _SessionLocal


def get_db():
    """Dependency for getting database session."""
    try:
        SessionLocal = _get_session_local()
        db = SessionLocal()
        try:
            yield db
        finally:
            db.close()
    except OperationalError as e:
        # Database not available - return None or raise
        print(f"Database operation failed: {e}")
        # For now, we'll allow endpoints to work without DB
        # by not requiring db dependency where not critical
        raise



















