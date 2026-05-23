#!/usr/bin/env python
"""Static security assertions for hardened deploy assets and active runtime code."""

from __future__ import annotations

import json
import os
import re
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
DEFAULT_COMPOSE_PATH = ROOT / "docker-compose.yml"
COMPOSE_PATH = Path(os.getenv("SECURITY_COMPOSE_FILE", str(DEFAULT_COMPOSE_PATH))).resolve()
DYNAMIC_TRAEFIK_PATH = ROOT / "deploy" / "traefik" / "dynamic.yml"
ACTIVE_RUNTIME_SOURCE_PATHS = [
    ROOT / "src" / "fhirbridge" / "ingestion" / "api.py",
    ROOT / "src" / "fhirbridge" / "core" / "outbox_dispatcher.py",
    ROOT / "src" / "fhirbridge" / "workers" / "ocr_worker.py",
    ROOT / "src" / "fhirbridge" / "workers" / "llm_worker.py",
    ROOT / "src" / "fhirbridge" / "workers" / "fhir_export_worker.py",
]
KAFKA_GUARDED_RUNTIME_SOURCE_PATHS = [
    ROOT / "src" / "fhirbridge" / "core" / "base_worker.py",
    ROOT / "src" / "fhirbridge" / "core" / "auth.py",
    ROOT / "src" / "fhirbridge" / "core" / "config.py",
    ROOT / "src" / "fhirbridge" / "core" / "rabbitmq.py",
    ROOT / "src" / "fhirbridge" / "core" / "outbox_dispatcher.py",
    ROOT / "src" / "fhirbridge" / "core" / "database.py",
    ROOT / "src" / "fhirbridge" / "core" / "telemetry.py",
    ROOT / "src" / "fhirbridge" / "core" / "storage.py",
    ROOT / "src" / "fhirbridge" / "core" / "failure_handling.py",
    ROOT / "src" / "fhirbridge" / "core" / "llm.py",
    ROOT / "src" / "fhirbridge" / "core" / "llm_client.py",
    ROOT / "src" / "fhirbridge" / "core" / "anonymizer.py",
    ROOT / "src" / "fhirbridge" / "core" / "read_models.py",
    ROOT / "src" / "fhirbridge" / "core" / "s3_client.py",
    ROOT / "src" / "fhirbridge" / "core" / "qdrant_security.py",
    ROOT / "src" / "fhirbridge" / "core" / "semantic_chunking.py",
    ROOT / "src" / "fhirbridge" / "core" / "icd10_matcher.py",
    ROOT / "src" / "fhirbridge" / "core" / "pdf_engine.py",
    ROOT / "src" / "fhirbridge" / "core" / "migrations.py",
    ROOT / "src" / "fhirbridge" / "ingestion" / "api.py",
    ROOT / "src" / "fhirbridge" / "workers" / "ocr_worker.py",
    ROOT / "src" / "fhirbridge" / "workers" / "llm_worker.py",
    ROOT / "src" / "fhirbridge" / "workers" / "fhir_export_worker.py",
]
RUNTIME_MANIFEST_PATHS = [
    ROOT / "pyproject.toml",
    ROOT / "requirements_core.txt",
]
SHADOW_PIPELINE_DOC_ANCHORS = {
    ROOT / "docs" / "adr" / "ADR-026-Destination-Scoped-Dual-Bus-Guardrails.md": {
        "runtime inactive guard": [r"runtime inactive", r"inactive by design", r"guardrail-only"],
        "destination-scoped outbox separation": [
            r"destination.{0,40}outbox record",
            r"outbox record.{0,40}destination",
        ],
        "shared-fence prohibition": [r"shared claim", r"shared lease", r"shared publish", r"shared repair"],
        "RabbitMQ authority": [
            r"rabbitmq command semantics remain authoritative",
            r"operational rabbitmq command dispatch",
        ],
    },
    ROOT / "docs" / "adr" / "ADR-028-Research-Isolation-and-Advisory-Only-Retrieval.md": {
        "runtime inactive guard": [r"runtime inactive", r"inactive by design", r"guardrail-only"],
        "research bridge scope": [r"research[- ]bridge"],
        "one-way isolation": [r"one-way", r"one way"],
        "no return path": [r"no return path", r"no backchannel", r"kein rueckkanal"],
        "separate security domain": [
            r"separate credentials.{0,120}separate tenant",
            r"separate credentials.{0,120}incident model",
            r"separate tenant.{0,120}incident model",
        ],
        "advisory-only retrieval": [r"advisory-only", r"advisory only"],
    },
    ROOT / "docs" / "adr" / "ADR-029-BSI-Audit-Ledger-Shadow-Pipeline-Anchoring.md": {
        "runtime inactive guard": [r"runtime inactive", r"inactive by design", r"guardrail-only"],
        "retention is not immutability": [
            r"retention.{0,40}not treated as immutability",
            r"retention.{0,40}does not create immutability",
        ],
        "external anchor requirement": [
            r"external immutable anchor",
            r"independently auditable proof mechanism",
        ],
        "repair and replay auditability": [
            r"repair.{0,120}replay",
            r"replay.{0,120}audit",
            r"repair.{0,120}audit",
        ],
        "no live verification claim": [
            r"no operational verification is claimed",
            r"requires separate runtime evidence",
        ],
    },
    ROOT / "docs" / "security" / "control-mapping.md": {
        "inactive by design": [r"inactive by design"],
        "audit-ledger coverage": [r"audit[- ]ledger"],
        "research-bridge coverage": [r"research[- ]bridge"],
    },
    ROOT / "docs" / "security" / "threat-model.md": {
        "inactive by design": [r"inactive by design"],
        "audit-ledger coverage": [r"audit[- ]ledger"],
        "research-bridge coverage": [r"research[- ]bridge"],
    },
}
SHADOW_PIPELINE_DOC_SCAN_ROOTS = [
    ROOT / "docs" / "adr",
    ROOT / "docs" / "security",
]

