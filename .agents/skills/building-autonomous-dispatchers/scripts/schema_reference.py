"""
Enterprise Job Queue Schema Reference
Compliant with strict typing (PEP 484) and Pydantic validation.
Implements robust "At-Least-Once" features including locking and retry backoff.
"""
import enum
import uuid
from datetime import UTC, datetime

from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy import Column, DateTime, Integer, String
from sqlalchemy import Enum as SAEnum
from sqlalchemy.orm import declarative_base

# -----------------------------------------------------------------------------
# 1. Enums and Constants
# -----------------------------------------------------------------------------

class JobStatus(str, enum.Enum):
    PENDING = "PENDING"
    OCR_PROCESSING = "OCR_PROCESSING"
    LLM_EXTRACTION = "LLM_EXTRACTION"
    FHIR_GENERATED = "FHIR_GENERATED"
    ERROR = "ERROR"
    FAILED_PERMANENTLY = "FAILED_PERMANENTLY"

MAX_RETRIES = 3

# -----------------------------------------------------------------------------
# 2. SQLAlchemy ORM Model
# -----------------------------------------------------------------------------

Base = declarative_base()

class Job(Base):
    """
    SQLAlchemy model representing a file processing job in the priority queue.
    Includes fields for distributed locking and retry management to prevent
    GPU starvation or parallel overlap.
    """
    __tablename__ = "background_jobs"

    # Core
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    file_path = Column(String(1024), nullable=False, index=True)
    status = Column(SAEnum(JobStatus), nullable=False, default=JobStatus.PENDING, index=True)

    # State tracking & Error handling
    error_message = Column(String(4096), nullable=True)
    retry_count = Column(Integer, nullable=False, default=0)

    # Distributed Locking (For Horizontal Scaling / Worker crash recovery)
    lock_id = Column(String(36), nullable=True, index=True)  # UUID of the worker processing it
    locked_at = Column(DateTime(timezone=True), nullable=True)
    next_retry_at = Column(DateTime(timezone=True), nullable=True)

    # Timestamps
    created_at = Column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(UTC))
    updated_at = Column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(UTC), onupdate=lambda: datetime.now(UTC))

# -----------------------------------------------------------------------------
# 3. Pydantic Validation Models
# -----------------------------------------------------------------------------

class JobCreate(BaseModel):
    """Model for enqueueing a new job."""
    file_path: str = Field(..., description="Absolute path to the ingress file (PDF/HL7)")

    model_config = ConfigDict(frozen=True)


class JobUpdate(BaseModel):
    """Model for updating an existing job state."""
    status: JobStatus | None = None
    error_message: str | None = None
    lock_id: str | None = None
    locked_at: datetime | None = None
    retry_count: int | None = None
    next_retry_at: datetime | None = None

    model_config = ConfigDict(extra="forbid")


class JobResponse(BaseModel):
    """Model mapping the DB output, safe for API usage."""
    id: str
    file_path: str
    status: JobStatus
    error_message: str | None = None
    retry_count: int
    lock_id: str | None = None
    locked_at: datetime | None = None
    next_retry_at: datetime | None = None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)
