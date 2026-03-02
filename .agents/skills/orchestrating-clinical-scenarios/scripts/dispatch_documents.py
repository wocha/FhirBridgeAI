"""
Document Dispatcher for Clinical Scenarios (Tier 6).
Takes a generated mock PatientState, generates multiple KDL documents,
renders them as PDFs, uploads them to MinIO (S3 Claim-Check Pattern),
writes a record to PostgreSQL, and directly publishes the S3 Object Key
(S-Token) asynchronously into the RabbitMQ TOPIC exchange 
(`fhir_ingestion`) for stress testing.
"""
import argparse
import asyncio
import json
import logging
import os
import random
import sys
import uuid
from datetime import UTC, date, datetime
from pathlib import Path

import aio_pika
import aioboto3
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# --- Path Injection for Antigravity Cross-Skill Imports ---
BASE_DIR = Path(__file__).resolve().parent.parent.parent.parent.parent
sys.path.insert(0, str(BASE_DIR / "src"))

SKILLS_DIR = BASE_DIR / ".agents" / "skills"
sys.path.append(str(SKILLS_DIR / "integrating-local-llms" / "scripts"))
sys.path.append(str(SKILLS_DIR / "orchestrating-clinical-scenarios" / "scripts"))
sys.path.append(str(SKILLS_DIR / "building-autonomous-dispatchers" / "scripts"))
sys.path.append(str(SKILLS_DIR / "generating-kdl-clinical-findings" / "scripts"))
sys.path.append(str(SKILLS_DIR / "generating-kdl-nursing-ward-docs" / "scripts"))
sys.path.append(str(SKILLS_DIR / "generating-kdl-discharge-summaries" / "scripts"))

# Optional imports
try:
    from fhirbridge.core.pdf_engine import MedicalPdfEngine
except ImportError:
    class MedicalPdfEngine:
        def render_clean_pdf(self, doc_obj, output_path, **kwargs):
            Path(output_path).write_text(doc_obj.model_dump_json(indent=2), encoding="utf-8")
        def degrade_pdf_to_scan(self, clean_pdf, dirty_pdf, remove_clean=True):
            content = Path(clean_pdf).read_text(encoding="utf-8")
            Path(dirty_pdf).write_text(content + "\n[DEGRADED SCAN MOCK]\n", encoding="utf-8")
            if remove_clean:
                Path(clean_pdf).unlink()

# DB Models
from fhirbridge.models.patient_record import PatientLongitudinalRecordDB, Base

# KDL Generators
from generate_discharge_summary import delegate_discharge_summary
from generate_findings import delegate_imaging_report, delegate_surgery_report
from simulate_nursing import generate_daily_nursing_log

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)

# Config
BASE_OUT_DIR = BASE_DIR / "data" / "inbound"
RABBITMQ_URL = os.getenv("RABBITMQ_URL", "amqp://guest:guest@localhost:5672/")

# Database Setup
DATABASE_URL = os.getenv("DATABASE_URL", f"sqlite:///{BASE_DIR}/data/dispatcher.db")
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Ensure tables exist
Base.metadata.create_all(bind=engine)

# MinIO / S3 Setup
S3_ENDPOINT_URL = os.getenv("S3_ENDPOINT_URL", "http://localhost:9000")
S3_ACCESS_KEY = os.getenv("S3_ACCESS_KEY", "minioadmin")
S3_SECRET_KEY = os.getenv("S3_SECRET_KEY", "minioadmin")
S3_BUCKET = "synthetic-archive"


# --- Mock Patient Classes ---
class MockIdentity:
    def __init__(self, name, birth_date, gender, base_patient_id):
        self.name = name
        self.birth_date = birth_date
        self.gender = gender
        self.base_patient_id = base_patient_id

class MockPatient:
    def __init__(self, identity, active_diagnoses, active_medications=[]):
        self.identity = identity
        self.active_diagnoses = active_diagnoses
        self.active_medications = active_medications

def generate_synthetic_patients(count: int) -> list:
    patients = []
    first_names = ["Lukas", "Anna", "Maximilian", "Sophie", "Johann", "Maria", "Felix", "Klara"]
    last_names = ["Müller", "Schmidt", "Schneider", "Fischer", "Weber", "Meyer", "Wagner", "Becker"]
    diagnoses_sets = [
        ["Akute Appendizitis", "Arterielle Hypertonie"],
        ["Schenkelhalsfraktur rechts", "Osteoporose"],
        ["Cholezystitis", "Diabetes Mellitus Typ 2"],
        ["Pneumonie", "COPD GOLD II"],
        ["Koxarthrose links", "Adipositas"]
    ]

    for _ in range(count):
        fname = random.choice(first_names)
        lname = random.choice(last_names)
        dob = date(random.randint(1940, 1990), random.randint(1, 12), random.randint(1, 28))
        gender = "m" if fname in ["Lukas", "Maximilian", "Johann", "Felix"] else "w"
        pid = f"PAT-{random.randint(10000, 99999)}"
        diag = random.choice(diagnoses_sets)

        identity = MockIdentity(f"{fname} {lname}", dob, gender, pid)
        patients.append(MockPatient(identity, diag))
    return patients