SHADOW_PIPELINE_DOC_FORBIDDEN_PATTERNS = {
    "positive Kafka runtime claim": r"\bkafka\b.{0,40}\b(?:is|are|was|were|already|now|remains)\b.{0,20}\b(?:active|operational|running|enabled|deployed)\b",
    "positive live-evidence claim": r"\blive\s+kafka\s+(?:runtime\s+)?evidence\b.{0,40}\b(?:exists|captured|available|verified|proven)\b",
    "positive shadow-pipeline claim": r"\b(?:audit[- ]ledger|research[- ]bridge)\b.{0,40}\b(?:is|are|was|were|already|now|remains)\b.{0,20}\b(?:active|operational|running)\b",
    "operationally verified": r"\boperationally verified\b",
    "already operational": r"\balready operational\b",
}
COMPOSE_RENDER_PLACEHOLDERS = {
    # Render-only placeholders let `docker compose config` resolve required vars
    # for static analysis without claiming that these values are safe for runtime.
    "INTERNAL_AUTH_CONTEXT_SECRET": "render-only-static-analysis-secret-0123456789",
    "MINIO_ROOT_USER": "render-only-minio-user",
    "MINIO_ROOT_PASSWORD": "render-only-minio-password",
    "FHIR_AUTH_BEARER": "render-only-fhir-bearer-token",
    "FHIR_SERVER_URL": "https://render-only.invalid/fhir",
}
GOVERNED_SCRIPT_ROOTS = [
    ROOT / "scripts",
]
GOVERNED_SCRIPT_ALLOWLIST = {
    ROOT / "scripts" / "security" / "check_security_posture.py",
}
GOVERNED_SCRIPT_SUFFIXES = {".py", ".md", ".sh"}
GOVERNED_SCRIPT_FORBIDDEN_PATTERNS = [
    "sqlite://",
    "aiosqlite",
    "create_all(",
    "default_exchange.publish",
    "guest:guest",
    "admin123",
    "minioadmin",
]
KAFKA_FORBIDDEN_DEPENDENCY_TOKENS = [
    "aiokafka",
    "confluent-kafka",
    "confluent_kafka",
    "kafka-python",
]
KAFKA_FORBIDDEN_RUNTIME_TOKENS = [
    "kafka",
    "aiokafka",
    "confluent_kafka",
    "kafkaproducer",
    "kafkaconsumer",
    "aiokafkaproducer",
    "aiokafkaconsumer",
]
KAFKA_FORBIDDEN_SERVICE_TOKENS = [
    "kafka",
    "zookeeper",
    "schema-registry",
    "redpanda",
    "kafdrop",
]


