"""
Tests für die ISiK-konformen FHIR Pydantic-Modelle.

Ausführung:
    cd <project-root>
    python3 -m pytest tests/test_fhir_models.py -v
"""

import json

import pytest
from pydantic import ValidationError

from fhirbridge.models.fhir_models import (
    ISIK_ENCOUNTER_PROFILE,
    ISIK_PATIENT_PROFILE,
    Coding,
    Encounter,
    HumanName,
    Identifier,
    Patient,
    Reference,
)

pytestmark = pytest.mark.smoke

# -------------------------------------------------------------------------
# Fixtures
# -------------------------------------------------------------------------


@pytest.fixture
def valid_patient_dict() -> dict:
    """Vollständiges ISiK-konformes Patient-JSON."""
    return {
        "resourceType": "Patient",
        "id": "pat-12345",
        "meta": {"profile": [ISIK_PATIENT_PROFILE]},
        "identifier": [
            {
                "use": "official",
                "system": "http://fhir.de/sid/gkv/kvid-10",
                "value": "A123456789",
            }
        ],
        "name": [
            {
                "use": "official",
                "family": "Mustermann",
                "given": ["Max"],
            }
        ],
        "gender": "male",
        "birthDate": "1975-12-24",
        "active": True,
        "telecom": [
            {"system": "phone", "value": "+49 30 12345678", "use": "home"},
            {"system": "email", "value": "max@example.de"},
        ],
        "address": [
            {
                "use": "home",
                "line": ["Musterstraße 1"],
                "city": "Berlin",
                "postalCode": "10115",
                "country": "DE",
            }
        ],
    }


@pytest.fixture
def valid_encounter_dict() -> dict:
    """Vollständiges ISiK-konformes Encounter-JSON."""
    return {
        "resourceType": "Encounter",
        "id": "enc-9876",
        "meta": {"profile": [ISIK_ENCOUNTER_PROFILE]},
        "identifier": [
            {
                "use": "usual",
                "system": "https://fhir.krankenhaus.de/sid/fallnummer",
                "value": "F-2026-0034",
            }
        ],
        "status": "finished",
        "class": {
            "system": "http://terminology.hl7.org/CodeSystem/v3-ActCode",
            "code": "IMP",
            "display": "inpatient encounter",
        },
        "type": [
            {
                "coding": [
                    {
                        "system": "http://fhir.de/CodeSystem/kontaktart-de",
                        "code": "abteilungskontakt",
                        "display": "Abteilungskontakt",
                    }
                ]
            }
        ],
        "serviceType": {
            "coding": [
                {
                    "system": "http://fhir.de/CodeSystem/dkgev/Fachabteilungsschluessel",
                    "code": "0100",
                    "display": "Innere Medizin",
                }
            ]
        },
        "subject": {
            "reference": "Patient/pat-12345",
            "display": "Max Mustermann",
        },
        "period": {
            "start": "2026-02-15T08:00:00+01:00",
            "end": "2026-02-20T14:30:00+01:00",
        },
        "location": [
            {
                "location": {"reference": "Location/station-3a", "display": "Station 3A"},
                "status": "active",
            }
        ],
        "hospitalization": {
            "admitSource": {
                "coding": [
                    {
                        "system": "http://fhir.de/CodeSystem/dgkev/Aufnahmeanlass",
                        "code": "E",
                        "display": "Einweisung durch einen Arzt",
                    }
                ]
            },
            "dischargeDisposition": {
                "coding": [
                    {
                        "system": "http://fhir.de/CodeSystem/dkgev/Entlassungsgrund",
                        "code": "01",
                        "display": "Behandlung regulär beendet",
                    }
                ]
            },
        },
        "diagnosis": [
            {
                "condition": {
                    "reference": "Condition/cond-01",
                    "display": "Pneumonie",
                },
                "rank": 1,
            }
        ],
    }


# -------------------------------------------------------------------------
# Tests
# -------------------------------------------------------------------------