def _save_to_db(patient_id: str, encounter_id: str, document_id: str, document_type: str, presigned_url: str):
    """Synchronous DB insert executed in thread."""
    session = SessionLocal()
    try:
        record = PatientLongitudinalRecordDB(
            patient_id=patient_id,
            encounter_id=encounter_id,
            document_id=document_id,
            document_type=document_type,
            presigned_url=presigned_url,
            created_at=datetime.now(UTC)
        )
        session.add(record)
        session.commit()
    except Exception as e:
        session.rollback()
        logger.error(f"DB Error while saving record {document_id}: {e}")
        raise
    finally:
        session.close()


async def publish_kdl_to_rabbitmq(
    channel: aio_pika.abc.AbstractChannel, 
    exchange: aio_pika.abc.AbstractExchange, 
    file_path: str, 
    patient_id: str,
    fall_id: str,
    op_type: str,
    chaos_dlq_rate: float
) -> bool:
    """
    Implements Claim-Check Pattern:
    1. Uploads PDF to S3/MinIO bucket
    2. Generates short-lived presigned URL
    3. Saves reference to DB
    4. Publishes small JSON envelope to RabbitMQ TOPIC exchange
    """
    
    doc_uuid = str(uuid.uuid4())
    s3_key = f"{doc_uuid}.pdf"

    # 1. & 2. S3 Upload & Presigned URL via aioboto3
    session = aioboto3.Session()
    try:
        async with session.client("s3", 
                                  endpoint_url=S3_ENDPOINT_URL, 
                                  aws_access_key_id=S3_ACCESS_KEY, 
                                  aws_secret_access_key=S3_SECRET_KEY) as s3_client:
            
            # Ensure bucket exists (optional, could be done once, but done here for safety in dev envs)
            # In production, the bucket would ideally already exist
            try:
                await s3_client.head_bucket(Bucket=S3_BUCKET)
            except Exception:
                await s3_client.create_bucket(Bucket=S3_BUCKET)

            # Upload the local PDF file directly
            await s3_client.upload_file(file_path, S3_BUCKET, s3_key)
            logger.info(f"Successfully uploaded {s3_key} to S3 bucket {S3_BUCKET}")
            
            # Generate 3600s presigned URL
            presigned_url = await s3_client.generate_presigned_url(
                'get_object',
                Params={'Bucket': S3_BUCKET, 'Key': s3_key},
                ExpiresIn=3600
            )

    except Exception as e:
        logger.error(f"Failed S3 Operation for {file_path}: {e}")
        return False

    # 3. Save to Database
    document_type_mapping = {
        "discharge": "discharge_summary",
        "imaging": "imaging_report",
        "surgery": "surgery_report",
        "nursing": "nursing_log"
    }
    document_type = document_type_mapping.get(op_type, "unknown_kdl")
    
    try:
        await asyncio.to_thread(_save_to_db, patient_id, fall_id, s3_key, document_type, presigned_url)
        logger.info(f"Saved DB Record for S3 Token: {s3_key}")
    except Exception as e:
        logger.error(f"Aborting publish due to DB error: {e}")
        return False

    # 4. RabbitMQ Claim-Check Envelope Publish
    routing_key = "document.ingested.pdf"
    
    # KDL Code mapping logic
    kdl_code_map = {
        "imaging": "LB120101",
        "surgery": "PT140302",
        "nursing": "VL160105", 
        "discharge": "AD010101"
    }
    kdl_code = kdl_code_map.get(op_type, "UNKNOWN")

    # ==========================================
    # CHAOS ENGINEERING - DLQ STRESS TESTING
    # ==========================================
    if chaos_dlq_rate > 0 and random.random() < chaos_dlq_rate:
        logger.warning(f"[CHAOS] Triggered chaos injection for {s3_key}!")
        routing_key = "document.ingested.chaos"
        if random.random() < 0.5:
            # Inject garbage token
            s3_key = "CHAOS_MISSING_KEY.pdf"
            logger.warning("-> Mutated payload envelope S3 key to force a download error on worker")
        else:
            logger.warning("-> Using chaos routing key to simulate DLQ fail-routing")

    # JSON Metadata Envelope (Claim-Check Pattern)
    message_payload = {
        "document_id": doc_uuid,
        "patient_id": patient_id,
        "fall_id": fall_id,
        "document_type": document_type,
        "kdl_code": kdl_code,
        "file_path": file_path,
        "document_s3_key": s3_key,
        "presigned_url": presigned_url
    }

    # Delivery Mode 2: Persistent 
    message = aio_pika.Message(
        body=json.dumps(message_payload).encode("utf-8"),
        delivery_mode=aio_pika.DeliveryMode.PERSISTENT,
        message_id=message_payload["document_id"],
        content_type="application/json",
        headers={"source_file": file_path, "op_type": op_type}
    )

    try:
        # Pika Publisher Confirms enabled: await confirm before succeeding
        await exchange.publish(message, routing_key=routing_key)
        logger.info(f"Published Claim-Check Envelope and ACK received for: {s3_key} (Routing Key: {routing_key})")
        return True
    except Exception as e:
        logger.error(f"Failed to receive ACK from broker for {s3_key}: {e}")
        return False