def _compose_cmd() -> list[str]:
    cmd = ["docker", "compose"]
    if COMPOSE_PATH != DEFAULT_COMPOSE_PATH:
        cmd.extend(["-f", str(COMPOSE_PATH)])
    return cmd


def _compose_render_env() -> dict[str, str]:
    env = os.environ.copy()
    for key, value in COMPOSE_RENDER_PLACEHOLDERS.items():
        env.setdefault(key, value)
    return env


def load_compose() -> dict:
    output = subprocess.check_output(
        [*_compose_cmd(), "config", "--format", "json"],
        text=True,
        env=_compose_render_env(),
    )
    return json.loads(output)


def check_realm_export() -> list[str]:
    issues: list[str] = []
    realm_path = ROOT / "deploy" / "keycloak" / "realm-export.json"
    realm = json.loads(realm_path.read_text(encoding="utf-8"))

    for client in realm.get("clients", []):
        secret = client.get("secret")
        if isinstance(secret, str) and secret.strip():
            issues.append("realm-export.json still contains non-empty client secret")

    for user in realm.get("users", []):
        for cred in user.get("credentials", []) or []:
            if isinstance(cred, dict) and cred.get("value"):
                issues.append("realm-export.json still contains plaintext user credential value")

    return issues


def check_oauth2_cfg() -> list[str]:
    issues: list[str] = []
    cfg_path = ROOT / "deploy" / "oauth2-proxy" / "oauth2-proxy.cfg"
    text = cfg_path.read_text(encoding="utf-8")

    if "ssl_insecure_skip_verify = true" in text:
        issues.append("oauth2-proxy.cfg has ssl_insecure_skip_verify=true")

    insecure_oidc_urls = re.findall(
        r'\b(?:login_url|redeem_url|profile_url|oidc_jwks_url|oidc_issuer_url)\s*=\s*"http://',
        text,
    )
    if insecure_oidc_urls:
        issues.append("oauth2-proxy.cfg still uses HTTP OIDC endpoints")

    return issues


def _env_keys(env: object) -> set[str]:
    if isinstance(env, list):
        return {entry.split("=", 1)[0] for entry in env if isinstance(entry, str) and "=" in entry}
    if isinstance(env, dict):
        return set(env.keys())
    return set()


def _net_keys(value: object) -> set[str]:
    if isinstance(value, list):
        return {str(v) for v in value}
    if isinstance(value, dict):
        return {str(v) for v in value.keys()}
    return set()


def _volume_sources_and_targets(volumes: object) -> list[tuple[str, str]]:
    pairs: list[tuple[str, str]] = []
    if not isinstance(volumes, list):
        return pairs

    for entry in volumes:
        if isinstance(entry, dict):
            src = str(entry.get("source", ""))
            tgt = str(entry.get("target", ""))
            pairs.append((src, tgt))
        elif isinstance(entry, str):
            parts = entry.split(":")
            if len(parts) >= 2:
                pairs.append((parts[0], parts[1]))

    return pairs


def _command_text(value: object) -> str:
    if isinstance(value, list):
        return " ".join(str(x) for x in value)
    return str(value or "")


def _matches_any(text: str, patterns: list[str]) -> bool:
    return any(re.search(pattern, text, flags=re.IGNORECASE | re.DOTALL) for pattern in patterns)