class TestPatient:
    """Tests für das ISiKPatient-Modell."""

    def test_patient_valid(self, valid_patient_dict: dict):
        """Ein vollständiges ISiK-Patient-JSON wird erfolgreich validiert."""
        patient = Patient.model_validate(valid_patient_dict)
        assert patient.resourceType == "Patient"
        assert patient.id == "pat-12345"
        assert patient.gender == "male"
        assert patient.birthDate == "1975-12-24"
        assert len(patient.identifier) == 1
        assert patient.identifier[0].value == "A123456789"
        assert patient.active is True
        assert patient.telecom is not None
        assert len(patient.telecom) == 2

    def test_patient_missing_required_fields(self):
        """Fehlende Pflichtfelder lösen ValidationError aus."""
        with pytest.raises(ValidationError) as exc_info:
            Patient.model_validate({"resourceType": "Patient"})
        errors = exc_info.value.errors()
        missing_fields = {e["loc"][0] for e in errors}
        assert "identifier" in missing_fields
        assert "name" in missing_fields
        assert "gender" in missing_fields
        assert "birthDate" in missing_fields

    def test_patient_invalid_gender(self, valid_patient_dict: dict):
        """Ungültiger gender-Wert wird abgewiesen."""
        valid_patient_dict["gender"] = "invalid"
        with pytest.raises(ValidationError):
            Patient.model_validate(valid_patient_dict)

    def test_meta_profile_present(self, valid_patient_dict: dict):
        """meta.profile enthält die ISiK-Profil-URL."""
        patient = Patient.model_validate(valid_patient_dict)
        assert patient.meta.profile is not None
        assert ISIK_PATIENT_PROFILE in patient.meta.profile

    def test_patient_default_meta(self):
        """Ohne explizites meta wird das ISiK-Profil automatisch gesetzt."""
        patient = Patient(
            identifier=[Identifier(system="http://fhir.de/sid/gkv/kvid-10", value="A123456789")],
            name=[HumanName(family="Test")],
            gender="female",
            birthDate="2000-01-01",
        )
        assert patient.meta.profile == [ISIK_PATIENT_PROFILE]

    def test_patient_roundtrip(self, valid_patient_dict: dict):
        """JSON → Modell → JSON Roundtrip behält alle Felder bei."""
        patient = Patient.model_validate(valid_patient_dict)
        output = json.loads(patient.model_dump_json(by_alias=True, exclude_none=True))

        assert output["resourceType"] == "Patient"
        assert output["identifier"][0]["value"] == "A123456789"
        assert output["name"][0]["family"] == "Mustermann"
        assert output["gender"] == "male"
        assert output["address"][0]["city"] == "Berlin"


class TestEncounter:
    """Tests für das ISiKKontaktGesundheitseinrichtung-Modell."""

    def test_encounter_valid(self, valid_encounter_dict: dict):
        """Ein vollständiges ISiK-Encounter-JSON wird erfolgreich validiert."""
        encounter = Encounter.model_validate(valid_encounter_dict)
        assert encounter.resourceType == "Encounter"
        assert encounter.status == "finished"
        assert encounter.class_.code == "IMP"
        assert encounter.subject.reference == "Patient/pat-12345"
        assert encounter.type is not None
        assert encounter.serviceType is not None
        assert encounter.location is not None
        assert encounter.hospitalization is not None

    def test_encounter_class_alias_from_json(self, valid_encounter_dict: dict):
        """JSON-Key 'class' wird korrekt auf Python-Attribut 'class_' gemappt."""
        encounter = Encounter.model_validate(valid_encounter_dict)
        assert encounter.class_.system == "http://terminology.hl7.org/CodeSystem/v3-ActCode"
        assert encounter.class_.code == "IMP"

    def test_encounter_class_alias_to_json(self, valid_encounter_dict: dict):
        """Python 'class_' wird im JSON-Output als 'class' serialisiert."""
        encounter = Encounter.model_validate(valid_encounter_dict)
        output = json.loads(encounter.model_dump_json(by_alias=True, exclude_none=True))
        assert "class" in output
        assert "class_" not in output
        assert output["class"]["code"] == "IMP"

    def test_encounter_class_populate_by_name(self):
        """Encounter kann auch via class_=... in Python instanziiert werden."""
        encounter = Encounter(
            identifier=[
                Identifier(system="https://fhir.krankenhaus.de/sid/fallnummer", value="F-001")
            ],
            status="planned",
            class_=Coding(
                system="http://terminology.hl7.org/CodeSystem/v3-ActCode",
                code="AMB",
            ),
            subject=Reference(reference="Patient/1"),
        )
        assert encounter.class_.code == "AMB"

    def test_encounter_missing_required(self):
        """Fehlende Pflichtfelder lösen ValidationError aus."""
        with pytest.raises(ValidationError) as exc_info:
            Encounter.model_validate({"resourceType": "Encounter"})
        errors = exc_info.value.errors()
        missing_fields = {e["loc"][0] for e in errors}
        assert "identifier" in missing_fields
        assert "status" in missing_fields
        assert "subject" in missing_fields

    def test_encounter_roundtrip(self, valid_encounter_dict: dict):
        """JSON → Modell → JSON Roundtrip behält alle Felder bei."""
        encounter = Encounter.model_validate(valid_encounter_dict)
        output = json.loads(encounter.model_dump_json(by_alias=True, exclude_none=True))

        assert output["resourceType"] == "Encounter"
        assert output["status"] == "finished"
        assert output["class"]["code"] == "IMP"
        assert output["subject"]["reference"] == "Patient/pat-12345"
        assert output["serviceType"]["coding"][0]["code"] == "0100"
        assert output["location"][0]["location"]["display"] == "Station 3A"
        assert output["hospitalization"]["admitSource"]["coding"][0]["code"] == "E"
        assert output["diagnosis"][0]["condition"]["display"] == "Pneumonie"

    def test_encounter_default_meta(self):
        """Ohne explizites meta wird das ISiK-Encounter-Profil automatisch gesetzt."""
        encounter = Encounter(
            identifier=[
                Identifier(system="https://fhir.krankenhaus.de/sid/fallnummer", value="F-001")
            ],
            status="in-progress",
            class_=Coding(code="IMP"),
            subject=Reference(reference="Patient/1"),
        )
        assert encounter.meta.profile == [ISIK_ENCOUNTER_PROFILE]