async def async_main():
    parser = argparse.ArgumentParser(description="Synthetic Patient Orchestrator - Async Claim-Check Firehose")
    parser.add_argument("--patients", type=int, default=1, help="Number of synthetic patients to generate (limit 5)")
    parser.add_argument("--chaos-dlq-rate", type=float, default=0.0, help="Probability (0.0 to 1.0) to intentionally corrupt payloads for DLQ testing")
    args = parser.parse_args()

    patient_count = min(args.patients, 5) # Safety limit
    chaos_rate = max(0.0, min(1.0, args.chaos_dlq_rate))

    # 1. Connect to RabbitMQ using aio_pika
    logger.info(f"Connecting to RabbitMQ at {RABBITMQ_URL}...")
    try:
        connection = await aio_pika.connect_robust(RABBITMQ_URL)
    except Exception as e:
        logger.error(f"Could not connect to RabbitMQ broker: {e}")
        sys.exit(1)

    # 2. Open Channel with Publisher Confirms Required (Zero Data Loss)
    channel = await connection.channel(publisher_confirms=True)
    
    # 3. Declare target TOPIC Exchange (Principal Architect Rule #1)
    exchange_name = "fhir_ingestion"
    exchange = await channel.declare_exchange(
        name=exchange_name, 
        type=aio_pika.ExchangeType.TOPIC, 
        durable=True
    )
    logger.info(f"Exchange '{exchange_name}' is ready (Type: TOPIC). Publisher Confirms ENABLED.")

    pdf_engine = MedicalPdfEngine()
    patients = generate_synthetic_patients(patient_count)

    logger.info(f"Starting async claim-check orchestration loop for {patient_count} synthetic patients...")

    success_count = 0
    failure_count = 0

    for pt in patients:
        fall_id = f"FALL-{random.randint(100000, 999999)}"
        target_date = date.today()
        patient_id = pt.identity.base_patient_id
        patient_dir = BASE_OUT_DIR / patient_id / fall_id
        patient_dir.mkdir(parents=True, exist_ok=True)

        logger.info(f"--- Processing Case {fall_id} for Patient {pt.identity.name} ---")
        primary_diag = pt.active_diagnoses[0]

        # Define the medical timeline for this patient
        operations = [
            ("imaging", "Abdomensonographie/Röntgen", "Abklärung unklarer Befund"),
            ("surgery", "Chirurgische Intervention gem. Leitlinie", primary_diag),
            ("nursing", None, None),
            ("discharge", None, primary_diag)
        ]

        for op_type, proc, ind in operations:
            output_filename = f"KDL_{op_type}_{fall_id}.pdf"
            output_pdf_path = patient_dir / output_filename
            temp_clean_pdf = patient_dir / f"clean_{output_filename}"

            logger.info(f"Generating {op_type} report for {fall_id}...")
            try:
                # 1. Generate Structured Document Content via LLM
                doc_obj = None
                if op_type == "imaging":
                    doc_obj = delegate_imaging_report(pt, ind, proc, target_date, fall_id)
                elif op_type == "surgery":
                    doc_obj = delegate_surgery_report(pt, ind, proc, target_date, fall_id)
                elif op_type == "nursing":
                    doc_obj = generate_daily_nursing_log(pt, target_date, fall_id)
                elif op_type == "discharge":
                    doc_obj = delegate_discharge_summary(pt, ind, target_date, fall_id, ambulant=False)

                if not doc_obj:
                    continue

                # 2. Render to Clean PDF
                pdf_engine.render_clean_pdf(
                    doc_obj=doc_obj,
                    output_path=str(temp_clean_pdf),
                    synthea_hospital_name="Waldklinikum Antigravity",
                    include_qr=True
                )

                # 3. Degrade PDF to Scan
                pdf_engine.degrade_pdf_to_scan(
                    clean_pdf=str(temp_clean_pdf),
                    dirty_pdf=str(output_pdf_path),
                    remove_clean=True
                )

                # 4. Push to MinIO, DB, and RabbitMQ Claim-Check 
                success = await publish_kdl_to_rabbitmq(
                    channel=channel,
                    exchange=exchange,
                    file_path=str(output_pdf_path),
                    patient_id=patient_id,
                    fall_id=fall_id,
                    op_type=op_type,
                    chaos_dlq_rate=chaos_rate
                )

                if success:
                    success_count += 1
                else:
                    failure_count += 1

            except Exception as e:
                logger.error(f"Failed to process {op_type} for {pt.identity.name}: {e}")
                failure_count += 1

    # Final Summary
    logger.info("=========================================================")
    logger.info(f"--- Async Claim-Check Firehose Complete ---")
    logger.info(f"Messages Successfully ACK'd (Zero Data Loss): {success_count}")
    logger.info(f"Messages Failed or Denied: {failure_count}")
    logger.info("=========================================================")
    
    # Close connection gracefully upon full success
    await connection.close()

def main():
    asyncio.run(async_main())

if __name__ == "__main__":
    main()
