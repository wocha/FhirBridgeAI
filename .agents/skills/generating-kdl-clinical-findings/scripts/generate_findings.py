"""
KDL Clinical Findings Generator (Tier 5 Implementation).

Uses local LLM integration to generate highly realistic, structured
clinical findings for Surgery and Imaging reports. Enforces strict typing
and explicit error boundaries via the canonical LlmRetryClient.
"""

import datetime
import logging
import os
import sys

from pydantic import BaseModel, Field

# Setup basic logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Ensure canonical LlmRetryClient is importable
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "integrating-local-llms", "scripts")))
try:
    from llm_retry_client import LlmConfig, LlmRetryClient, LlmValidationError
except ImportError as e:
    logging.error(f"Failed to import LlmRetryClient: {e}")
    sys.exit(1)

# Ensure patient_state is importable
try:
    sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "orchestrating-clinical-scenarios", "scripts")))
    from patient_state import PatientState
except ImportError:
    pass

# --- Pydantic Definitions -----------------------------------------------------

class KdlDocumentBase(BaseModel):
    """Base class for all specific KDL documents generated."""
    kdl_code: str = Field(..., description="The KDL document code.")
    kdl_name: str = Field(..., description="The human readable document type name.")
    patient_id: str = Field(..., description="The patient identifier.")
    patient_name: str = Field(..., description="The patient name.")
    fall_id: str = Field(..., description="The Encounter/Fall identifier.")
    document_date: str = Field(..., description="The date the report was finalized as string.")

class SurgeryReport(KdlDocumentBase):
    """Structured representation of KDL OP150103 (Operativer Bericht)."""
    indication: str = Field(..., description="Medical reason for the surgery.")
    surgeon_name: str = Field(..., description="Name of the main surgeon.")
    procedure_name: str = Field(..., description="Primary surgical procedure performed (e.g., Appendektomie).")
    findings_macroscopic: str = Field(..., description="What was observed during exploration.")
    procedure_steps: list[str] = Field(..., description="Chronological list of steps taken during surgery.")
    complications: str | None = Field(None, description="Any complications during the procedure. 'Keine' if none.")

class ImagingReport(KdlDocumentBase):
    """Structured representation of KDL DG02* (Radiologischer Befund)."""
    modality: str = Field(..., description="Imaging modality (e.g., CT, MRT, Röntgen).")
    indication: str = Field(..., description="Clinical question leading to this scan.")
    technique: str = Field(..., description="Details of the scan (e.g., 'mit Kontrastmittel i.v.').")
    findings: str = Field(..., description="Detailed description of the imaging findings.")
    conclusion: str = Field(..., description="Summary of the radiological diagnosis.")
    recommendation: str | None = Field(None, description="Further actions recommended by the radiologist.")


def _build_patient_context(patient) -> str:
    """Helper to convert PatientState to a context string for the LLM."""
    if hasattr(patient, 'identity'):
        name = patient.identity.name
        birth_date = patient.identity.birth_date.strftime("%d.%m.%Y")
        gender = patient.identity.gender
        diagnoses = ", ".join(patient.active_diagnoses) if patient.active_diagnoses else "Keine"
        return f"Patient: {name}\nGeburtsdatum: {birth_date}\nGeschlecht: {gender}\nAktuelle Diagnosen: {diagnoses}"
    return str(patient)

# --- LLM Delegators -----------------------------------------------------------

