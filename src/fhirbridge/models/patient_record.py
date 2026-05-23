from datetime import datetime
from uuid import UUID, uuid4

from sqlalchemy import Column, String, DateTime, Text
from sqlalchemy.dialects.postgresql import UUID as pgUUID
from sqlalchemy.orm import declarative_base

from pydantic import BaseModel, ConfigDict, Field

Base = declarative_base()

class PatientLongitudinalRecordDB(Base):
    """SQLAlchemy Modell für das langfristige Tracking von Patienten-Dokumenten (S3)."""
    __tablename__ = 'patient_longitudinal_records'

    id = Column(pgUUID(as_uuid=True), primary_key=True, default=uuid4)
    patient_id = Column(String(255), nullable=False, index=True)
    encounter_id = Column(String(255), nullable=False, index=True)
    document_id = Column(String(512), nullable=False, unique=True, index=True) # MinIO S3 Key (S-Token)
    document_type = Column(String(50), nullable=True) # z.B. 'discharge_summary'
    presigned_url = Column(Text, nullable=True) # Optional fürs kurzfristige Caching
    created_at = Column(DateTime, default=datetime.utcnow)

class PatientLongitudinalRecord(BaseModel):
    """Pydantic Modell für Inter-Service Messaging & Validierung."""
    id: UUID = Field(default_factory=uuid4)
    patient_id: str
    encounter_id: str
    document_id: str = Field(..., description="MinIO S3 Key (S-Token)")
    document_type: str | None = None
    created_at: datetime = Field(default_factory=datetime.utcnow)

    model_config = ConfigDict(from_attributes=True)
