from __future__ import annotations

import pytest

from fhirbridge.workers import parse_ocr_to_fhir
from verify_export import main as verify_export_main

pytestmark = pytest.mark.smoke


def test_parse_ocr_to_fhir_legacy_path_is_blocked() -> None:
    with pytest.raises(SystemExit):
        parse_ocr_to_fhir.main()


def test_verify_export_legacy_path_is_blocked() -> None:
    with pytest.raises(SystemExit):
        verify_export_main()