def delegate_surgery_report(
    patient,
    indication: str,
    procedure: str,
    target_date: datetime.date,
    fall_id: str
) -> SurgeryReport:
    """Generates a highly realistic surgical report using Mistral."""
    logger.info(f"Delegating SurgeryReport generation for {procedure}...")

    config = LlmConfig(temperature=0.3)
    client = LlmRetryClient(config=config)

    system_context = (
        "Du bist ein erfahrener Oberarzt in einer deutschen Klinik. "
        "Erstelle einen sehr realistischen, detaillierten Operationsbericht "
        "mit korrekter medizinischer Fachsprache (z.B. Exploration, Resektion, Ligatur). "
        f"{_build_patient_context(patient)}"
    )

    prompt = (
        f"Erstelle einen fiktiven OP-Bericht am {target_date.strftime('%d.%m.%Y')}.\n"
        f"Eingriff: {procedure}\n"
        f"Indikation: {indication}\n\n"
        "Fülle alle Felder des JSON-Schemas mit realistischen, zusammenhängenden Textbausteinen aus."
    )

    # We define a helper schema for generation to let LLM only focus on content,
    # and fill the base deterministic fields ourselves.
    class _GenSurgeryContent(BaseModel):
        indication: str
        surgeon_name: str
        procedure_name: str
        findings_macroscopic: str
        procedure_steps: list[str]
        complications: str | None

    try:
        content = client.generate_structured(
            prompt=prompt,
            schema=_GenSurgeryContent,
            system_context=system_context
        )

        # Merge with deterministic data
        return SurgeryReport(
            kdl_code="OP150103",
            kdl_name="OP-Bericht",
            patient_id=getattr(patient.identity, 'base_patient_id', 'UNKNOWN'),
            patient_name=getattr(patient.identity, 'name', 'UNKNOWN'),
            fall_id=fall_id,
            document_date=target_date.strftime("%d.%m.%Y"),
            **content.model_dump()
        )
    except Exception as e:
        logger.error(f"Failed to generate SurgeryReport: {e}")
        raise


def delegate_imaging_report(
    patient,
    indication: str,
    modality: str,
    target_date: datetime.date,
    fall_id: str
) -> ImagingReport:
    """Generates a realistic radiology report using Mistral."""
    logger.info(f"Delegating ImagingReport generation for {modality}...")

    config = LlmConfig(temperature=0.3)
    client = LlmRetryClient(config=config)

    system_context = (
        "Du bist ein erfahrener Radiologe in einer deutschen Klinik. "
        "Erstelle einen detaillierten, realistischen radiologischen Befund "
        "mit typischer Terminologie (z.B. Verschattung, Kontrastmittelanreicherung, unauffällig). "
        f"{_build_patient_context(patient)}"
    )

    prompt = (
        f"Erstelle einen fiktiven radiologischen Befund am {target_date.strftime('%d.%m.%Y')}.\n"
        f"Modalität: {modality}\n"
        f"Klinische Fragestellung/Indikation: {indication}\n\n"
        "Fülle alle Felder des JSON-Schemas mit realistischen, detaillierten Befundtexten aus."
    )

    class _GenImagingContent(BaseModel):
        modality: str
        indication: str
        technique: str
        findings: str
        conclusion: str
        recommendation: str | None

    try:
        content = client.generate_structured(
            prompt=prompt,
            schema=_GenImagingContent,
            system_context=system_context
        )

        kdl_code = "DG020110" if "Röntgen" in modality else "DG020103" if "CT" in modality else "DG020000"
        kdl_name = "Röntgenbefund" if "Röntgen" in modality else "CT-Befund" if "CT" in modality else "Bildgebung"

        return ImagingReport(
            kdl_code=kdl_code,
            kdl_name=kdl_name,
            patient_id=getattr(patient.identity, 'base_patient_id', 'UNKNOWN'),
            patient_name=getattr(patient.identity, 'name', 'UNKNOWN'),
            fall_id=fall_id,
            document_date=target_date.strftime("%d.%m.%Y"),
            **content.model_dump()
        )
    except Exception as e:
        logger.error(f"Failed to generate ImagingReport: {e}")
        raise


if __name__ == "__main__":
    try:
        from patient_state import PatientIdentity, PatientState
    except ImportError:
        print("patient_state not found, skipping self-test.")
        sys.exit(0)

    fake_patient = PatientState(
        identity=PatientIdentity(
            name="Max Mustermann",
            birth_date=datetime.date(1980, 5, 15),
            gender="m",
            base_patient_id="P12345"
        ),
        active_diagnoses=["Akute Appendizitis (K35.8)"],
        active_medications=[],
        timeline=[]
    )

    print("Generating Imaging Report...")
    imaging = delegate_imaging_report(
        patient=fake_patient,
        indication="Verdacht auf akute Appendizitis, Druckschmerz rechter Unterbauch",
        modality="Abdomensonographie",
        target_date=datetime.date(2026, 2, 28),
        fall_id="F98765"
    )
    print(imaging.model_dump_json(indent=2))
