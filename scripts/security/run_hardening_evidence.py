"""Run the reproducible hardening evidence suite and write a dated evidence artifact."""

from __future__ import annotations

import os
import subprocess
import sys
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
EVIDENCE_PATH = ROOT / "docs" / "security" / "test-evidence-2026-03-15.md"
LOCAL_PYTEST_SUITE = [
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


@dataclass(slots=True)
class CommandResult:
    name: str
    command: list[str]
    returncode: int
    stdout: str
    stderr: str


def _run_command(name: str, command: list[str], *, extra_env: dict[str, str] | None = None) -> CommandResult:
    env = os.environ.copy()
    if extra_env:
        env.update(extra_env)
    completed = subprocess.run(
        command,
        cwd=ROOT,
        capture_output=True,
        text=True,
        env=env,
        check=False,
    )
    return CommandResult(
        name=name,
        command=command,
        returncode=completed.returncode,
        stdout=completed.stdout.strip(),
        stderr=completed.stderr.strip(),
    )


def _format_command(command: list[str]) -> str:
    return " ".join(f'"{part}"' if " " in part else part for part in command)


def _render_result(result: CommandResult) -> str:
    lines = [
        f"## {result.name}",
        "",
        "Command:",
        "```text",
        _format_command(result.command),
        "```",
        "",
        f"Exit code: `{result.returncode}`",
        "",
        "Stdout:",
        "```text",
        result.stdout or "<empty>",
        "```",
    ]
    if result.stderr:
        lines.extend(
            [
                "",
                "Stderr:",
                "```text",
                result.stderr,
                "```",
            ]
        )
    return "\n".join(lines)


def _write_evidence(results: list[CommandResult]) -> None:
    timestamp = datetime.now(UTC).strftime("%Y-%m-%d %H:%M:%SZ")
    content = [
        "# Test Evidence 2026-03-15",
        "",
        "## Evidence Entry-Point",
        "",
        "Run this harness to reproduce the evidence below:",
        "```text",
        _format_command([sys.executable, str(Path(__file__).resolve())]),
        "```",
        "",
        f"Generated at: `{timestamp}`",
        "",
        "## Local Pytest Suite",
        "",
        "Files:",
        *[f"- `{path}`" for path in LOCAL_PYTEST_SUITE],
        "",
        "## Optional Live Harness",
        "",
        "- `tests/test_postgres_runtime_harness.py` is part of the standard pytest command.",
        "- If `TEST_DATABASE_URL` is unset, those live PostgreSQL harness tests are expected to skip and remain `nicht nachweisbar` for live execution.",
        "",
    ]
    for result in results:
        content.append(_render_result(result))
        content.append("")

    EVIDENCE_PATH.write_text("\n".join(content).rstrip() + "\n", encoding="utf-8")


def main() -> int:
    pytest_result = _run_command(
        "Pytest Hardening Suite",
        [sys.executable, "-m", "pytest", *LOCAL_PYTEST_SUITE, "-q"],
    )
    posture_result = _run_command(
        "Security Posture Check",
        [sys.executable, "scripts/security/check_security_posture.py"],
        extra_env={
            "INTERNAL_AUTH_CONTEXT_SECRET": "abcdefghijklmnopqrstuvwxyz1234567890ABCDEF",
            "MINIO_ROOT_USER": "miniooperator",
            "MINIO_ROOT_PASSWORD": "MinioStrongPass!234",
            "FHIR_SERVER_URL": "https://fhir.example.internal/fhir",
            "FHIR_AUTH_BEARER": "FhirBearerStrong123456",
            "POSTGRES_USER": "pg_user_test",
            "POSTGRES_PASSWORD": "PgStrongPass!234",
            "POSTGRES_DB": "fhirbridge",
            "DATABASE_URL": "postgresql://pg_user_test:PgStrongPass!234@postgres:5432/fhirbridge?sslmode=require",
            "RABBITMQ_DEFAULT_USER": "mq_admin_test",
            "RABBITMQ_DEFAULT_PASS": "MqStrongPass!234",
        },
    )

    results = [pytest_result, posture_result]
    _write_evidence(results)

    for result in results:
        print(f"[{result.name}] exit={result.returncode}")
        if result.stdout:
            print(result.stdout)
        if result.stderr:
            print(result.stderr)

    return 0 if all(result.returncode == 0 for result in results) else 1


if __name__ == "__main__":
    raise SystemExit(main())
