import enum
from datetime import date

from pydantic import BaseModel, Field, field_validator


# ---------------------------------------------------------------------------
# 1. Kataloge (Enums) - Das sind unsere strikten "Vokabulare"
# Sie verhindern, dass das LLM halluziniert (z.B. "Männlich", "man", "M" -> alles wird zu MALE)
# ---------------------------------------------------------------------------
class Gender(str, enum.Enum):
    MALE = "male"
    FEMALE = "female"
    OTHER = "other"
    UNKNOWN = "unknown"

class EncounterStatus(str, enum.Enum):
    PLANNED = "planned"
    IN_PROGRESS = "in-progress"
    DISCHARGED = "discharged"
    CANCELLED = "cancelled"

# ---------------------------------------------------------------------------
# 2. Sub-Schemata (Die Bausteine unseres Patienten)
# ---------------------------------------------------------------------------
class ChronicCondition(BaseModel):
    """Repräsentiert eine chronische Vorerkrankung (z.B. Diabetes)."""
    name: str = Field(description="Klartextname der Diagnose, z.B. 'Diabetes Mellitus Typ 2'")
    icd10_code: str | None = Field(None, description="Optionaler ICD-10 Code, z.B. 'E11.9'")
    onset_year: int | None = Field(None, description="Jahr der Erstdiagnose")

    @field_validator('icd10_code')
    def validate_icd10(cls, v):
        if v and not (len(v) >= 3 and v[0].isalpha()):
            raise ValueError("Ungültiges ICD-10 Format (erwartet Buchstabe gefolgt von Zahlen)")
        return v

class CurrentEncounter(BaseModel):
    """Der tagesaktuelle Grund, warum der Patient im Krankenhaus ist (Der 'Fall')."""
    encounter_id: str = Field(description="Eindeutige Fallnummer (Fall-ID)")
    admission_date: date = Field(description="Aufnahmedatum")
    reason_for_admission: str = Field(description="Aufnahmegrund / Einweisungsdiagnose")
    status: EncounterStatus = Field(default=EncounterStatus.IN_PROGRESS, description="Fall-Status")
    ward: str | None = Field(None, description="Aktuelle Station, z.B. 'Innere Medizin 3'")

class PatientDemographics(BaseModel):
    """Stammdaten des Patienten"""
    patient_id: str = Field(description="Zentrale Patienten-ID (MPI)")
    first_name: str
    last_name: str
    date_of_birth: date
    gender: Gender

    @property
    def age(self) -> int:
        today = date.today()
        # Berechnet das exakte Alter
        return today.year - self.date_of_birth.year - ((today.month, today.day) < (self.date_of_birth.month, self.date_of_birth.day))

# ---------------------------------------------------------------------------
# 3. Das Root-Schema (Der 'Patient State')
# Dies ist das JSON-Objekt, das wir in die Datenbank speichern oder dem LLM geben.
# ---------------------------------------------------------------------------
class PatientState(BaseModel):
    """
    Der aggregierte Längsschnitt-Zustand eines Patienten zu einem bestimmten Zeitpunkt.
    Hier fließt alles zusammen: Wer ist der Patient, was hat er chronisch, und warum ist er jetzt hier?
    """
    demographics: PatientDemographics
    chronic_conditions: list[ChronicCondition] = Field(default_factory=list)
    active_encounter: CurrentEncounter | None = Field(None, description="Der aktuelle Krankenhausaufenthalt (falls vorhanden)")

    # Hier merken wir uns, was schon generiert wurde, um Doppelungen zu vermeiden
    generated_documents: list[str] = Field(default_factory=list, description="Liste von KDL/Dokumenten-IDs, die bereits generiert wurden")

    def get_clinical_summary(self) -> str:
        """
        Eine Hilfsfunktion, die den State in einen sauberen Text-Prompt für Mistral übersetzt.
        """
        demo = self.demographics
        summary = f"Patient: {demo.first_name} {demo.last_name}, {demo.age} Jahre ({demo.gender.value}).\n"

        if self.chronic_conditions:
            conds = ", ".join([f"{c.name} ({c.icd10_code or 'kein ICD'})" for c in self.chronic_conditions])
            summary += f"Chronische Vorerkrankungen: {conds}.\n"
        else:
            summary += "Keine bekannten chronischen Vorerkrankungen.\n"

        if self.active_encounter:
            enc = self.active_encounter
            summary += f"Aktueller Aufenthalt (Fall {enc.encounter_id}): {enc.reason_for_admission}, aufgenommen am {enc.admission_date}, Station: {enc.ward or 'Unbekannt'}."
        else:
            summary += "Patient befindet sich aktuell nicht in stationärer Behandlung."

        return summary
