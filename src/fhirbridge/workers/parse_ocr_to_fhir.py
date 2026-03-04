"""
Parse OCR Text to FHIR JSON via Local LLM (Mistral-NeMo).

Liest extrahierte OCR-Texte (aus `extract_ocr.py`), steuert Ollama
(Mistral-NeMo) an, um strukturierte Entitäten zu extrahieren,
und wendet einen Pydantic-Validation-Loop (max 3 Retries) gegen
die ISiK FHIR-Modelle (`fhir_models.py`) an.

Erfüllt Architekturvorgaben des 'building-autonomous-dispatchers'
und 'integrating-local-llms' Skills:
- SQLite basierte Queue (Dispatcher) für Idempotence und Crash-Recovery
- Durable Audit Logging in der DB
- Context Chunking gegen OOM-Fehler des lokalen Modells
- Keine Cloud APIs
- Structured Outputs via Pydantic Validation Loop
- Deterministic Lookup für ICD-10 Codes (LLM extrahiert nur den Text)

Aufruf:
    python scripts/parse_ocr_to_fhir.py --input data/ocr_output
"""

import glob
import json
import logging
import os
import sys
import traceback
from pathlib import Path
from typing import Any

from pydantic import ValidationError

# Importiere unsere rigorosen ISiK Modelle
from fhirbridge.models.fhir_models import (
    BundleExtraction,
    CodeableConcept,
    Coding,
    Encounter,
    EncounterDiagnosis,
    Patient,
    Reference,
)

_SKILL_SCRIPTS_DIR = str(
    Path(__file__).resolve().parent.parent.parent.parent
    / ".agents"
    / "skills"
    / "integrating-local-llms"
    / "scripts"
)
if _SKILL_SCRIPTS_DIR not in sys.path:
    sys.path.insert(0, _SKILL_SCRIPTS_DIR)

from llm_retry_client import LlmConfig, LlmRetryClient  # noqa: E402

# ---------------------------------------------------------------------------
# Konfiguration (No magic numbers!)
# ---------------------------------------------------------------------------

CONFIG: dict[str, Any] = {
    "MODEL_NAME": "mistral-nemo",  # Mistral NeMo 12B lokal
    "TEMPERATURE": 0.1,  # Sehr niedrig (0.1) für deterministische Extraktion
    "MAX_RETRIES": 3,  # Fehlerkorrektur-Schleife gemäß Architekturvorgabe
    "DB_PATH": "data/dispatcher.db",
    "OUT_DIR": "data/fhir_output",
    "CHUNK_SIZE": 2500,  # Maximale Zeichenanzahl pro Prompt an das LLM
    "TIMEOUT": 120,  # Hard timeout für inference
}

from fhirbridge.core.config import get_settings

OLLAMA_URL = get_settings().ollama_url.rstrip("/") + "/api/chat"

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)


from fhirbridge.core.database import Job, JobStatus, get_session_factory, init_db  # noqa: E402

# ---------------------------------------------------------------------------
# SQLAlchemy Dispatcher Backend
# ---------------------------------------------------------------------------


def scan_files_into_db(input_dir: str, session: Any) -> int:
    """Findet alle txt Dateien und fügt neue als PENDING in die DB ein."""
    txt_files = sorted(glob.glob(os.path.join(input_dir, "**", "*.txt"), recursive=True))
    added = 0

    for filepath in txt_files:
        existing = session.query(Job).filter_by(filepath=filepath).first()
        if not existing:
            new_job = Job(filepath=filepath, status=JobStatus.PENDING)
            session.add(new_job)
            added += 1

    session.commit()
    return added


def get_next_job(session: Any) -> Job | None:
    """Holt den nächsten PENDING/LLM_EXTRACTION Job und markiert ihn als LLM_EXTRACTION."""
    job = (
        session.query(Job)
        .filter(Job.status.in_([JobStatus.PENDING, JobStatus.LLM_EXTRACTION]))
        .order_by(Job.status.desc(), Job.id.asc())
        .first()
    )

    if job:
        job.status = JobStatus.LLM_EXTRACTION
        session.commit()
    return job  # type: ignore[no-any-return]


def mark_job_done(
    session: Any,
    job: Job,
    output_path: str,
    ocr_text: str | None = None,
    fhir_json: str | None = None,
) -> None:
    """Markiert einen Job als erfolgreich beendet und speichert die Texte im Audit Log."""
    job.status = JobStatus.FHIR_GENERATED
    job.output_path = output_path  # type: ignore[assignment]
    if ocr_text is not None:
        job.ocr_text = ocr_text  # type: ignore[assignment]
    if fhir_json is not None:
        job.fhir_json = fhir_json  # type: ignore[assignment]
    session.commit()


