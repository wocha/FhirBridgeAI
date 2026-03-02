"""
KDL Discharge Summary Generator (Tier 5 Implementation).

Uses local LLM integration to generate highly realistic, structured
Arztbriefe (DIN 5008). Enforces strict typing and explicit error boundaries
via the canonical LlmRetryClient.
"""

import datetime
import logging
import os
import sys
from pathlib import Path

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

class DischargeSummary(KdlDocumentBase):
    """Structured representation of KDL AD010103 (Entlassungsbericht)."""
    hauptdiagnose: str = Field(..., description="Primary diagnosis including ICD-10.")
    nebendiagnosen: list[str] = Field(default_factory=list, description="Secondary diagnoses.")
    anamnese: str = Field(..., description="Admission context and history.")
    therapie_und_verlauf: str = Field(..., description="Clinical narrative of the hospital stay.")
    epikrise: str = Field(..., description="Summary and recommendations for follow-up.")
    medikation_entlassung: str = Field(..., description="Discharge medication table or list.")

# --- Generator Function -------------------------------------------------------

def _build_patient_context(patient) -> str:
    """Helper to convert PatientState to a context string for the LLM."""
    if hasattr(patient, 'identity'):
        name = patient.identity.name
        birth_date = patient.identity.birth_date.strftime("%d.%m.%Y")
        diagnoses = ", ".join(patient.active_diagnoses) if hasattr(patient, 'active_diagnoses') and patient.active_diagnoses else "Keine"
        return f"Patient: {name}\nGeburtsdatum: {birth_date}\nAktuelle Diagnosen zur Aufnahme: {diagnoses}"
    return str(patient)


def delegate_discharge_summary(
    patient,
    hauptdiagnose: str,
    target_date: datetime.date,
    fall_id: str,
    ambulant: bool = False
) -> DischargeSummary:
    """Generates a highly realistic Discharge Summary using Mistral."""
    doc_type_name = "Ambulanzbrief" if ambulant else "Entlassungsbericht"
    logger.info(f"Delegating {doc_type_name} generation for {getattr(patient.identity, 'name', 'Unknown') if hasattr(patient, 'identity') else 'Unknown'}...")

    # We allow slightly higher temperature for creative text writing,
    # but rely on Pydantic to keep the structure bounded.
    config = LlmConfig(temperature=0.5)
    client = LlmRetryClient(config=config)

    system_context = (
        "Du bist ein erfahrener Stationsarzt in einer großen deutschen Klinik. "
        "Schreibe einen professionellen, realistischen Arztbrief nach DIN 5008 Vorgaben. "
        "Nutze exakte medizinische Terminologie und einen kollegialen Tonfall an die Weiterbehandler."
    )

    # Load the prompt template created in tier-4
    template_path = Path(__file__).parent.parent / "templates" / "discharge_summary_prompt.txt"
    if template_path.exists():
        prompt_template = template_path.read_text(encoding="utf-8")
        prompt = prompt_template.format(
            diagnose=hauptdiagnose,
            patient_context=_build_patient_context(patient)
        )
    else:
        # Fallback if file missing
        prompt = (
            f"Schreibe einen {doc_type_name} für Hauptdiagnose: {hauptdiagnose}.\n\n"
            f"{_build_patient_context(patient)}\n\n"
            "Fülle alle Abschnitte detailliert aus."
        )

    # Model for the LLM extraction payload
    class _GenDischargeContent(BaseModel):
        hauptdiagnose: str
        nebendiagnosen: list[str]
        anamnese: str
        therapie_und_verlauf: str
        epikrise: str
        medikation_entlassung: str

    try:
        content = client.generate_structured(
            prompt=prompt,
            schema=_GenDischargeContent,
            system_context=system_context
        )

        kdl_code = "AD010111" if ambulant else "AD010103"

        return DischargeSummary(
            kdl_code=kdl_code,
            kdl_name=doc_type_name,
            patient_id=getattr(patient.identity, 'base_patient_id', 'UNKNOWN') if hasattr(patient, 'identity') else 'UNKNOWN',
            patient_name=getattr(patient.identity, 'name', 'UNKNOWN') if hasattr(patient, 'identity') else 'UNKNOWN',
            fall_id=fall_id,
            document_date=target_date.strftime("%d.%m.%Y"),
            **content.model_dump()
        )
    except Exception as e:
        logger.error(f"Failed to generate DischargeSummary: {e}")
        raise


if __name__ == "__main__":
    try:
        from patient_state import PatientIdentity, PatientState  # type: ignore
    except ImportError:
        print("patient_state not found, skipping self-test.")
        sys.exit(0)

    fake_patient = PatientState(
        identity=PatientIdentity(
            name="Heinz Müller",
            birth_date=datetime.date(1955, 3, 22),
            gender="m",
            base_patient_id="P55555"
        ),
        active_diagnoses=["Exazerbierte COPD", "Arterielle Hypertonie"],
        active_medications=[],
        timeline=[]
    )

    print("Generating Discharge Summary...")
    brief = delegate_discharge_summary(
        patient=fake_patient,
        hauptdiagnose="Infektexazerbierte COPD GOLD III",
        target_date=datetime.date(2026, 2, 28),
        fall_id="FALL8888"
    )
    print(brief.model_dump_json(indent=2))
