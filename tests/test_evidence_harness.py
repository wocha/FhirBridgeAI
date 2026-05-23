from __future__ import annotations

from scripts.security import run_hardening_evidence


def test_hardening_evidence_suite_is_explicit_and_stable() -> None:
    assert run_hardening_evidence.LOCAL_PYTEST_SUITE == [
        "tests/test_evidence_harness.py",
        "tests/test_boundary_contracts.py",
        "tests/test_database_runtime.py",
        "tests/test_outbox_dispatcher.py",
        "tests/test_runtime_config.py",
        "tests/test_read_model_gate.py",
        "tests/test_qdrant_security.py",
        "tests/test_legacy_blockade.py",
        "tests/test_dashboard_read_model_endpoint.py",
        "tests/test_ingestion_saga_compensation.py",
        "tests/test_review_endpoint.py",
        "tests/test_architecture_guards.py",
        "tests/test_token_exchange.py",
        "tests/test_postgres_runtime_harness.py",
    ]


def test_hardening_evidence_writes_to_dated_security_artifact() -> None:
    assert run_hardening_evidence.EVIDENCE_PATH.name == "test-evidence-2026-03-15.md"
