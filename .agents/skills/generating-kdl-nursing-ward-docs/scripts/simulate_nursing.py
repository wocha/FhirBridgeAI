"""
Algorithmic & LLM-Assisted Generation of Nursing Ward Docs.

Creates synthetic daily nursing logs (KDL VL160105 / Pflegeberichte)
leveraging the PatientState and Mistral for varied narrative text.
Enforces strict JSON schema output via the LlmRetryClient.
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

# We also ensure the global Kdl definitions are preserved if needed by the router mapping,
# although we define structured Pydantic locally to dictate the LLM schema.

# --- Pydantic Definitions -----------------------------------------------------

class Vitals(BaseModel):
    blood_pressure: str = Field(..., description="e.g. 120/80 mmHg")
    heart_rate: int = Field(..., description="Beats per minute")
    temperature: float = Field(..., description="Body temperature in Celsius")

class NursingShiftLog(BaseModel):
    timestamp_start: str = Field(..., description="ISO datetime of shift start, e.g. 2026-02-28T06:00:00")
    timestamp_end: str = Field(..., description="ISO datetime of shift end")
    shift_type: str = Field(..., description="Frühschicht, Spätschicht, Nachtschicht")
    vitals_recorded: Vitals = Field(..., description="Recorded vital signs during the shift")
    observations: str = Field(..., description="Narrative observations by the nurse (e.g. pain level, mobility, mood)")
    interventions: list[str] = Field(..., description="Actions performed (e.g. 'Verbandswechsel', 'Waschen im Bett')")
    nurse_name: str = Field(..., description="Realistic fictional name of the nurse")

class NursingWardDoc(BaseModel):
    """Structured representation of KDL VL160105 (Pflegebericht)."""
    kdl_code: str = "VL160105"
    kdl_name: str = "Pflegebericht"
    patient_id: str
    patient_name: str
    fall_id: str
    document_date: str
    shift_logs: list[NursingShiftLog] = Field(..., description="List of shifts recorded on this day.")

# --- Generators ---------------------------------------------------------------

def _build_patient_context(patient) -> str:
    """Helper to convert PatientState to a context string for the LLM."""
    if hasattr(patient, 'identity'):
        name = patient.identity.name
        diagnoses = ", ".join(patient.active_diagnoses) if hasattr(patient, 'active_diagnoses') and patient.active_diagnoses else "Keine"
        return f"Patient: {name}\nAktuelle Diagnosen: {diagnoses}"
    return str(patient)


def generate_daily_nursing_log(
    patient,
    target_date: datetime.date,
    fall_id: str
) -> NursingWardDoc:
    """
    Simulates a full day of nursing logs. Instead of entirely hardcoded matching, 
    we use LlmRetryClient with a low temperature to generate varied but realistic shifts
    (Early, Late, Night) based on the patient's current active diagnoses.
    """
    logger.info(f"Generating Daily Nursing Log for {getattr(patient.identity, 'name', 'Unknown') if hasattr(patient, 'identity') else 'Unknown'}...")

    # We want varied generation but deterministic JSON adherence.
    config = LlmConfig(temperature=0.4)
    client = LlmRetryClient(config=config)

    system_context = (
        "Du bist eine examinierte Pflegefachkraft in einer deutschen Klinik. "
        "Schreibe typische, realistische Pflegeberichte für eine Schicht. "
        "Verwende Fachbegriffe (z.B. Dekubitusprophylaxe, Mobilisation, VZ-Kontrolle). "
        f"{_build_patient_context(patient)}"
    )

    prompt = (
        f"Generiere für den {target_date.strftime('%d.%m.%Y')} genau DREI Schichten "
        "(Frühschicht 06:00-14:00, Spätschicht 14:00-22:00, Nachtschicht 22:00-06:00). "
        "Passe die Vitals und Beobachtungen an die aktiven Diagnosen des Patienten an."
    )

    # Define an intermediate model mapping just the list of shifts to help LLM
    class _GenShifts(BaseModel):
        shifts: list[NursingShiftLog]

    try:
        content = client.generate_structured(
            prompt=prompt,
            schema=_GenShifts,
            system_context=system_context
        )

        return NursingWardDoc(
            patient_id=getattr(patient.identity, 'base_patient_id', 'UNKNOWN') if hasattr(patient, 'identity') else 'UNKNOWN',
            patient_name=getattr(patient.identity, 'name', 'UNKNOWN') if hasattr(patient, 'identity') else 'UNKNOWN',
            fall_id=fall_id,
            document_date=target_date.strftime("%d.%m.%Y"),
            shift_logs=content.shifts
        )
    except Exception as e:
        logger.error(f"Failed to generate NursingWardDoc: {e}")
        raise


if __name__ == "__main__":
    try:
        from patient_state import PatientIdentity, PatientState  # type: ignore
    except ImportError:
        print("patient_state not found, skipping self-test.")
        sys.exit(0)

    fake_patient = PatientState(
        identity=PatientIdentity(
            name="Edith Maier",
            birth_date=datetime.date(1940, 10, 12),
            gender="w",
            base_patient_id="P99999"
        ),
        active_diagnoses=["Oberschenkelhalsfraktur rechts", "Arterielle Hypertonie"],
        active_medications=[],
        timeline=[]
    )

    print("Generating Daily Nursing Log...")
    log = generate_daily_nursing_log(
        patient=fake_patient,
        target_date=datetime.date(2026, 2, 28),
        fall_id="FALL9875"
    )
    print(log.model_dump_json(indent=2))
