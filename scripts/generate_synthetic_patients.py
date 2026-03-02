import argparse
import datetime
import logging
import random
import sys
import uuid
from pathlib import Path

from faker import Faker

# Setup Paths to Skills and Core
ROOT_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT_DIR / "src"))
sys.path.insert(
    0, str(ROOT_DIR / ".agents" / "skills" / "orchestrating-clinical-scenarios" / "scripts")
)
sys.path.insert(0, str(ROOT_DIR / ".agents" / "skills" / "generating-lab-results" / "scripts"))

from patient_state import (  # noqa: E402
    MedicalEvent,
    MedicalEventType,
    PatientIdentity,
    PatientState,
)
from simulate_labs import generate_correlating_labs  # noqa: E402

from fhirbridge.core.llm_client import LlmClient  # noqa: E402
from fhirbridge.core.pdf_engine import MedicalPdfEngine  # noqa: E402
from fhirbridge.models.kdl_document import DischargeBrief  # noqa: E402

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)


def simulate_patient_lifeline(fake: Faker, pt_idx: int) -> PatientState:
    """Generates a structured PatientState with a causal, longitudinal clinical arc."""
    gender = random.choice(["m", "w"])
    first_name = fake.first_name_male() if gender == "m" else fake.first_name_female()
    last_name = fake.last_name()
    name = f"{first_name} {last_name}"

    # Calculate Age & Birthdate
    age = random.randint(45, 85)  # Tending towards older for cardiovascular risks
    today = datetime.date.today()
    birth_year = today.year - age
    birth_date = datetime.date(birth_year, random.randint(1, 12), random.randint(1, 28))

    # Generate strict ISiK KVNR: ^[A-Z][0-9]{9}$
    letter = chr(65 + random.randint(0, 25))
    number = f"{random.randint(0, 999999999):09d}"
    patient_id = f"{letter}{number}"

    identity = PatientIdentity(
        name=name, birth_date=birth_date, gender=gender, base_patient_id=patient_id
    )

    # 1. Cardiovascular Risk Profile and Chronic Conditions
    smoker = random.random() < 0.4
    obesity = random.random() < 0.5

    chronic_conditions = []
    daily_meds = []

    if age > 50 and obesity:
        chronic_conditions.append("Diabetes Mellitus Typ 2")
        daily_meds.append("Metformin")
    if age > 60 or smoker or obesity:
        chronic_conditions.append("Arterielle Hypertonie")
        daily_meds.append("Ramipril")
    if smoker and age > 65:
        chronic_conditions.append("COPD")
        daily_meds.append("Salbutamol Bedarfsmedikation")

    if not chronic_conditions:
        chronic_conditions = ["Essentielle Hypertonie"]
        daily_meds = ["Amlodipin"]

    state = PatientState(
        identity=identity, active_diagnoses=chronic_conditions, active_medications=daily_meds
    )

    logger.info(
        f"[{patient_id}] Simulated Patient Profile: Age {age}, Diagnoses: {chronic_conditions}"
    )

    # 2. Historical Acute Encounters (Hospital Stays)
    num_encounters = random.randint(2, 3)

    # Generate random admission dates in the past 10 years, sorted chronologically
    admission_dates = sorted(
        [today - datetime.timedelta(days=random.randint(30, 3650)) for _ in range(num_encounters)]
    )

    encounter_reasons = []
    if "Diabetes Mellitus Typ 2" in chronic_conditions:
        encounter_reasons.extend(["Diabetisches Fußsyndrom", "Hypoglykämie"])
    if "Arterielle Hypertonie" in chronic_conditions:
        encounter_reasons.extend(["NSTEMI", "Hypertensive Entgleisung"])
    if "COPD" in chronic_conditions:
        encounter_reasons.extend(["COPD Exazerbation", "Pneumonie"])
    if not encounter_reasons:
        encounter_reasons = ["Akute Appendizitis", "Sepsis"]

    for i, admission_date in enumerate(admission_dates):
        reason = random.choice(encounter_reasons)
        los = random.randint(4, 10)  # Length of stay in days
        discharge_date = admission_date + datetime.timedelta(days=los)

        # Fall ID e.g. FALL-2018-8A3B
        fall_id = f"FALL-{admission_date.strftime('%Y')}-{uuid.uuid4().hex[:4].upper()}"
        logger.info(f"[{patient_id}] Generating Encounter {fall_id}: {reason} ({los} days)")

        # Day 1: Admission
        state.add_event(
            MedicalEvent(
                fall_id=fall_id,
                date=admission_date,
                event_type=MedicalEventType.ADMISSION,
                description=f"Stationäre Aufnahme wegen {reason}.",
            )
        )

        # Day 1 to Discharge: Daily Lab Results
        for day in range(los):
            lab_date = admission_date + datetime.timedelta(days=day)
            state.add_event(
                MedicalEvent(
                    fall_id=fall_id,
                    date=lab_date,
                    event_type=MedicalEventType.LAB_RESULT,
                    description=f"Tägliches Routinelabor (Tag {day + 1}).",
                )
            )

        # Final Day: Discharge
        state.add_event(
            MedicalEvent(
                fall_id=fall_id,
                date=discharge_date,
                event_type=MedicalEventType.DISCHARGE,
                description=f"Entlassung nach Behandlung von: {reason}.",
            )
        )

        # Optionally add a medication or diagnosis update based on the encounter
        if reason == "NSTEMI" and "ASS" not in state.active_medications:
            state.active_medications.extend(["ASS", "Bisoprolol"])
            state.active_diagnoses.append("Z.n. NSTEMI")

    return state


