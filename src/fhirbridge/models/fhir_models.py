"""
ISiK-konforme FHIR R4 Pydantic-Modelle.

Dieses Modul definiert strukturierte Pydantic-Modelle für:
  - ISiKPatient (Patient)
  - ISiKKontaktGesundheitseinrichtung (Encounter)

Die Modelle orientieren sich an den ISiK-Basismodul-Profilen (Stufe 3+)
und erzwingen zentrale Pflichtfelder sowie Must-Support-Elemente auf
Python-Ebene.

Referenzen:
  - https://simplifier.net/isik-basis-v4/isikpatient
  - https://simplifier.net/isik-basis-v4/isikkontaktgesundheitseinrichtung
  - FHIR R4: https://hl7.org/fhir/R4/
"""

from __future__ import annotations

import re
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator

# =============================================================================
# ISiK Profil-URLs (Kanonisch)
# =============================================================================

ISIK_PATIENT_PROFILE = "https://gematik.de/fhir/isik/StructureDefinition/ISiKPatient"
ISIK_ENCOUNTER_PROFILE = (
    "https://gematik.de/fhir/isik/StructureDefinition/" "ISiKKontaktGesundheitseinrichtung"
)


# =============================================================================
# FHIR Basis-Datentypen (Leaf Nodes)
# =============================================================================


class Extension(BaseModel):
    """Generische FHIR Extension (url + value[x]).

    Wird für deutsche ISiK-Extensions gebraucht, z.B.:
      - Stadtteil in Address
      - GeschlechtAdministrativ
    """

    url: str
    valueString: str | None = None
    valueCode: str | None = None
    valueCoding: Coding | None = None
    valueBoolean: bool | None = None
    valueReference: Reference | None = None


class Meta(BaseModel):
    """FHIR Meta — enthält die Profil-URL zur ISiK-Konformitätserklärung."""

    profile: list[str] | None = None
    versionId: str | None = None
    lastUpdated: str | None = None
    source: str | None = None


class Identifier(BaseModel):
    """FHIR Identifier — z.B. KVNR, PID, Fallnummer.

    ISiK verlangt mindestens einen Identifier auf Patient und Encounter.
    Typische Systeme:
      - GKV KVNR: http://fhir.de/sid/gkv/kvid-10
      - PKV:      http://fhir.de/sid/pkv/kvid-10
      - PID:      Krankenhaus-spezifisch
    """

    use: str | None = None  # 'usual' | 'official' | 'temp' | 'secondary'
    type: CodeableConcept | None = None
    system: str | None = None
    value: str | None = None


class HumanName(BaseModel):
    """FHIR HumanName — Name des Patienten.

    ISiK: `family` und `given` sind Must-Support.
    """

    use: str | None = None  # 'official' | 'usual' | 'maiden' | ...
    text: str | None = None
    family: str | None = None
    given: list[str] | None = None
    prefix: list[str] | None = None
    suffix: list[str] | None = None
    extension: list[Extension] | None = None


class Address(BaseModel):
    """FHIR Address — inkl. deutscher Extensions.

    ISiK Must-Support: `line`, `city`, `postalCode`, `country`.
    Deutsche Profile ergänzen _line-Extensions für Straßenname,
    Hausnummer, Zusatz und Stadtteil.
    """

    use: str | None = None  # 'home' | 'work' | 'temp' | 'billing'
    type: str | None = None  # 'postal' | 'physical' | 'both'
    text: str | None = None
    line: list[str] | None = None
    city: str | None = None
    district: str | None = None
    state: str | None = None
    postalCode: str | None = None
    country: str | None = None
    extension: list[Extension] | None = None


class ContactPoint(BaseModel):
    """FHIR ContactPoint — Telefon, E-Mail etc.

    ISiK Must-Support auf Patient.telecom.
    """

    system: str | None = None  # 'phone' | 'fax' | 'email' | 'pager' | 'url'
    value: str | None = None
    use: str | None = None  # 'home' | 'work' | 'temp' | 'mobile'
    rank: int | None = None


class Coding(BaseModel):
    """FHIR Coding — ein einzelner Code in einem Codesystem."""

    system: str | None = None
    version: str | None = None
    code: str | None = None
    display: str | None = None
    userSelected: bool | None = None


