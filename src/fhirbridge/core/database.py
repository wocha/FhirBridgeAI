"""
Database setup for the FhirBridgeAI Dispatcher.
Uses SQLAlchemy ORM with SQLite Write-Ahead Logging (WAL) for safe concurrent reads.
"""

import logging
import os
import sqlite3
from datetime import datetime

from sqlalchemy import Column, DateTime, Engine, Integer, String, Text, create_engine
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

from fhirbridge.core.config import get_settings

logger = logging.getLogger(__name__)


class Base(DeclarativeBase):
    pass


class Job(Base):
    __tablename__ = "jobs"

    id = Column(Integer, primary_key=True, autoincrement=True)
    filepath = Column(String, unique=True, nullable=False)
    # Expected statuses: PENDING, OCR_PROCESSING, LLM_EXTRACTION, FHIR_GENERATED, ERROR
    status = Column(String, nullable=False, default="PENDING")

    # Process outputs
    ocr_text = Column(Text, nullable=True)  # Result from Tesseract
    fhir_json = Column(Text, nullable=True)  # Result from Mistral-NeMo

    output_path = Column(String, nullable=True)
    error_trace = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


def get_engine(db_path: str = "data/dispatcher.db") -> Engine:
    """
    Creates an SQLAlchemy engine configured for concurrent reads.
    If DATABASE_URL is set, uses Postgres. Otherwise falls back to SQLite (WAL mode).
    """
    database_url = get_settings().database_url
    if database_url:
        return create_engine(database_url, pool_pre_ping=True)

    os.makedirs(os.path.dirname(db_path), exist_ok=True)

    # Enable WAL mode via connect_args for SQLite
    engine = create_engine(
        f"sqlite:///{db_path}",
        connect_args={"check_same_thread": False},  # Required for multi-thread access
        pool_pre_ping=True,
    )
    return engine


def auto_upgrade_schema(db_path: str, engine: Engine, base: type[DeclarativeBase]) -> None:
    """
    Lightweight auto-migration for SQLite.
    Checks existing tables against SQLAlchemy models and adds missing columns.
    Only supports ADD COLUMN (additive migrations).
    """
    if engine.name != "sqlite" or not os.path.exists(db_path):
        return

    # Use raw SQLite connection to inspect and alter schema easily
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    for table_name, table in base.metadata.tables.items():
        # Get existing columns in the database
        cursor.execute(f"PRAGMA table_info({table_name})")
        existing_columns = {row[1] for row in cursor.fetchall()}

        if not existing_columns:
            continue  # Table doesn't exist yet, metadata.create_all handles it

        # Check model columns against existing
        for column in table.columns:
            if column.name not in existing_columns:
                # Determine SQL type based on SQLAlchemy type
                # For SQLite, TEXT, INTEGER, REAL, BLOB are primary.
                sql_type = "TEXT"  # Default fallback
                col_type_str = str(column.type).upper()
                if "INT" in col_type_str:
                    sql_type = "INTEGER"
                elif (
                    "DATETIME" in col_type_str
                    or "DATE" in col_type_str
                    or "VARCHAR" in col_type_str
                    or "STRING" in col_type_str
                ):
                    sql_type = "TEXT"
                elif "FLOAT" in col_type_str or "REAL" in col_type_str:
                    sql_type = "REAL"

                logger.info(
                    f"Auto-Migration: Adding column '{column.name}'"
                    f" ({sql_type}) to table '{table_name}'."
                )

                alter_stmt = f"ALTER TABLE {table_name} ADD COLUMN {column.name} {sql_type}"
                try:
                    cursor.execute(alter_stmt)
                    conn.commit()
                except sqlite3.OperationalError as e:
                    logger.error(f"Failed to add column {column.name} to {table_name}: {e}")

    conn.close()


def init_db(db_path: str = "data/dispatcher.db") -> Engine:
    engine = get_engine(db_path)

    # Run auto-migration before create_all ensures we don't crash if table exists but schemas differ
    if engine.name == "sqlite":
        auto_upgrade_schema(db_path, engine, Base)

    Base.metadata.create_all(engine)

    # Force WAL mode (needs raw connection)
    if engine.name == "sqlite":
        with engine.connect() as conn:
            conn.exec_driver_sql("PRAGMA journal_mode=WAL;")

    return engine


def get_session_factory(engine: Engine) -> sessionmaker[Session]:
    return sessionmaker(bind=engine)
