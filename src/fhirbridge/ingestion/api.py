import json
import logging
import os
import uuid
from typing import Optional, Dict, Any

from fastapi import FastAPI, Depends, HTTPException, status, Security
from fastapi.security.api_key import APIKeyHeader
from pydantic import BaseModel, Field
import aio_pika
import aio_pika.abc

# Configure logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

# Constants and Configuration
API_KEY_NAME = "X-API-Key"
from fhirbridge.core.config import get_settings
from fhirbridge.core.database import Job, get_session_factory, init_db
from fhirbridge.core.rabbitmq import DocumentMetaData

API_KEY_SECRET = os.getenv("API_KEY_SECRET", "kritis-dev-key-change-in-prod")
RABBITMQ_URL = get_settings().rabbitmq_url
QUEUE_NAME = "llm_extraction_queue"

# Init DB
engine = init_db(os.getenv("DATABASE_URL", "sqlite:///data/dispatcher.db"))
SessionFactory = get_session_factory(engine)
EPHEMERAL_DIR = "/tmp/fhirbridge_ephemeral"
try:
    os.makedirs(EPHEMERAL_DIR, exist_ok=True)
except PermissionError:
    pass
# Security
api_key_header = APIKeyHeader(name=API_KEY_NAME, auto_error=True)

def get_api_key(api_key_header: str = Security(api_key_header)) -> str:
    if api_key_header != API_KEY_SECRET:
        logger.warning("Failed authentication attempt")
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Could not validate credentials"
        )
    return api_key_header


# Pydantic Models
class DocumentIngestionRequest(BaseModel):
    document_id: str = Field(default_factory=lambda: str(uuid.uuid4()), description="Client-provided or auto-generated UUID for the document")
    content: str = Field(..., description="The textual content of the document or OCR output")
    document_type: Optional[str] = Field(default="unknown", description="Type of the document, e.g., 'discharge_summary'")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional context metadata")

class DocumentIngestionResponse(BaseModel):
    status: str
    document_id: str
    message: str


# FastAPI Application
app = FastAPI(
    title="FhirBridgeAi Ingestion Gateway",
    description="High-throughput, asynchronous ingestion layer for medical documents.",
    version="1.0.0"
)

# RabbitMQ Connection Pool (Simple Global for now)
_rmq_connection: Optional[aio_pika.abc.AbstractRobustConnection] = None

async def get_rabbitmq_channel() -> Any:
    """Provides a RabbitMQ channel, establishing connection if required."""
    global _rmq_connection
    if not _rmq_connection or _rmq_connection.is_closed:
        logger.info("Connecting to RabbitMQ...")
        _rmq_connection = await aio_pika.connect_robust(RABBITMQ_URL)
    
    assert _rmq_connection is not None
    # Returning a channel (in production, we might want a pool instead of simple transient channels)
    return await _rmq_connection.channel()

@app.on_event("startup")
async def startup_event() -> None:
    """Initialize RabbitMQ connection and queues on startup."""
    try:
        channel = await get_rabbitmq_channel()
        # Declare the queue ensuring it exists
        await channel.declare_queue(QUEUE_NAME, durable=True)
        logger.info(f"Ingestion gateway started. Queue '{QUEUE_NAME}' is ready.")
        await channel.close()
    except Exception as e:
        logger.error(f"Failed to initialize RabbitMQ connection on startup: {e}")
        # Not exiting here to allow FastAPI to start and maybe recover later, but could be adjusted for fast failure.

@app.on_event("shutdown")
async def shutdown_event() -> None:
    """Clean up resources."""
    global _rmq_connection
    if _rmq_connection and not _rmq_connection.is_closed:
        await _rmq_connection.close()
        logger.info("RabbitMQ connection closed.")


@app.post(
    "/api/v1/documents",
    response_model=DocumentIngestionResponse,
    status_code=status.HTTP_202_ACCEPTED,
    summary="Ingest a new document for processing",
)
async def ingest_document(
    request: DocumentIngestionRequest,
    api_key: str = Depends(get_api_key)
) -> DocumentIngestionResponse:
    """
    Ingests a document as JSON, validates it, and asynchronously pushes it to RabbitMQ.
    Returns 202 Accepted immediately without waiting for processing.
    """
    try:
        channel = await get_rabbitmq_channel()
        
        # 1. Create Job in DB to get the required integer ID
        with SessionFactory() as session:
            new_job = Job(filepath=f"api_ingest_{request.document_id}", status="QUEUED_LLM")
            session.add(new_job)
            session.commit()
            job_id = new_job.id
            
        # 2. Write content to ephemeral storage (Claim-Check pattern)
        ephemeral_path = os.path.join(EPHEMERAL_DIR, f"job_{job_id}_payload.txt")
        with open(ephemeral_path, "w", encoding="utf-8") as f:
            f.write(request.content)
            
        payload_uri = f"file://{os.path.abspath(ephemeral_path)}"
        
        # 3. Publish to correct queue for LLM Worker
        msg = DocumentMetaData(job_id=job_id, filepath=f"api_ingest_{request.document_id}", payload_uri=payload_uri)
        
        message = aio_pika.Message(
            body=msg.model_dump_json().encode('utf-8'),
            delivery_mode=aio_pika.DeliveryMode.PERSISTENT,
            message_id=request.document_id,
            content_type="application/json"
        )
        
        # Send to queue
        await channel.default_exchange.publish(
            message,
            routing_key=QUEUE_NAME
        )
        # Note: We reuse the cached robust connection pool's channel, so we do not close the entire channel here if connection is shared. 
        # But if get_rabbitmq_channel creates a new channel for us, we could close it. We leave it open to avoid thrashing.
        
        logger.info(f"Successfully queued document {request.document_id}")
        return DocumentIngestionResponse(
            status="accepted",
            document_id=request.document_id,
            message="Document accepted and queued for processing"
        )
        
    except Exception as e:
        logger.error(f"Error queueing document {request.document_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error while queueing document"
        )
