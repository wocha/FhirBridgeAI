import pytest
from pydantic import ValidationError

from fhirbridge.models.clinical_base import SYSTEM_KVNR_GKV, ISiKObservation
from fhirbridge.models.fhir_models import Encounter, Patient


def test_patient_valid_kvnr():
    patient_data = {
        "identifier": [{"system": SYSTEM_KVNR_GKV, "value": "A123456789"}],
        "name": [{"family": "Mustermann", "given": ["Max"]}],
        "gender": "male",
        "birthDate": "1990-01-01",
    }
    patient = Patient(**patient_data)
    assert patient.identifier[0].value == "A123456789"


def test_patient_invalid_kvnr():
    patient_data = {
        "identifier": [
            {"system": SYSTEM_KVNR_GKV, "value": "123456789"}  # Fehlt der führende Buchstabe
        ],
        "name": [{"family": "Mustermann"}],
        "gender": "male",
        "birthDate": "1990-01-01",
    }
    with pytest.raises(ValidationError) as exc:
        Patient(**patient_data)
    assert "Ungültige KVNR" in str(exc.value)


def test_patient_missing_family_name():
    patient_data = {
        "identifier": [{"system": SYSTEM_KVNR_GKV, "value": "A123456789"}],
        "name": [{"given": ["Max"]}],  # Kein family name
        "gender": "male",
        "birthDate": "1990-01-01",
    }
    with pytest.raises(ValidationError) as exc:
        Patient(**patient_data)
    assert "mindestens einen Nachnamen" in str(exc.value)


def test_encounter_missing_vn():
    encounter_data = {
        "identifier": [{"system": "http://example.org", "value": "123"}],
        "status": "finished",
        "class": {"system": "http://terminology.hl7.org/CodeSystem/v3-ActCode", "code": "IMP"},
        "subject": {"reference": "Patient/1"},
    }
    with pytest.raises(ValidationError) as exc:
        Encounter(**encounter_data)
    assert "zwingend eine Fallnummer" in str(exc.value)


def test_encounter_valid_vn():
    encounter_data = {
        "identifier": [
            {
                "type": {
                    "coding": [
                        {"system": "http://terminology.hl7.org/CodeSystem/v2-0203", "code": "VN"}
                    ]
                },
                "value": "FALL-123",
            }
        ],
        "status": "finished",
        "class": {"system": "http://terminology.hl7.org/CodeSystem/v3-ActCode", "code": "IMP"},
        "subject": {"reference": "Patient/1"},
    }
    enc = Encounter(**encounter_data)
    assert enc.status == "finished"


def test_observation_exclusive_values():
    obs_data = {
        "status": "final",
        "category": [
            {
                "coding": [
                    {
                        "system": "http://terminology.hl7.org/CodeSystem/observation-category",
                        "code": "laboratory",
                    }
                ]
            }
        ],
        "code": {"coding": [{"system": "http://loinc.org", "code": "718-7"}]},
        "subject": {"reference": "Patient/1"},
        "effectiveDateTime": "2023-10-10T10:00:00Z",
        "valueQuantity": {"value": 12.5, "unit": "g/dL"},
        "valueString": "Erhöht",  # Ungültig, weil valueQuantity bereits gesetzt ist
    }
    with pytest.raises(ValidationError) as exc:
        ISiKObservation(**obs_data)
    assert "maximal einen value[x]" in str(exc.value)


def test_observation_valid():
    obs_data = {
        "status": "final",
        "category": [
            {
                "coding": [
                    {
                        "system": "http://terminology.hl7.org/CodeSystem/observation-category",
                        "code": "laboratory",
                    }
                ]
            }
        ],
        "code": {"coding": [{"system": "http://loinc.org", "code": "718-7"}]},
        "subject": {"reference": "Patient/1"},
        "effectiveDateTime": "2023-10-10T10:00:00Z",
        "valueQuantity": {"value": 12.5, "unit": "g/dL"},
    }
    obs = ISiKObservation(**obs_data)
    assert obs.valueQuantity["value"] == 12.5