def dispatch_llm_discharge(
    llm_client: LlmClient,
    pdf_engine: MedicalPdfEngine,
    state: PatientState,
    event: MedicalEvent,
    fall_dir: Path,
    fall_id: str,
):
    """Uses LLM to generate physical text for a DISCHARGE KDL and renders via PDFEngine."""
    output_pdf_filename = f"KDL-AD010103_{event.date.strftime('%Y%m%d')}.pdf"
    output_pdf_path = fall_dir / output_pdf_filename

    if output_pdf_path.exists():
        logger.info(
            f"[{state.identity.base_patient_id}] Skipping DISCHARGE, file exists: {output_pdf_filename}"
        )
        return

    logger.info(f"[{state.identity.base_patient_id}] Dispatching LLM DISCHARGE event...")

    context = (
        f"Patient: {state.identity.name}, Geboren: {state.identity.birth_date}, Geschlecht: {state.identity.gender}\n"
        f"Bisherige Diagnosen: {', '.join(state.active_diagnoses)}\n"
        f"Laufende Medikamente: {', '.join(state.active_medications)}\n"
    )

    prompt = (
        f"Erstelle einen ausführlichen, realistischen Entlassungsbericht (DischargeBrief) "
        f"für folgendes klinisches Ereignis: {event.description}."
    )

    try:
        discharge_brief = llm_client.generate_structured_kdl(
            prompt=prompt,
            schema_class=DischargeBrief,
            context=context,
            target_date_str=event.date.strftime("%d.%m.%Y"),
        )

        # Override to ensure consistency
        discharge_brief.patient_id = state.identity.base_patient_id
        discharge_brief.patient_name = state.identity.name
        discharge_brief.fall_id = fall_id
        discharge_brief.document_date = event.date.strftime("%d.%m.%Y")
        discharge_brief.kdl_code = "AD010103"

        temp_clean = fall_dir / f"clean_{output_pdf_filename}"

        pdf_engine.render_clean_pdf(
            doc_obj=discharge_brief, output_path=str(temp_clean), include_qr=True
        )
        pdf_engine.degrade_pdf_to_scan(
            clean_pdf=str(temp_clean), dirty_pdf=str(output_pdf_path), remove_clean=True
        )
        logger.info(f"[{state.identity.base_patient_id}] Generated LLM PDF: {output_pdf_filename}")

    except Exception as e:
        logger.error(
            f"[{state.identity.base_patient_id}] Failed LLM Dispatch for {event.date}: {e}"
        )


