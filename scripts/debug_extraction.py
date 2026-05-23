from __future__ import annotations

import json
import os

from fhirbridge.core.config import get_settings
from fhirbridge.core.database import Job, get_session_factory, get_sync_engine, verify_runtime_schema


def debug_extraction(pat_id: str = "PAT_2002_1114") -> None:
    engine = get_sync_engine(database_url=get_settings().require_database_url())
    try:
        verify_runtime_schema(engine)
        session_factory = get_session_factory(engine)
        with session_factory() as session:
            jobs = session.query(Job).filter(Job.filepath.contains(pat_id)).all()

            print(f"--- Debugging Extraction for {pat_id} ---")
            for job in jobs:
                print(f"\nFile: {os.path.basename(job.filepath)}")
                print(f"Status: {job.status}")
                if job.ocr_text:
                    print(f"OCR Snippet (100 chars): {job.ocr_text[:100]}...")
                else:
                    print("OCR Text: [EMPTY]")

                if not job.fhir_json:
                    print("FHIR JSON: [EMPTY]")
                    continue

                fhir = json.loads(job.fhir_json)
                patient = fhir.get("Patient", {})
                name = patient.get("name", [{}])[0].get("family", "Unknown")
                birth_date = patient.get("birthDate", "Unknown")
                encounter = fhir.get("Encounter", {})
                case_id = encounter.get("identifier", [{}])[0].get("value", "Unknown")
                diagnoses = encounter.get("diagnosis", [])
                print(
                    "Extracted: Name=%s, BD=%s, Fall=%s, Diags=%s"
                    % (name, birth_date, case_id, len(diagnoses))
                )
    finally:
        engine.dispose()


if __name__ == "__main__":
    debug_extraction()