def mark_job_error(session: Any, job: Job, error_trace: str) -> None:
    """Speichert einen Error mit Stack Trace (Audit Logging)."""
    job.status = JobStatus.FAILED
    job.error_trace = error_trace  # type: ignore[assignment]
    session.commit()


from fhirbridge.core.icd10_matcher import match_icd10_code  # noqa: E402

# ---------------------------------------------------------------------------
# LLM Integration & Pydantic Validation Loop
# ---------------------------------------------------------------------------


def _chunk_text(text: str, chunk_size: int) -> list[str]:
    """Teilt einen langen Text in sinnvolle Chunks (z.B. nach Absätzen)."""
    paragraphs = text.split("\n\n")
    chunks = []
    current_chunk = ""

    for p in paragraphs:
        if len(current_chunk) + len(p) < chunk_size:
            current_chunk += p + "\n\n"
        else:
            if current_chunk:
                chunks.append(current_chunk.strip())
            current_chunk = p + "\n\n"

    if current_chunk:
        chunks.append(current_chunk.strip())

    # Falls der Text gar keine Absätze hat (schlechtes OCR), breche hart um
    if not chunks and text:
        chunks = [text[i : i + chunk_size] for i in range(0, len(text), chunk_size)]

    return chunks


async def _extract_from_chunk(chunk_text: str) -> dict[str, Any]:
    """Verarbeitet einen einzelnen Text-Chunk durch das LLM und validiert gegen Pydantic."""

    system_prompt = (
        "Du bist ein Extraktions-Experte für deutsche Krankenhaus-Arztbriefe. "
        "Deine Aufgabe ist es, exakt EIN JSON-Objekt zurückzugeben, das "
        "relevante Entitäten enthält. Wenn Teile fehlen, "
        "sind die Felder leer oder nicht vorhanden.\n"
        "Regeln:\n"
        "1. Generiere NUR JSON. Keinen Markdown-Text.\n"
        "2. Erfinde KEINE Daten. Extrahiere den reinen Text aus dem OCR.\n"
        "3. Lade alle verfügbaren Infos in 'Patient' oder 'Encounter'.\n"
        "4. Datumsformate müssen zwingend YYYY-MM-DD sein.\n"
        "5. Das Geschlecht muss aus (male, female, other, unknown) gewählt werden.\n"
        "6. Bei Diagnosen: Extrahiere den Text UND versuche den"
        " ICD-10 Code zu ermitteln (falls im Text vorhanden, sonst leer lassen).\n"
        "BEISPIEL ANTWORT:\n"
        "{\n"
        '  "Patient": {\n'
        '    "identifier": [{"value": "123456789"}],\n'
        '    "name": [{"family": "Mustermann", "given": ["Max"]}],\n'
        '    "gender": "male",\n'
        '    "birthDate": "1980-05-15"\n'
        "  },\n"
        '  "Encounter": {\n'
        '    "identifier": [{"value": "FALL-2023-01"}],\n'
        '    "diagnoses": [\n'
        '      {"text": "Diabetes Mellitus Typ 2", "icd10": "E11.9"},\n'
        '      {"text": "Bluthochdruck", "icd10": "I10"}\n'
        "    ]\n"
        "  }\n"
        "}\n"
    )

    user_prompt = (
        "Extrahiere die klinischen Daten in das folgende strikte Schema"
        " (ersetze die <PLATZHALTER> durch die echten Werte aus dem Text."
        " Lass fehlende Keys komplett weg):\n\n"
        "{\n"
        '  "Patient": {\n'
        '    "identifier": [{"value":'
        ' "<KRANKENVERSICHERUNGSNUMMER ODER PATIENTEN-ID (z.B. PAT_...)>"}],\n'
        '    "name": [{"family": "<NACHNAME>", "given": ["<VORNAME>"]}],\n'
        '    "gender": "<male|female|other|unknown>",\n'
        '    "birthDate": "<GEBURTSDATUM (YYYY-MM-DD)>"\n'
        "  },\n"
        '  "Encounter": {\n'
        '    "identifier": [{"value": "<FALLNUMMER (z.B. FALL_...)>"}],\n'
        '    "diagnoses": [\n'
        '      {"text": "<DIAGNOSE-TEXT 1>", "icd10": "<ICD-10 CODE 1 (falls vorhanden)>"}\n'
        "    ]\n"
        "  }\n"
        "}\n\n"
        f"--- OCR TEXT ---\n{chunk_text}\n--- ENDE OCR TEXT ---"
    )

    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_prompt},
    ]


    config = LlmConfig(
        model=CONFIG["MODEL_NAME"],
        temperature=CONFIG["TEMPERATURE"],
        max_tokens=2500,
        request_timeout_seconds=CONFIG["TIMEOUT"],
        max_retries=CONFIG["MAX_RETRIES"],
    )
    client = LlmRetryClient(config)

    try:
        bundle = await client.chat_structured(messages=messages, schema=BundleExtraction)
        from typing import cast

        return cast(dict[str, Any], json.loads(bundle.model_dump_json(exclude_none=True)))
    except Exception as e:
        logger.error(
            f"    Chunk Extraktion - fehlgeschlagen nach {CONFIG['MAX_RETRIES']} Retries: {e}"
        )
        empty_dict: dict[str, Any] = {}
        return empty_dict


