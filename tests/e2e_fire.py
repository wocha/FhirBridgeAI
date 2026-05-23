import json
import os

import requests

try:
    import pytest
except ModuleNotFoundError:
    pytest = None

API_URL = "http://localhost:8000/api/v1/documents"
API_KEY = os.getenv("TEST_API_KEY", "dev-key-set-via-env")
PAYLOAD_FILE = "test_payload.json"

# Legacy smoke script: this still targets the retired X-API-Key auth path.
SKIP_REASON = "Legacy API-key e2e script; migrate to JWT auth before enabling."
pytestmark = [pytest.mark.integration, pytest.mark.skip(reason=SKIP_REASON)] if pytest else ()


def test_legacy_e2e_fire_is_disabled() -> None:
    assert True


def main():
    payload_path = os.path.join(os.path.dirname(__file__), PAYLOAD_FILE)

    with open(payload_path, encoding="utf-8") as f:
        payload = json.load(f)

    import uuid

    payload["document_id"] = f"e2e-test-{uuid.uuid4()}"

    headers = {"Content-Type": "application/json", "X-API-Key": API_KEY}

    print(f"[*] Fire Request to {API_URL} ...")
    response = requests.post(API_URL, json=payload, headers=headers)

    print(f"[*] Response Status: {response.status_code}")
    try:
        print(f"[*] Response Body: {json.dumps(response.json(), indent=2)}")
    except Exception:
        print(f"[*] Response Body: {response.text}")


if __name__ == "__main__":
    main()
