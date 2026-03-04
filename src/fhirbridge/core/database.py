"""
Database setup for the FhirBridgeAI Dispatcher.
Uses SQLAlchemy ORM with PostgreSQL (via Alembic / create_all).
"""

import enum
import logging
import os
from datetime import datetime

from sqlalchemy import Column, DateTime, Engine, Integer, String, Text, create_engine
from sqlalchemy import Enum as SAEnum
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

from fhirbridge.core.config import get_settings

logger = logging.getLogger(__name__)


class Base(DeclarativeBase):
    pass


class JobStatus(enum.StrEnum):
    """Single Source of Truth for all pipeline job statuses."""

    PENDING = "PENDING"
    OCR_PROCESSING = "OCR_PROCESSING"
    LLM_EXTRACTION = "LLM_EXTRACTION"
    FHIR_GENERATED = "FHIR_GENERATED"
    EXPORTING = "EXPORTING"
    EXPORTED = "EXPORTED"
    FAILED = "FAILED"
    EXPORT_FAILED = "EXPORT_FAILED"


class Job(Base):
    __tablename__ = "jobs"

    id = Column(Integer, primary_key=True, autoincrement=True)
    filepath = Column(String, unique=True, nullable=False)
    status = Column(
        SAEnum(JobStatus, values_callable=lambda e: [x.value for x in e]),
        nullable=False,
        default=JobStatus.PENDING,
    )

    # Process outputs
    ocr_text = Column(Text, nullable=True)  # Result from Tesseract
    fhir_json = Column(Text, nullable=True)  # Result from Mistral-NeMo

    output_path = Column(String, nullable=True)
    error_trace = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


def get_engine(db_path: str = "data/dispatcher.db") -> Engine:
    """
    Creates an SQLAlchemy engine.
    Uses DATABASE_URL (Postgres) from settings. Falls back to SQLite for local dev.
    """
    database_url = get_settings().database_url
    if database_url:
        return create_engine(database_url, pool_pre_ping=True)

    os.makedirs(os.path.dirname(db_path), exist_ok=True)

    engine = create_engine(
        f"sqlite:///{db_path}",
        connect_args={"check_same_thread": False},
        pool_pre_ping=True,
    )
    return engine


def init_db(db_path: str = "data/dispatcher.db") -> Engine:
    """Initializes the database engine and creates tables if needed."""
    engine = get_engine(db_path)
    Base.metadata.create_all(engine)
    return engine


def get_session_factory(engine: Engine) -> sessionmaker[Session]:
    return sessionmaker(bind=engine)