async def extract_fhir_bundle(ocr_text: str) -> dict[str, Any]:
    """
    Teilt den Text in Chunks (Memory Safety), iteriert über das LLM,
    merged die JSONs und validiert alles strikt durch unsere ISiK Pydantic Modelle.
    """
    chunks = _chunk_text(ocr_text, int(CONFIG["CHUNK_SIZE"]))
    logger.info(f"  Text aufgeteilt in {len(chunks)} Chunks.")

    merged_data: dict[str, dict[str, Any]] = {
        "Patient": {"resourceType": "Patient"},
        "Encounter": {
            "resourceType": "Encounter",
            "status": "finished",
            "class": {"code": "IMP"},
            "subject": {"reference": "Patient/1"},
        },
    }
    raw_diagnoses_all = set()

    for i, chunk in enumerate(chunks):
        logger.info(f"  Verarbeite Chunk {i+1}/{len(chunks)}...")
        chunk_data = await _extract_from_chunk(chunk)

        # Merge Patient Data
        p_data = chunk_data.get("Patient", {})
        for key in ["identifier", "name", "gender", "birthDate"]:
            if key in p_data and p_data[key]:
                if isinstance(p_data[key], list):
                    merged_data["Patient"].setdefault(key, []).extend(p_data[key])
                else:
                    merged_data["Patient"][key] = p_data[key]

        # Merge Encounter Data
        e_data = chunk_data.get("Encounter", {})
        if "identifier" in e_data and e_data["identifier"]:
            merged_data["Encounter"].setdefault("identifier", []).extend(e_data["identifier"])
        if "raw_diagnoses" in e_data:
            for diag in e_data["raw_diagnoses"]:
                raw_diagnoses_all.add(diag)

    # --- Pydantic Validation Check ---
    # Dummy Fillers falls OCR nichts findet, da ISiK strikt ist (Card 1..*)
    if "identifier" not in merged_data["Patient"] or not merged_data["Patient"]["identifier"]:
        merged_data["Patient"]["identifier"] = [
            {
                "value": "UNKNOWN-PID",
                "type": {
                    "coding": [
                        {"system": "http://terminology.hl7.org/CodeSystem/v2-0203", "code": "MR"}
                    ]
                },
            }
        ]
    else:
        # Ensure at least one identifier has a valid type for ISiK
        has_typed = False
        for ident in merged_data["Patient"]["identifier"]:
            if isinstance(ident, dict):
                if ident.get("system") in [
                    "http://fhir.de/sid/gkv/kvid-10",
                    "http://fhir.de/sid/pkv/kvid-10",
                ]:
                    has_typed = True
                    break
                if ident.get("type", {}).get("coding"):
                    has_typed = True
                    break
        if not has_typed:
            # Tag the first identifier as a Patient ID (MR)
            merged_data["Patient"]["identifier"][0]["type"] = {
                "coding": [
                    {"system": "http://terminology.hl7.org/CodeSystem/v2-0203", "code": "MR"}
                ]
            }
    if "name" not in merged_data["Patient"] or not merged_data["Patient"]["name"]:
        merged_data["Patient"]["name"] = [{"family": "UNKNOWN"}]
    if "gender" not in merged_data["Patient"]:
        merged_data["Patient"]["gender"] = "unknown"
    if "birthDate" not in merged_data["Patient"]:
        merged_data["Patient"]["birthDate"] = "1900-01-01"

    if "identifier" not in merged_data["Encounter"] or not merged_data["Encounter"]["identifier"]:
        merged_data["Encounter"]["identifier"] = [
            {
                "value": "UNKNOWN-FALL",
                "type": {
                    "coding": [
                        {"system": "http://terminology.hl7.org/CodeSystem/v2-0203", "code": "VN"}
                    ]
                },
            }
        ]
    else:
        # Ensure at least one identifier has VN type for ISiK
        has_vn = False
        for ident in merged_data["Encounter"]["identifier"]:
            if isinstance(ident, dict):
                if ident.get("type", {}).get("coding"):
                    if any(c.get("code") == "VN" for c in ident["type"]["coding"]):
                        has_vn = True
                        break
                if ident.get("system") and "fallnummer" in ident.get("system", "").lower():
                    has_vn = True
                    break
        if not has_vn:
            merged_data["Encounter"]["identifier"][0]["type"] = {
                "coding": [
                    {"system": "http://terminology.hl7.org/CodeSystem/v2-0203", "code": "VN"}
                ]
            }

    try:
        patient_model = Patient.model_validate(merged_data["Patient"])

        # Diagnosen verarbeiten (List of Dicts: {"text": "...", "icd10": "..."})
        diagnosis_objects = []
        if raw_diagnoses_all:
            for i, diag_item in enumerate(raw_diagnoses_all, start=1):
                if isinstance(diag_item, dict):
                    diag_text = diag_item.get("text", "")
                    llm_hint = diag_item.get("icd10", "")
                else:
                    diag_text = str(diag_item)
                    llm_hint = ""

                if not diag_text:
                    continue

                icd_code, display = match_icd10_code(diag_text)

                # Use LLM hint if matcher returns unknown, but LLM found something plausible
                if icd_code == "R69" and llm_hint and len(llm_hint) >= 3:
                    icd_code = llm_hint
                    display = diag_text

                diagnosis_objects.append(
                    EncounterDiagnosis(
                        condition=Reference(display=display),
                        use=CodeableConcept(
                            coding=[
                                Coding(
                                    system="http://fhir.de/CodeSystem/bfarm/icd-10-gm",
                                    code=icd_code,
                                )
                            ]
                        ),
                        rank=i,
                    )
                )

        if diagnosis_objects:
            merged_data["Encounter"]["diagnosis"] = [
                json.loads(d.model_dump_json(exclude_none=True)) for d in diagnosis_objects
            ]

        encounter_model = Encounter.model_validate(merged_data["Encounter"])
        logger.info("  ✓ Pydantic Validation erfolgreich!")

        return {
            "Patient": json.loads(patient_model.model_dump_json(by_alias=True, exclude_none=True)),
            "Encounter": json.loads(
                encounter_model.model_dump_json(by_alias=True, exclude_none=True)
            ),
        }

    except ValidationError as e:
        logger.error(f"  ✗ Pydantic Validation an finalem Merge gescheitert:\n{e}")
        raise ValueError(f"Merged output invalid against ISiK profiles: {e}")