class CodeableConcept(BaseModel):
    """FHIR CodeableConcept — kodiertes Konzept mit optionalem Freitext."""

    coding: list[Coding] | None = None
    text: str | None = None


class Reference(BaseModel):
    """FHIR Reference — Verweis auf eine andere Ressource."""

    reference: str | None = None  # z.B. "Patient/123"
    type: str | None = None
    identifier: Identifier | None = None
    display: str | None = None

    @model_validator(mode="after")
    def check_not_empty(self) -> Reference:
        if not self.reference and not self.identifier and not self.display:
            raise ValueError("Reference must have at least a reference, identifier, or display.")
        return self


class Period(BaseModel):
    """FHIR Period — Zeitspanne mit Start- und optionalem Enddatum."""

    start: str | None = None  # ISO 8601 / FHIR dateTime
    end: str | None = None


class Narrative(BaseModel):
    """FHIR Narrative — menschenlesbarer Text einer Ressource."""

    status: str | None = None  # 'generated' | 'extensions' | 'additional'
    div: str | None = None  # XHTML


# =============================================================================
# Encounter-spezifische Unterstrukturen
# =============================================================================


class EncounterDiagnosis(BaseModel):
    """Diagnose-Zuordnung innerhalb eines Encounters."""

    condition: Reference
    use: CodeableConcept | None = None
    rank: int | None = None


class EncounterLocation(BaseModel):
    """Ortszuordnung innerhalb eines Encounters (Station, Bett).

    ISiK Must-Support für stationäre Encounters.
    """

    location: Reference
    status: str | None = None  # 'planned'|'active'|'reserved'|'completed'
    physicalType: CodeableConcept | None = None
    period: Period | None = None


class EncounterHospitalization(BaseModel):
    """Aufnahme- und Entlassungsdetails.

    Relevant für stationäre ISiK-Encounters:
      - admitSource: Aufnahmeanlass
      - dischargeDisposition: Entlassungsgrund
    """

    admitSource: CodeableConcept | None = None
    dischargeDisposition: CodeableConcept | None = None
    preAdmissionIdentifier: Identifier | None = None
    origin: Reference | None = None
    destination: Reference | None = None
    extension: list[Extension] | None = None


# =============================================================================
# Root-Ressourcen
# =============================================================================


class Patient(BaseModel):
    """ISiK-konformer FHIR Patient.

    Pflichtfelder (ISiK Basismodul):
      - identifier (mind. 1, z.B. KVNR oder PID)
      - name       (mind. 1 HumanName)
      - gender     (FHIR AdministrativeGender ValueSet)
      - birthDate  (YYYY-MM-DD)

    Must-Support:
      - active, telecom, address, meta.profile
    """

    model_config = ConfigDict(populate_by_name=True)

    resourceType: Literal["Patient"] = "Patient"
    id: str | None = None
    meta: Meta = Field(default_factory=lambda: Meta(profile=[ISIK_PATIENT_PROFILE]))
    text: Narrative | None = None
    extension: list[Extension] | None = None

    # --- Pflicht ---
    identifier: list[Identifier] = Field(..., min_length=1)
    name: list[HumanName] = Field(..., min_length=1)
    gender: Literal["male", "female", "other", "unknown"]
    birthDate: str = Field(..., pattern=r"^\d{4}(-\d{2}(-\d{2})?)?$")  # YYYY-MM-DD

    # --- Must-Support ---
    active: bool | None = None
    telecom: list[ContactPoint] | None = None
    address: list[Address] | None = None

    @model_validator(mode="after")
    def validate_isik_constraints(self) -> Patient:
        # 1. KVNR Formatprüfung & PID Pflicht
        has_valid_identifier = False
        valid_kvid_systems = [
            "http://fhir.de/sid/gkv/kvid-10",
            "http://fhir.de/sid/pkv/kvid-10",
        ]

        for ident in self.identifier:
            if ident.system in valid_kvid_systems:
                has_valid_identifier = True
                if ident.value and not re.match(r"^[A-Z][0-9]{9}$", ident.value):
                    raise ValueError(
                        f"Ungültige KVNR: '{ident.value}'. Muss ^[A-Z][0-9]{9}$ entsprechen."
                    )
            elif ident.type and ident.type.coding:
                for c in ident.type.coding:
                    if c.code in ["MR", "PI"]:
                        has_valid_identifier = True
                        break

        if not has_valid_identifier:
            raise ValueError(
                "Patient muss mindestens eine KVNR oder PID (MR/PI) als Identifier haben."
            )

        # 2. HumanName: Mindestens ein Nachname (family)
        if not any(n.family for n in self.name if n.family):
            raise ValueError("ISiK verlangt bei Patient.name mindestens einen Nachnamen (family).")

        return self