def dispatch_algorithmic_lab(
    pdf_engine: MedicalPdfEngine,
    state: PatientState,
    event: MedicalEvent,
    fall_dir: Path,
    fall_id: str,
):
    """Uses the generate_correlating_labs algorithmic approach and renders via PDFEngine."""
    logger.info(f"[{state.identity.base_patient_id}] Dispatching Algorithmic LAB event...")

    lab_doc = generate_correlating_labs(
        active_diagnoses=state.active_diagnoses,
        patient_id=state.identity.base_patient_id,
        patient_name=state.identity.name,
        fall_id=fall_id,
        document_date=event.date.strftime("%d.%m.%Y"),
    )

    output_pdf_filename = f"KDL-LB120103_{event.date.strftime('%Y%m%d')}.pdf"
    output_pdf_path = fall_dir / output_pdf_filename
    temp_clean = fall_dir / f"clean_{output_pdf_filename}"

    pdf_engine.render_clean_pdf(
        doc_obj=lab_doc, output_path=str(temp_clean), include_qr=False
    )  # Labs typically might not have QR
    pdf_engine.degrade_pdf_to_scan(
        clean_pdf=str(temp_clean), dirty_pdf=str(output_pdf_path), remove_clean=True
    )
    logger.info(
        f"[{state.identity.base_patient_id}] Generated Algorithmic PDF: {output_pdf_filename}"
    )


def main():
    parser = argparse.ArgumentParser(
        description="Master Orchestrator: Synthetische Patienten (Antigravity Goldstandard)"
    )
    parser.add_argument(
        "--limit", type=int, default=10, help="Anzahl der zu generierenden Patientenakten"
    )
    args = parser.parse_args()

    logger.info(f"=== Starte Master Orchestrator ({args.limit} Patienten) ===")

    fake = Faker("de_DE")
    llm_client = LlmClient()
    pdf_engine = MedicalPdfEngine()

    inbound_dir = ROOT_DIR / "data" / "inbound"
    inbound_dir.mkdir(parents=True, exist_ok=True)

    temp_dir = ROOT_DIR / "data" / "temp_media"
    temp_dir.mkdir(parents=True, exist_ok=True)

    for i in range(args.limit):
        try:
            state = simulate_patient_lifeline(fake, i + 1)
            logger.info(
                f"--- Processing {i+1}/{args.limit}: {state.identity.name} ({state.identity.base_patient_id}) ---"
            )

            # Save state explicitly for documentation/debugging purposes in temp
            state_file = temp_dir / f"state_{state.identity.base_patient_id}.json"
            with open(state_file, "w", encoding="utf-8") as f:
                f.write(state.model_dump_json(indent=2))

            patient_dir = inbound_dir / state.identity.base_patient_id

            # Loop over events in the timeline
            for event in state.timeline:
                fall_id = event.fall_id
                fall_dir = patient_dir / fall_id
                fall_dir.mkdir(parents=True, exist_ok=True)

                if event.event_type == MedicalEventType.LAB_RESULT:
                    dispatch_algorithmic_lab(pdf_engine, state, event, fall_dir, fall_id)
                elif event.event_type == MedicalEventType.DISCHARGE:
                    dispatch_llm_discharge(llm_client, pdf_engine, state, event, fall_dir, fall_id)
                else:
                    logger.debug(
                        f"Skipping abstract event type: {event.event_type.name} (handled implicitly or ignored)"
                    )

        except Exception as e:
            logger.error(f"Error processing patient {i+1}: {e}")

    pdf_engine.cleanup()
    logger.info("Master Orchestrator Lauf erfolgreich beendet.")


if __name__ == "__main__":
    main()
