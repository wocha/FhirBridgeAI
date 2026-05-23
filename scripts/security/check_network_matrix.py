#!/usr/bin/env python
"""Runtime network segmentation checks with static preflight and optional live probes."""

from __future__ import annotations

import re
import ssl
import subprocess
from dataclasses import dataclass
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
COMPOSE_TEXT = (ROOT / "docker-compose.yml").read_text(encoding="utf-8")


@dataclass(frozen=True)
class MatrixRule:
    source_service: str
    target_host: str
    port: int
    should_allow: bool
    rationale: str
    http_path: str | None = None
    scheme: str = "http"
    ca_bundle_path: str | None = None


RULES: list[MatrixRule] = [
    MatrixRule(
        source_service="dashboard",
        target_host="prometheus",
        port=9090,
        should_allow=True,
        rationale="Dashboard must read queue metrics via Prometheus only.",
        http_path="/-/healthy",
    ),
    MatrixRule(
        source_service="dashboard",
        target_host="ingestion-api.docker.localhost",
        port=8443,
        should_allow=True,
        rationale="Dashboard must reach the backend review/read-model API only over the dedicated internal TLS path on frontend_api.",
        http_path="/openapi.json",
        scheme="https",
        ca_bundle_path="/etc/ssl/certs/local-ca.pem",
    ),
    MatrixRule(
        source_service="dashboard",
        target_host="rabbitmq",
        port=5672,
        should_allow=False,
        rationale="Dashboard must not access broker plane.",
    ),
    MatrixRule(
        source_service="dashboard",
        target_host="postgres",
        port=5432,
        should_allow=False,
        rationale="Dashboard must not access pipeline database.",
    ),
    MatrixRule(
        source_service="dashboard",
        target_host="jaeger",
        port=16686,
        should_allow=False,
        rationale="Dashboard must not access broader observability control-plane.",
    ),
    MatrixRule(
        source_service="dashboard",
        target_host="grafana",
        port=3000,
        should_allow=False,
        rationale="Dashboard must not access Grafana service directly.",
    ),
    MatrixRule(
        source_service="dashboard",
        target_host="keycloak",
        port=8080,
        should_allow=False,
        rationale="Dashboard must not access Keycloak service directly.",
    ),
    MatrixRule(
        source_service="ingestion-gateway",
        target_host="rabbitmq",
        port=5672,
        should_allow=True,
        rationale="Ingestion must publish to RabbitMQ.",
    ),
]


def _static_failures() -> list[str]:
    issues: list[str] = []
    if re.search(r"(?ms)^\s{2}ingestion-gateway:\n.*?^\s{4}ports:\n", COMPOSE_TEXT):
        issues.append("ingestion-gateway still publishes a host port")
    if "DASHBOARD_API_BASE_URL=https://ingestion-api.docker.localhost:8443" not in COMPOSE_TEXT:
        issues.append("dashboard API base URL is not pinned to the dedicated internal HTTPS hostname")
    if "DASHBOARD_API_CA_BUNDLE_PATH=/etc/ssl/certs/local-ca.pem" not in COMPOSE_TEXT:
        issues.append("dashboard is missing an explicit CA bundle for API TLS")
    if "Host(`ingestion-api.docker.localhost`)" in (ROOT / "deploy" / "traefik" / "dynamic.yml").read_text(encoding="utf-8"):
        issues.append("traefik must not route the dedicated internal dashboard API hostname")
    if "FHIR_SERVER_URL=${FHIR_SERVER_URL:?FHIR_SERVER_URL is required}" not in COMPOSE_TEXT:
        issues.append("FHIR export worker does not require an explicit HTTPS FHIR_SERVER_URL")
    if "FHIR_SERVER_CA_BUNDLE_PATH=/etc/ssl/certs/local-ca.pem" not in COMPOSE_TEXT:
        issues.append("FHIR export worker is missing the explicit CA bundle path")
    if "http://host.docker.internal" in COMPOSE_TEXT.lower():
        issues.append("compose still contains host.docker.internal plaintext fallback")
    if "http://minio:9000" in COMPOSE_TEXT.lower():
        issues.append("compose still contains plaintext MinIO traffic")
    return issues