type EncounterStatus = Literal[
    "planned",
    "arrived",
    "triaged",
    "in-progress",
    "onleave",
    "finished",
    "cancelled",
    "entered-in-error",
    "unknown",
]


class Encounter(BaseModel):
    """ISiK-konformer FHIR Encounter (Kontakt/Fall).

    Pflichtfelder (ISiK Basismodul):
      - identifier  (mind. 1, z.B. Fallnummer)
      - status      (FHIR EncounterStatus ValueSet)
      - class_      (Alias "class" — Fallart: AMB, IMP, EMER, ...)
      - type        (Kontaktart, z.B. Abteilungskontakt)
      - subject     (Referenz auf Patient)

    Must-Support:
      - serviceType     (Fachabteilungsschlüssel DKG)
      - period, location, hospitalization, partOf, diagnosis, account
    """

    model_config = ConfigDict(populate_by_name=True)

    resourceType: Literal["Encounter"] = "Encounter"
    id: str | None = None
    meta: Meta = Field(default_factory=lambda: Meta(profile=[ISIK_ENCOUNTER_PROFILE]))
    text: Narrative | None = None
    extension: list[Extension] | None = None

    # --- Pflicht ---
    identifier: list[Identifier] = Field(..., min_length=1)
    status: EncounterStatus
    class_: Coding = Field(alias="class")
    type: list[CodeableConcept] | None = None
    subject: Reference

    # --- Must-Support ---
    serviceType: CodeableConcept | None = None
    period: Period | None = None
    location: list[EncounterLocation] | None = None
    hospitalization: EncounterHospitalization | None = None
    serviceProvider: Reference | None = None
    partOf: Reference | None = None
    diagnosis: list[EncounterDiagnosis] | None = None
    account: list[Reference] | None = None

    @model_validator(mode="after")
    def validate_isik_encounter(self) -> Encounter:
        has_vn = False
        for ident in self.identifier:
            # Check auf 'VN' (Visit Number / Fallnummer) in type.coding
            if ident.type and ident.type.coding:
                if any(c.code == "VN" for c in ident.type.coding):
                    has_vn = True
                    break
            # Fallback auf System-URI, falls type fehlt
            if ident.system and "fallnummer" in ident.system.lower():
                has_vn = True
                break

        if not has_vn:
            raise ValueError(
                "Encounter muss zwingend eine Fallnummer"
                " (Identifier Typ 'VN' oder passendes System) haben."
            )

        return self


# =============================================================================
# Intermediate Extraction Models (Lenient LLM Targets)
# =============================================================================


class PatientExtraction(BaseModel):
    """Lenient model for LLM to extract patient data. No strict ENUMs or ISiK rules."""

    identifier: list[dict[str, str]] | None = None  # [{"value": "123"}]
    name: list[dict[str, Any]] | None = None  # [{"family": "Doe", "given": ["John"]}]
    gender: str | None = None  # 'male', 'female', 'm', 'weiblich', etc.
    birthDate: str | None = None


class EncounterExtraction(BaseModel):
    """Lenient model for LLM to extract encounter data."""

    identifier: list[dict[str, str]] | None = None
    diagnoses: list[dict[str, str]] | None = None


class BundleExtraction(BaseModel):
    """Root model for OCR text extraction."""

    Patient: PatientExtraction | None = None
    Encounter: EncounterExtraction | None = None


# =============================================================================
# Forward-Reference-Auflösung
# =============================================================================

Extension.model_rebuild()
Identifier.model_rebuild()
HumanName.model_rebuild()
Reference.model_rebuild()
Encounter.model_rebuild()
Patient.model_rebuild()
PatientExtraction.model_rebuild()
EncounterExtraction.model_rebuild()
BundleExtraction.model_rebuild()