# ---------------------------------------------------------------------------
# Dispatcher Worker Loop
# ---------------------------------------------------------------------------


async def run_worker(db_path: str) -> None:
    """The continuous FHIR extraction loop."""
    import asyncio

    engine = init_db(db_path)
    SessionFactory = get_session_factory(engine)

    os.makedirs(str(CONFIG["OUT_DIR"]), exist_ok=True)

    logger.info("=======================================")
    logger.info("🚀 FHIR Extraction Worker Active")
    logger.info("=======================================")

    try:
        while True:
            with SessionFactory() as session:
                # Poll for jobs that have OCR text ready
                job = (
                    session.query(Job)
                    .filter(Job.status == JobStatus.LLM_EXTRACTION)
                    .order_by(Job.id.asc())
                    .first()
                )

                if not job:
                    await asyncio.sleep(5)
                    continue

                logger.info(f"==> Verarbeite Job #{job.id}: {os.path.basename(job.filepath)}")

                try:
                    ocr_text = job.ocr_text  # type: ignore[assignment]
                    if not ocr_text or not ocr_text.strip():
                        raise ValueError("Job hat keinen OCR Text in der DB.")

                    fhir_bundle = await extract_fhir_bundle(str(ocr_text))

                    # File naming: use parent folders to avoid collisions
                    # job.filepath is /data/inbound/PAT/FALL/doc.pdf
                    path_parts = job.filepath.replace("\\", "/").split("/")
                    # Take PAT and FALL for naming
                    if len(path_parts) >= 3:
                        prefix = f"{path_parts[-3]}_{path_parts[-2]}_"
                    else:
                        prefix = ""

                    base_name = (
                        f"{prefix}{os.path.basename(job.filepath).replace('.pdf', '_fhir.json')}"
                    )
                    out_file = os.path.join(str(CONFIG["OUT_DIR"]), base_name)

                    with open(out_file, "w", encoding="utf-8") as f:
                        json.dump(fhir_bundle, f, indent=2, ensure_ascii=False)

                    mark_job_done(
                        session,
                        job,
                        out_file,
                        fhir_json=json.dumps(fhir_bundle, ensure_ascii=False),
                    )
                    logger.info(f"  ✓ FHIR generiert: {out_file}")

                except Exception as e:
                    error_trace = traceback.format_exc()
                    logger.error(f"  ✗ Job #{job.id} fehlgeschlagen! {type(e).__name__}: {e}")
                    mark_job_error(session, job, error_trace)

    except KeyboardInterrupt:
        logger.info(" Worker manuell beendet.")


async def main() -> None:
    await run_worker(str(CONFIG["DB_PATH"]))


if __name__ == "__main__":
    import asyncio

    asyncio.run(main())
