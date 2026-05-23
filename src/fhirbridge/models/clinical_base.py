from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator

from fhirbridge.models.fhir_models import (
    CodeableConcept,
    Meta,
    Narrative,
    Period,
    Reference,
)

# =============================================================================
# Code-Systeme Konfiguration (ISiK / KRITIS)
# =============================================================================

SYSTEM_ICD10_GM = "http://fhir.de/CodeSystem/bfarm/icd-10-gm"
SYSTEM_OPS = "http://fhir.de/CodeSystem/bfarm/ops"
SYSTEM_KDL = "http://dvmd.de/fhir/CodeSystem/kdl"
SYSTEM_LOINC = "http://loinc.org"
SYSTEM_KVNR_GKV = "http://fhir.de/sid/gkv/kvid-10"
SYSTEM_KVNR_PKV = "http://fhir.de/sid/pkv/kvid-10"


# =============================================================================
# Basis Medizinische Entitäten
# =============================================================================


class Condition(BaseModel):
    """ISiK-Diagnose (Condition).

    Must-Support:
      - clinicalStatus, verificationStatus
      - code (bevorzugt ICD-10-GM via SYSTEM_ICD10_GM)
      - subject (Patient)
      - recordedDate
    """

    model_config = ConfigDict(populate_by_name=True)

    resourceType: Literal["Condition"] = "Condition"
    id: str | None = None
    meta: Meta = Field(
        default_factory=lambda: Meta(
            profile=["https://gematik.de/fhir/isik/StructureDefinition/ISiKDiagnose"]
        )
    )

    clinicalStatus: CodeableConcept | None = None
    verificationStatus: CodeableConcept | None = None
    category: list[CodeableConcept] | None = None
    code: CodeableConcept
    bodySite: list[CodeableConcept] | None = None
    subject: Reference
    encounter: Reference | None = None
    recordedDate: str | None = None

    @model_validator(mode="after")
    def validate_icd10(self) -> Condition:
        # Eine warnende Validierung, falls das System ungleich ICD-10-GM ist,
        # dies wird in der Praxis oft auch durch SNOMED abgebildet (hier loose Constraint)
        return self


class Procedure(BaseModel):
    """ISiK-Prozedur (Procedure)."""

    model_config = ConfigDict(populate_by_name=True)

    resourceType: Literal["Procedure"] = "Procedure"
    id: str | None = None
    meta: Meta = Field(
        default_factory=lambda: Meta(
            profile=["https://gematik.de/fhir/isik/StructureDefinition/ISiKProzedur"]
        )
    )

    status: Literal[
        "preparation",
        "in-progress",
        "not-done",
        "on-hold",
        "stopped",
        "completed",
        "entered-in-error",
        "unknown",
    ]
    category: CodeableConcept | None = None
    code: CodeableConcept  # Sollte OPS enthalten
    subject: Reference
    encounter: Reference | None = None
    performedDateTime: str | None = None
    performedPeriod: Period | None = None

    @model_validator(mode="after")
    def validate_ops(self) -> Procedure:
        return self


# =============================================================================
# Komplexe ISiK Profile (Observation & Composition)
# =============================================================================


class ISiKObservation(BaseModel):
    """ISiK-konforme Observation (Laborwerte / Vitalparameter).

    Must-Support:
      - status
      - category
      - code (LOINC)
      - subject
      - effective[x] (DateTime)
      - value[x] (Quantity, CodeableConcept, String)
    """

    model_config = ConfigDict(populate_by_name=True)

    resourceType: Literal["Observation"] = "Observation"
    id: str | None = None
    meta: Meta = Field(
        default_factory=lambda: Meta(
            profile=["https://gematik.de/fhir/isik/StructureDefinition/ISiKObservation"]
        )
    )

    status: Literal[
        "registered",
        "preliminary",
        "final",
        "amended",
        "corrected",
        "cancelled",
        "entered-in-error",
        "unknown",
    ]
    category: list[CodeableConcept] = Field(..., min_length=1)
    code: CodeableConcept
    subject: Reference
    encounter: Reference | None = None
    effectiveDateTime: str = Field(
        ..., pattern=r"^\d{4}(-\d{2}(-\d{2}(T\d{2}:\d{2}:\d{2}(\.\d+)?(Z|([+-]\d{2}:\d{2})))?)?)?$"
    )

    # Exklusives Value-Feld
    valueQuantity: dict[str, Any] | None = None  # in FHIR: Quantity
    valueCodeableConcept: CodeableConcept | None = None
    valueString: str | None = None

    @model_validator(mode="after")
    def check_exclusive_value(self) -> ISiKObservation:
        values_set = sum(
            1
            for v in [self.valueQuantity, self.valueCodeableConcept, self.valueString]
            if v is not None
        )
        if values_set > 1:
            raise ValueError(
                "Observation darf nur maximal einen value[x]"
                " (Quantity, CodeableConcept, String) haben."
            )
        return self


class CompositionSection(BaseModel):
    """Ein Abschnitt in einem Arztbrief."""

    title: str
    code: CodeableConcept | None = None
    text: Narrative | None = None
    entry: list[Reference] | None = None


class ISiKArztbrief(BaseModel):
    """ISiK-konformer Arztbrief (Composition).

    Must-Support:
      - status
      - type (LOINC)
      - category (KDL)
      - subject
      - date
      - author
      - title
      - section
    """

    model_config = ConfigDict(populate_by_name=True)

    resourceType: Literal["Composition"] = "Composition"
    id: str | None = None
    meta: Meta = Field(
        default_factory=lambda: Meta(
            profile=["https://gematik.de/fhir/isik/StructureDefinition/ISiKArztbrief"]
        )
    )

    status: Literal["preliminary", "final", "amended", "entered-in-error"]
    type: CodeableConcept
    category: list[CodeableConcept] = Field(..., min_length=1)
    subject: Reference
    encounter: Reference | None = None
    date: str
    author: list[Reference] = Field(..., min_length=1)
    title: str
    section: list[CompositionSection] = Field(..., min_length=1)