def _running_services() -> set[str]:
    result = subprocess.run(
        ["docker", "compose", "ps", "--services", "--status", "running"],
        text=True,
        capture_output=True,
        check=True,
    )
    return {line.strip() for line in result.stdout.splitlines() if line.strip()}


def _exec_python(service: str, code: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["docker", "compose", "exec", "-T", service, "python", "-c", code],
        text=True,
        capture_output=True,
    )


def _tcp_probe(service: str, host: str, port: int, timeout_seconds: int = 3) -> bool:
    code = (
        "import socket,sys; "
        f"sock=socket.socket(); sock.settimeout({timeout_seconds}); "
        "ok=True; "
        "\ntry:\n"
        f"    sock.connect(('{host}', {port}))\n"
        "except Exception:\n"
        "    ok=False\n"
        "finally:\n"
        "    sock.close()\n"
        "sys.exit(0 if ok else 1)"
    )
    result = _exec_python(service, code)
    return result.returncode == 0


def _http_probe(
    service: str,
    url: str,
    *,
    timeout_seconds: int = 3,
    ca_bundle_path: str | None = None,
) -> bool:
    ssl_setup = ""
    opener_target = "urllib.request.urlopen"
    if url.lower().startswith("https://") and ca_bundle_path:
        ssl_setup = (
            "import ssl; "
            f"ctx=ssl.create_default_context(cafile='{ca_bundle_path}'); "
        )
        opener_target = "lambda target, timeout: urllib.request.urlopen(target, timeout=timeout, context=ctx)"

    code = (
        "import sys,urllib.request; "
        f"{ssl_setup}"
        f"opener={opener_target}; "
        f"resp=opener('{url}', timeout={timeout_seconds}); "
        "sys.exit(0 if 200 <= resp.status < 400 else 1)"
    )
    result = _exec_python(service, code)
    return result.returncode == 0


def main() -> int:
    failures: list[str] = []
    output: list[str] = []

    static_failures = _static_failures()
    for issue in static_failures:
        output.append(f"[FAIL] static guard: {issue}")
    if static_failures:
        print("\n".join(output))
        print("\nStatic network guard validation failed:")
        for issue in static_failures:
            print(f"- {issue}")
        return 1

    output.append("[PASS] static guard: ingestion host port removed, dashboard path pinned to dedicated internal TLS, and plaintext MinIO blocked")

    try:
        running = _running_services()
    except subprocess.CalledProcessError as exc:
        print("\n".join(output))
        print("\nLive network matrix not executed:")
        stderr = (exc.stderr or "").strip() or (exc.stdout or "").strip() or "docker compose ps returned no details"
        print(f"- {stderr}")
        return 1

    for rule in RULES:
        if rule.source_service not in running:
            failures.append(f"Source service not running: {rule.source_service}")
            output.append(f"[FAIL] {rule.source_service} -> {rule.target_host}:{rule.port} source not running")
            continue

        tcp_allowed = _tcp_probe(rule.source_service, rule.target_host, rule.port)
        effective_allow = tcp_allowed

        http_ok = None
        if rule.should_allow and rule.http_path:
            http_ok = _http_probe(
                rule.source_service,
                f"{rule.scheme}://{rule.target_host}:{rule.port}{rule.http_path}",
                ca_bundle_path=rule.ca_bundle_path,
            )
            effective_allow = tcp_allowed and http_ok

        passed = effective_allow == rule.should_allow
        status = "PASS" if passed else "FAIL"

        evidence = f"tcp={'open' if tcp_allowed else 'closed'}"
        if http_ok is not None:
            evidence += f", http={'ok' if http_ok else 'fail'}"

        output.append(
            f"[{status}] {rule.source_service} -> {rule.target_host}:{rule.port} "
            f"expected={'allow' if rule.should_allow else 'deny'} ({evidence})"
        )

        if not passed:
            failures.append(rule.rationale)

    print("\n".join(output))

    if failures:
        print("\nRuntime network matrix validation failed:")
        for issue in failures:
            print(f"- {issue}")
        return 1

    print("\nRuntime network matrix validation passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

