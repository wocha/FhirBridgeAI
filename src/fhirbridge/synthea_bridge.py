import logging
from datetime import datetime
from typing import Any

from fhirbridge.core.llm_client import LlmClient
from fhirbridge.models.kdl_document import DischargeBrief

logger = logging.getLogger(__name__)


class PatientState:
    """
    Represents the accumulated medical history of a patient up to a specific encounter.
    Used as context for the LLM to generate consistent documents.
    """

    def __init__(self, patient_info: dict[str, Any]):
        self.patient_info = patient_info
        self.conditions: list[dict[str, Any]] = []
        self.observations: list[dict[str, Any]] = []
        self.medications: list[dict[str, Any]] = []

    def add_condition(self, condition: dict[str, Any]) -> None:
        self.conditions.append(condition)

    def add_observation(self, observation: dict[str, Any]) -> None:
        self.observations.append(observation)

    def add_medication(self, medication: dict[str, Any]) -> None:
        self.medications.append(medication)

    def to_context_string(self) -> str:
        """Serializes current state into a readable prompt context."""
        context = []

        # Patient Info
        name_dict = self.patient_info.get("name", [{}])[0]
        name = f"{name_dict.get('given', [''])[0]} {name_dict.get('family', '')}".strip()
        gender = self.patient_info.get("gender", "unknown")
        birth_date = self.patient_info.get("birthDate", "unknown")
        context.append(f"Patient: {name} (Geb.: {birth_date}, Geschlecht: {gender})")

        # Conditions
        if self.conditions:
            context.append("\nBekannte Diagnosen/Zustände:")
            for cond in self.conditions:
                code_text = cond.get("code", {}).get("text", "Unbekannt")
                onset = cond.get("onsetDateTime", "Unbekannt")
                context.append(f"- {code_text} (seit {onset})")

        # Observations (Recent)
        if self.observations:
            context.append("\nAktuelle Beobachtungen/Laborwerte:")
            # Limit to last 10 to save context length
            for obs in self.observations[-10:]:
                code_text = obs.get("code", {}).get("text", "Unbekannt")
                value_quantity = obs.get("valueQuantity", {})
                if value_quantity:
                    val = value_quantity.get("value")
                    unit = value_quantity.get("unit")
                    context.append(f"- {code_text}: {val} {unit}")
                else:
                    context.append(f"- {code_text}")

        return "\n".join(context)


class SyntheaParser:
    """
    Parses a Synthea FHIR JSON bundle and replays the patient's history chronologically.
    """

    def __init__(self, bundle: dict[str, Any]):
        self.bundle = bundle
        self.resources = [entry.get("resource", {}) for entry in bundle.get("entry", [])]
        self.patient = self._find_patient()
        self.encounters = self._find_resources_by_type("Encounter")
        self.conditions = self._find_resources_by_type("Condition")
        self.observations = self._find_resources_by_type("Observation")
        self.medication_requests = self._find_resources_by_type("MedicationRequest")

        # Sort encounters by start date
        self.encounters.sort(key=lambda e: e.get("period", {}).get("start", "1900-01-01"))

    def _find_patient(self) -> dict[str, Any]:
        for r in self.resources:
            if r.get("resourceType") == "Patient":
                return r  # type: ignore[no-any-return]
        return {}

    def _find_resources_by_type(self, resource_type: str) -> list[dict[str, Any]]:
        return [r for r in self.resources if r.get("resourceType") == resource_type]

    def _get_resources_up_to_date(
        self, resources: list[dict[str, Any]], date_str: str, date_field: str
    ) -> list[dict[str, Any]]:
        """Helper to get resources that occurred at or before the given date_str."""
        result = []
        for r in resources:
            r_date = (
                r.get(date_field)
                or r.get("effectiveDateTime")
                or r.get("onsetDateTime")
                or r.get("authoredOn")
            )
            if r_date and r_date <= date_str:
                result.append(r)
        return result

    def get_patient_state_at_encounter(self, encounter: dict[str, Any]) -> PatientState:
        """Reconstructs the patient's clinical state up to the end of the given encounter."""
        state = PatientState(self.patient)
        end_date = encounter.get("period", {}).get(
            "end", encounter.get("period", {}).get("start", "2099-01-01")
        )

        for cond in self._get_resources_up_to_date(self.conditions, end_date, "onsetDateTime"):
            state.add_condition(cond)

        for obs in self._get_resources_up_to_date(self.observations, end_date, "effectiveDateTime"):
            state.add_observation(obs)

        for med in self._get_resources_up_to_date(self.medication_requests, end_date, "authoredOn"):
            state.add_medication(med)

        return state