def _iter_shadow_pipeline_docs() -> list[Path]:
    """Scan ALL .md files in doc roots, not only keyword-preselected ones."""
    docs: set[Path] = set(SHADOW_PIPELINE_DOC_ANCHORS.keys())
    for root in SHADOW_PIPELINE_DOC_SCAN_ROOTS:
        for path in root.glob("*.md"):
            docs.add(path)
    return sorted(docs)


def check_socketless_traefik(compose: dict) -> list[str]:
    issues: list[str] = []
    services = compose.get("services", {})
    traefik = services.get("traefik", {})

    command_text = _command_text(traefik.get("command", [])).lower()

    if re.search(r"--providers\.docker(?:\b|[.=])", command_text):
        issues.append("traefik docker provider is enabled; socketless mode requires file provider only")

    if "--providers.file.filename=/etc/traefik/dynamic.yml" not in command_text:
        issues.append("traefik file provider is missing expected dynamic.yml binding")

    for src, tgt in _volume_sources_and_targets(traefik.get("volumes", [])):
        joined = f"{src} {tgt}".lower()
        if "docker.sock" in joined:
            issues.append("traefik still mounts docker.sock")
            break

    return issues


def check_dynamic_traefik_file() -> list[str]:
    issues: list[str] = []

    if not DYNAMIC_TRAEFIK_PATH.exists():
        return [f"dynamic traefik file missing: {DYNAMIC_TRAEFIK_PATH}"]

    text = DYNAMIC_TRAEFIK_PATH.read_text(encoding="utf-8")

    required_snippets = [
        "Host(`dashboard.docker.localhost`)",
        "Host(`keycloak.docker.localhost`)",
        "Host(`grafana.docker.localhost`)",
        "Host(`ingestion.docker.localhost`)",
        "http://oauth2-proxy:4180",
        "http://keycloak:8080",
        "http://grafana:3000",
        "https://ingestion-gateway:8443",
        "ingestion-upstream",
        "/etc/traefik/certs/rootCA.pem",
        "strip-auth-headers",
        "X-Forwarded-User",
        "X-Forwarded-Groups",
        "X-Forwarded-Email",
        "X-Forwarded-Preferred-Username",
        "X-Auth-Request-User",
        "X-Auth-Request-Email",
        "X-Auth-Request-Groups",
        "Authorization",
    ]

    for snippet in required_snippets:
        if snippet not in text:
            issues.append(f"dynamic traefik config missing required snippet: {snippet}")

    return issues


def check_no_obsolete_traefik_labels(compose: dict) -> list[str]:
    issues: list[str] = []
    services = compose.get("services", {})

    for service_name in ("oauth2-proxy", "keycloak", "grafana"):
        labels = services.get(service_name, {}).get("labels")
        if labels:
            issues.append(f"{service_name} still defines Traefik labels; routing must be file-provider only")

    return issues


