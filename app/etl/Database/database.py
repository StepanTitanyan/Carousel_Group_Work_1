"""
Database Configuration
"""

import os
from pathlib import Path
from dotenv import load_dotenv

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base


# --------------------------------------------------
# Load environment variables
# --------------------------------------------------
load_dotenv(Path(__file__).resolve().parents[2] / ".env")


# --------------------------------------------------
# Build DATABASE URL
# --------------------------------------------------
def _build_database_url() -> str:
    database_url = os.environ.get("DATABASE_URL")
    if database_url:
        return database_url

    db_user = os.environ.get("DB_USER")
    db_password = os.environ.get("DB_PASSWORD")
    db_name = os.environ.get("DB_NAME")
    db_host = os.environ.get("DB_HOST", "db")       # Docker default
    db_port = os.environ.get("DB_PORT", "5432")

    if db_user and db_password and db_name:
        return f"postgresql+psycopg2://{db_user}:{db_password}@{db_host}:{db_port}/{db_name}"

    raise RuntimeError(
        "DATABASE_URL is not set and DB_USER/DB_PASSWORD/DB_NAME are incomplete."
    )


DATABASE_URL = _build_database_url()


# --------------------------------------------------
# Engine
# --------------------------------------------------
engine = create_engine(
    DATABASE_URL,
    pool_pre_ping=True,   # avoids stale connections (important in Docker)
    echo=False            #? set True for debugging
)


# --------------------------------------------------
# Base class for models
# --------------------------------------------------
Base = declarative_base()


# --------------------------------------------------
# Session
# --------------------------------------------------
SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine
)


# --------------------------------------------------
# FastAPI dependency
# --------------------------------------------------
def get_db():
    """
    Provides a database session per request
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()