def generate_kdl_from_encounter(
    llm_client: LlmClient, parser: SyntheaParser, encounter: dict[str, Any]
) -> DischargeBrief:
    """
    Takes an isolated Encounter and the patient's history, and asks Mistral to formulate
    a KDL AD010111 (Ambulanzbrief / Entlassungsbericht).
    """
    state = parser.get_patient_state_at_encounter(encounter)
    state_context = state.to_context_string()

    encounter_start = encounter.get("period", {}).get("start", "")
    encounter_end = encounter.get("period", {}).get("end", encounter_start)
    encounter_reason = "Unbekannt"
    reason_codes = encounter.get("reasonCode")
    if reason_codes:
        encounter_reason = reason_codes[0].get("text", "Unbekannt")

    # Format dates
    def format_date(iso_date: str) -> str:
        try:
            return datetime.fromisoformat(iso_date.replace("Z", "+00:00")).strftime("%d.%m.%Y")
        except Exception:
            return iso_date

    doc_date_str = format_date(encounter_end) if encounter_end else "01.01.2024"

    patient_name_dict = parser.patient.get("name", [{}])[0]
    patient_name = (
        f"{patient_name_dict.get('given', [''])[0]} {patient_name_dict.get('family', '')}".strip()
    )
    patient_id_raw = parser.patient.get("id", "Unknown-ID")
    import hashlib

    h = hashlib.md5(patient_id_raw.encode()).hexdigest()
    # Generate strict ISiK KVNR: ^[A-Z][0-9]{9}$
    patient_id = f"{chr(65 + int(h[0], 16) % 26)}{int(h[1:9], 16) % 1000000000:09d}"

    encounter_id_raw = encounter.get("id", "Unknown-Encounter-ID")
    h_enc = hashlib.md5(encounter_id_raw.encode()).hexdigest()
    encounter_id = f"F-{int(h_enc[:8], 16) % 100000000:08d}"

    prompt = f"""
    Schreibe einen deutschen Arztbrief-Freitext
    (KDL AD010111 / Ambulanzbrief) für diesen Patientenaufenthalt.

    Details zum Aufenthalt (Encounter):
    - Aufnahmegrund: {encounter_reason}
    - Zeitraum: {format_date(encounter_start)} bis {doc_date_str}

    Weise den Patientendaten die folgenden IDs und Codes zu:
    - kdl_code: "AD010111"
    - kdl_name: "Ambulanzbrief"
    - patient_id: "{patient_id}"
    - patient_name: "{patient_name}"
    - fall_id: "{encounter_id}"
    - document_date: "{doc_date_str}"
    - title: "AMBULANZBRIEF"

    Zusätzliche Anweisungen:
    - Beschreibe den Verlauf und die Empfehlungen
      detailliert in den `content_paragraphs`.
    - Nutze typische medizinische Fachbegriffe auf Deutsch.
    - Halluziniere keine grundlosen völlig neuen Krankheiten,
      sondern beziehe dich auf den angegebenen Kontext.
    """

    # Use LLM to generate the discharge brief
    kdl_doc = llm_client.generate_structured_kdl(
        prompt=prompt.strip(),
        schema_class=DischargeBrief,
        context=state_context,
        target_date_str=doc_date_str,
    )

    return kdl_doc