def check_compose_security(compose: dict, compose_text: str) -> list[str]:
    issues: list[str] = []
    services = compose.get("services", {})

    traefik_cmd = _command_text(services.get("traefik", {}).get("command", [])).lower()
    if "--api.insecure=true" in traefik_cmd:
        issues.append("traefik command still includes --api.insecure=true")

    traefik_image = str(services.get("traefik", {}).get("image", ""))
    if ":latest" in traefik_image:
        issues.append("traefik image is not pinned (uses latest)")

    for svc_name in ("keycloak", "keycloak-bootstrap"):
        image = str(services.get(svc_name, {}).get("image", ""))
        if ":latest" in image:
            issues.append(f"{svc_name} image is not pinned (uses latest)")

    if "${API_KEY_SECRET:-" in compose_text:
        issues.append("docker-compose still has fallback default for API_KEY_SECRET")
    if "${MINIO_ROOT_USER:-" in compose_text:
        issues.append("docker-compose still has fallback default for MINIO_ROOT_USER")
    if "${MINIO_ROOT_PASSWORD:-" in compose_text:
        issues.append("docker-compose still has fallback default for MINIO_ROOT_PASSWORD")
    if "${FHIR_AUTH_BEARER:-" in compose_text:
        issues.append("docker-compose still has fallback default for FHIR_AUTH_BEARER")
    if "${FHIR_AUTH_BEARER:?" not in compose_text:
        issues.append("docker-compose must require FHIR_AUTH_BEARER for the export worker")
    if "${FHIR_SERVER_URL:-" in compose_text:
        issues.append("docker-compose still has fallback default for FHIR_SERVER_URL")
    if "${INTERNAL_AUTH_CONTEXT_SECRET:-" in compose_text:
        issues.append("docker-compose still has fallback default for INTERNAL_AUTH_CONTEXT_SECRET")

    dashboard = services.get("dashboard", {})
    dashboard_env_keys = _env_keys(dashboard.get("environment", {}))

    forbidden_dashboard_keys = {
        "RABBITMQ_MANAGEMENT_URL",
        "RABBITMQ_DEFAULT_USER",
        "RABBITMQ_DEFAULT_PASS",
        "POSTGRES_USER",
        "POSTGRES_PASSWORD",
        "DATABASE_URL",
    }
    leaked = sorted(forbidden_dashboard_keys.intersection(dashboard_env_keys))
    if leaked:
        issues.append(f"dashboard service still has forbidden credential env keys: {leaked}")

    dashboard_nets = _net_keys(dashboard.get("networks", {}))
    if "observability" in dashboard_nets:
        issues.append("dashboard is still attached to observability network")
    if "metrics_read" not in dashboard_nets:
        issues.append("dashboard is missing metrics_read network")
    allowed_dashboard_nets = {"frontend", "metrics_read", "frontend_api"}
    extra_nets = sorted(dashboard_nets.difference(allowed_dashboard_nets))
    if extra_nets:
        issues.append(f"dashboard has unnecessary network attachments: {extra_nets}")

    prometheus_nets = _net_keys(services.get("prometheus", {}).get("networks", {}))
    if "metrics_read" not in prometheus_nets:
        issues.append("prometheus is missing metrics_read network")

    ingestion = services.get("ingestion-gateway", {})
    ingestion_nets = _net_keys(ingestion.get("networks", {}))
    if "frontend_api" not in ingestion_nets:
        issues.append("ingestion-gateway is missing frontend_api network for read-model policy calls")
    if ingestion.get("ports"):
        issues.append("ingestion-gateway must not publish a host port")

    ingestion_command = _command_text(ingestion.get("command", [])).lower()
    if "--ssl-certfile" not in ingestion_command or "--ssl-keyfile" not in ingestion_command:
        issues.append("ingestion-gateway command must enforce internal TLS with explicit certificate files")

    bootstrap_env = services.get("keycloak-bootstrap", {}).get("environment", {})
    bootstrap_url = ""
    if isinstance(bootstrap_env, dict):
        bootstrap_url = str(bootstrap_env.get("KEYCLOAK_BOOTSTRAP_URL", "")).strip()
    if bootstrap_url.lower().startswith("http://"):
        issues.append("keycloak-bootstrap still uses HTTP admin bootstrap URL")
    if not bootstrap_url.lower().startswith("https://"):
        issues.append("keycloak-bootstrap URL is not HTTPS")

    dashboard_env = services.get("dashboard", {}).get("environment", {})
    dashboard_api_url = ""
    dashboard_ca_bundle = ""
    if isinstance(dashboard_env, dict):
        dashboard_api_url = str(dashboard_env.get("DASHBOARD_API_BASE_URL", "")).strip()
        dashboard_ca_bundle = str(dashboard_env.get("DASHBOARD_API_CA_BUNDLE_PATH", "")).strip()
    if not dashboard_api_url.lower().startswith("https://"):
        issues.append("dashboard must call the ingestion API over HTTPS only")
    if not dashboard_ca_bundle:
        issues.append("dashboard is missing explicit DASHBOARD_API_CA_BUNDLE_PATH for API TLS validation")

    fhir_export_env = services.get("fhir-export-worker", {}).get("environment", {})
    fhir_server_url = ""
    if isinstance(fhir_export_env, dict):
        fhir_server_url = str(fhir_export_env.get("FHIR_SERVER_URL", "")).strip()
    if fhir_server_url.lower().startswith("http://"):
        issues.append("FHIR export worker still uses a plaintext FHIR_SERVER_URL")
    if "host.docker.internal" in fhir_server_url.lower():
        issues.append("FHIR export worker must not target host.docker.internal")

    if "MINIO_OBJECT_LOCK_EVIDENCE" in compose_text:
        issues.append("docker-compose must not expose an Object Lock bypass toggle")
    if "--with-lock" not in compose_text:
        issues.append("docker-compose must create the evidence bucket with Object Lock enabled")

    return issues


