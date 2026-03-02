import json
import os

os.makedirs("data/synthea/fhir", exist_ok=True)

for i in range(1, 11):
    data = {
        "resourceType": "Bundle",
        "type": "collection",
        "entry": [
            {
                "resource": {
                    "resourceType": "Patient",
                    "name": [{"family": f"Muster{i}", "given": [f"Max{i}"]}],
                    "gender": "male",
                    "birthDate": f"1980-01-{i:02d}",
                }
            },
            {"resource": {"resourceType": "Condition", "code": {"text": "Hypertension"}}},
        ],
    }
    with open(f"data/synthea/fhir/patient_{i:02d}.json", "w") as f:
        json.dump(data, f, indent=2)

print("Created 10 dummy patients")
