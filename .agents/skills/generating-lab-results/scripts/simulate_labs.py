import json
import random
from datetime import date
from pathlib import Path

from pydantic import BaseModel

from fhirbridge.models.kdl_document import LabParameter, LabResults


class ParameterMultiplier(BaseModel):
    """
    Defines how a parameter is multiplied when a disease is present,
    and what additional variance should be added.
    """
    multiplier: float
    variance: float = 0.1

class DiseaseMultiplier(BaseModel):
    """
    Defines the lab value multipliers for a set of related diagnoses.
    """
    diagnoses: list[str]
    effects: dict[str, ParameterMultiplier]

# Pre-defined multipliers for common simulated states.
DISEASE_MULTIPLIERS = [
    DiseaseMultiplier(
        diagnoses=["sepsis", "infektion", "pneumonie", "hwi", "appendizitis"],
        effects={
            "CRP": ParameterMultiplier(multiplier=10.0, variance=0.2),
            "Leukozyten": ParameterMultiplier(multiplier=2.5, variance=0.15),
            "Thrombozyten": ParameterMultiplier(multiplier=0.7, variance=0.1) # often lower in severe infections
        }
    ),
    DiseaseMultiplier(
        diagnoses=["anämie", "blutung", "hämolyse"],
        effects={
            "Hb": ParameterMultiplier(multiplier=0.6, variance=0.1)
        }
    ),
    DiseaseMultiplier(
        diagnoses=["niereninsuffizienz", "dehydratation", "exsikkose"],
        effects={
            "Kreatinin": ParameterMultiplier(multiplier=2.5, variance=0.15),
            "Kalium": ParameterMultiplier(multiplier=1.2, variance=0.05)
        }
    ),
    DiseaseMultiplier(
        diagnoses=["diabetes", "hyperglykämie"],
        effects={
            "Glukose": ParameterMultiplier(multiplier=2.0, variance=0.1)
        }
    )
]

def _load_base_labs() -> dict[str, dict]:
    file_path = Path(__file__).parent.parent / "templates" / "base_labs.json"
    with open(file_path, encoding="utf-8") as f:
        return json.load(f)

def generate_correlating_labs(
    active_diagnoses: list[str],
    patient_id: str = "P-UNKNOWN",
    patient_name: str = "Unbekannter Patient",
    fall_id: str = "F-UNKNOWN",
    document_date: str | None = None
) -> LabResults:
    """
    Algorithmically generates laboratory results (KDL LB120103) based on disease multipliers.
    Using Gaussian distribution to avoid exact numbers and create realistic variance over time.
    """
    if document_date is None:
        document_date = date.today().strftime("%d.%m.%Y")

    base_labs = _load_base_labs()

    # Calculate effective multipliers for each parameter based on all active diagnoses
    current_multipliers: dict[str, float] = {}
    current_variances: dict[str, float] = {}

    # Normalize input
    dx_lower_list = [dx.lower() for dx in active_diagnoses]

    for dx in dx_lower_list:
        for disease_multi in DISEASE_MULTIPLIERS:
            # Check if any keyword of the defined Multiplier matches the diagnosis
            if any(keyword in dx for keyword in disease_multi.diagnoses):
                for param, effect in disease_multi.effects.items():
                    # If multiple diagnoses affect the same param, we multiply the effects
                    current_multipliers[param] = current_multipliers.get(param, 1.0) * effect.multiplier
                    # Keep the maximum variance to ensure realism doesn't get scaled out of bounds
                    current_variances[param] = max(current_variances.get(param, 0.0), effect.variance)

    generated_params = []

    for param_name, defaults in base_labs.items():
        base_val = float(defaults["base_value"])
        min_h = defaults["min_healthy"]
        max_h = defaults["max_healthy"]
        unit = defaults["unit"]

        # Apply multipliers and standard variance (if healthy, e.g. 5% variance)
        multiplier = current_multipliers.get(param_name, 1.0)
        variance = current_variances.get(param_name, 0.05)

        target_val = base_val * multiplier

        # Add random gaussian noise
        final_val = random.gauss(target_val, target_val * variance)

        # Ensure biological minimums (e.g., CRP won't be < 0)
        final_val = max(0.01, final_val)

        # Formatting depending on unit
        if "G/l" in unit or "mg/l" in unit:
            val_str = f"{final_val:.1f}"
        elif "mg/dl" in unit:
             val_str = f"{final_val:.2f}"
        elif "mmol/l" in unit or "U/l" in unit:
             val_str = f"{final_val:.1f}"
        else:
            # Default fallback format
            val_str = f"{final_val:.1f}"

        generated_params.append(
            LabParameter(
                name=param_name,
                value=f"{val_str} {unit}",
                reference_range=f"{min_h}-{max_h}"
            )
        )

    # Return the validated LabResults Pydantic object
    return LabResults(
        kdl_code="LB120103",
        kdl_name="Laborbefund intern",
        patient_id=patient_id,
        patient_name=patient_name,
        fall_id=fall_id,
        document_date=document_date,
        parameters=generated_params
    )

if __name__ == "__main__":
    # Test execution / Demo
    print("--- Gesunder Patient ---")
    healthy_labs = generate_correlating_labs(["Gesund"])
    print(healthy_labs.model_dump_json(indent=2))

    print("\n--- Sepsis Patient ---")
    sepsis_labs = generate_correlating_labs(["Schwere Sepsis", "Niereninsuffizienz"])
    print(sepsis_labs.model_dump_json(indent=2))