def check_kafka_runtime_inactivity(compose: dict, compose_text: str) -> list[str]:
    issues: list[str] = []
    services = compose.get("services", {})

    for service_name, service in services.items():
        lowered_name = str(service_name).lower()
        if any(token in lowered_name for token in KAFKA_FORBIDDEN_SERVICE_TOKENS):
            issues.append(f"docker-compose activates forbidden Kafka-related service '{service_name}'")

        image = str(service.get("image", "")).lower()
        if any(token in image for token in KAFKA_FORBIDDEN_SERVICE_TOKENS):
            issues.append(
                f"docker-compose uses forbidden Kafka-related image '{image}' for service '{service_name}'"
            )

        command_text = _command_text(service.get("command", [])).lower()
        if "kafka" in command_text:
            issues.append(f"docker-compose command for service '{service_name}' contains Kafka activation text")

        env_keys = {key.upper() for key in _env_keys(service.get("environment", {}))}
        forbidden_env_keys = sorted(
            key
            for key in env_keys
            if key.startswith("KAFKA")
            or "BOOTSTRAP_SERVERS" in key
            or "SCHEMA_REGISTRY" in key
        )
        if forbidden_env_keys:
            issues.append(
                f"docker-compose service '{service_name}' exposes forbidden Kafka env keys: {forbidden_env_keys}"
            )

    compose_lower = compose_text.lower()
    forbidden_compose_snippets = [
        "9092:9092",
        "29092:29092",
        "kafka://",
        "bootstrap_servers",
        "schema_registry",
    ]
    for snippet in forbidden_compose_snippets:
        if snippet in compose_lower:
            issues.append(f"docker-compose contains forbidden Kafka activation snippet '{snippet}'")

    return issues


def check_bootstrap_script() -> list[str]:
    issues: list[str] = []
    bootstrap_path = ROOT / "deploy" / "keycloak" / "bootstrap.sh"
    text = bootstrap_path.read_text(encoding="utf-8")

    if "http://keycloak:8080" in text:
        issues.append("bootstrap.sh still contains HTTP Keycloak admin endpoint")

    if "insecure KEYCLOAK_BOOTSTRAP_URL is forbidden" not in text:
        issues.append("bootstrap.sh lacks explicit HTTP bootstrap deny control")

    if "trustStore" not in text and "truststore" not in text:
        issues.append("bootstrap.sh lacks explicit TLS truststore configuration")

    return issues


def check_active_runtime_source_guards() -> list[str]:
    issues: list[str] = []
    forbidden_snippets = [
        "guest:guest",
        "admin123",
        'os.getenv("MINIO_ROOT_USER",',
        'os.getenv("MINIO_ROOT_PASSWORD",',
        'os.getenv("RABBITMQ_URL",',
        "visible_raw",
        "required_raw",
        "verify=False",
        "http://host.docker.internal",
    ]

    for path in ACTIVE_RUNTIME_SOURCE_PATHS:
        text = path.read_text(encoding="utf-8")
        for snippet in forbidden_snippets:
            if snippet in text:
                issues.append(f"active runtime source still contains forbidden snippet '{snippet}' in {path}")

    dashboard_text = (ROOT / "dashboard" / "app.py").read_text(encoding="utf-8")
    if "/api/v1/read-models/dashboard" not in dashboard_text:
        issues.append("dashboard is not bound to the backend read-model endpoint")
    if "DASHBOARD_API_BASE_URL must use https://" not in dashboard_text:
        issues.append("dashboard lacks an explicit HTTPS-only API guard")
    if "verify=API_CA_BUNDLE_PATH" not in dashboard_text:
        issues.append("dashboard API client is missing explicit CA validation")

    ingestion_text = (ROOT / "src" / "fhirbridge" / "ingestion" / "api.py").read_text(encoding="utf-8")
    if "ObjectLockMode" not in ingestion_text or "ObjectLockRetainUntilDate" not in ingestion_text:
        issues.append("ingestion boundary is missing explicit evidence object-lock writes")

    return issues


def check_kafka_free_runtime_code_and_manifests() -> list[str]:
    issues: list[str] = []

    for path in KAFKA_GUARDED_RUNTIME_SOURCE_PATHS:
        lowered = path.read_text(encoding="utf-8").lower()
        for token in KAFKA_FORBIDDEN_RUNTIME_TOKENS:
            if token in lowered:
                issues.append(f"active runtime source contains forbidden Kafka token '{token}' in {path}")

    for path in RUNTIME_MANIFEST_PATHS:
        lowered = path.read_text(encoding="utf-8").lower()
        for token in KAFKA_FORBIDDEN_DEPENDENCY_TOKENS:
            if token in lowered:
                issues.append(f"runtime manifest contains forbidden Kafka dependency token '{token}' in {path}")

    return issues


def _iter_governed_script_paths() -> list[Path]:
    paths: set[Path] = set()
    for root in GOVERNED_SCRIPT_ROOTS:
        if not root.exists():
            continue
        for path in root.rglob("*"):
            if path.is_file() and "__pycache__" not in path.parts and path.suffix in GOVERNED_SCRIPT_SUFFIXES:
                paths.add(path)
    return sorted(paths)


def check_governed_script_context() -> list[str]:
    issues: list[str] = []
    for path in _iter_governed_script_paths():
        if path in GOVERNED_SCRIPT_ALLOWLIST:
            continue
        text = path.read_text(encoding="utf-8").lower()
        for pattern in GOVERNED_SCRIPT_FORBIDDEN_PATTERNS:
            if pattern in text:
                issues.append(f"governed script context contains forbidden pattern '{pattern}' in {path}")
    return issues


def check_shadow_pipeline_docs() -> list[str]:
    issues: list[str] = []

    for path, anchor_groups in SHADOW_PIPELINE_DOC_ANCHORS.items():
        text = path.read_text(encoding="utf-8").lower()
        for anchor_name, patterns in anchor_groups.items():
            if not _matches_any(text, patterns):
                issues.append(f"shadow-pipeline doc missing required anchor '{anchor_name}' in {path}")

    for path in _iter_shadow_pipeline_docs():
        text = path.read_text(encoding="utf-8").lower()
        for label, pattern in SHADOW_PIPELINE_DOC_FORBIDDEN_PATTERNS.items():
            if re.search(pattern, text, flags=re.IGNORECASE | re.DOTALL):
                issues.append(f"shadow-pipeline doc contains forbidden Kafka overclaim '{label}' in {path}")

    return issues


def main() -> int:
    failures: list[str] = []

    compose_text = COMPOSE_PATH.read_text(encoding="utf-8")
    compose = load_compose()

    failures.extend(check_compose_security(compose, compose_text))
    failures.extend(check_kafka_runtime_inactivity(compose, compose_text))
    failures.extend(check_socketless_traefik(compose))
    failures.extend(check_dynamic_traefik_file())
    failures.extend(check_no_obsolete_traefik_labels(compose))
    failures.extend(check_oauth2_cfg())
    failures.extend(check_realm_export())
    failures.extend(check_bootstrap_script())
    failures.extend(check_active_runtime_source_guards())
    failures.extend(check_kafka_free_runtime_code_and_manifests())
    failures.extend(check_governed_script_context())
    failures.extend(check_shadow_pipeline_docs())

    if failures:
        print("Security checks failed:")
        for failure in failures:
            print(f"- {failure}")
        return 1

    print("Security checks passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())


