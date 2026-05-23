from __future__ import annotations

import re
from pathlib import Path


WORKSPACE = Path(__file__).resolve().parents[1]
ACTIVE_RUNTIME_FILES = [
    WORKSPACE / "src/fhirbridge/ingestion/api.py",
    WORKSPACE / "src/fhirbridge/core/outbox_dispatcher.py",
    WORKSPACE / "src/fhirbridge/workers/ocr_worker.py",
    WORKSPACE / "src/fhirbridge/workers/llm_worker.py",
    WORKSPACE / "src/fhirbridge/workers/fhir_export_worker.py",
]
KAFKA_GUARDED_RUNTIME_FILES = [
    WORKSPACE / "src/fhirbridge/core/base_worker.py",
    WORKSPACE / "src/fhirbridge/core/auth.py",
    WORKSPACE / "src/fhirbridge/core/config.py",
    WORKSPACE / "src/fhirbridge/core/rabbitmq.py",
    WORKSPACE / "src/fhirbridge/core/outbox_dispatcher.py",
    WORKSPACE / "src/fhirbridge/core/database.py",
    WORKSPACE / "src/fhirbridge/core/telemetry.py",
    WORKSPACE / "src/fhirbridge/core/storage.py",
    WORKSPACE / "src/fhirbridge/core/failure_handling.py",
    WORKSPACE / "src/fhirbridge/core/llm.py",
    WORKSPACE / "src/fhirbridge/core/llm_client.py",
    WORKSPACE / "src/fhirbridge/core/anonymizer.py",
    WORKSPACE / "src/fhirbridge/core/read_models.py",
    WORKSPACE / "src/fhirbridge/core/s3_client.py",
    WORKSPACE / "src/fhirbridge/core/qdrant_security.py",
    WORKSPACE / "src/fhirbridge/core/semantic_chunking.py",
    WORKSPACE / "src/fhirbridge/core/icd10_matcher.py",
    WORKSPACE / "src/fhirbridge/core/pdf_engine.py",
    WORKSPACE / "src/fhirbridge/core/migrations.py",
    WORKSPACE / "src/fhirbridge/ingestion/api.py",
    WORKSPACE / "src/fhirbridge/workers/ocr_worker.py",
    WORKSPACE / "src/fhirbridge/workers/llm_worker.py",
    WORKSPACE / "src/fhirbridge/workers/fhir_export_worker.py",
]
SCALABLE_WORKERS = [
    WORKSPACE / "src/fhirbridge/workers/ocr_worker.py",
    WORKSPACE / "src/fhirbridge/workers/llm_worker.py",
    WORKSPACE / "src/fhirbridge/workers/fhir_export_worker.py",
]
LEGACY_PATHS = [
    WORKSPACE / "src/fhirbridge/workers/parse_ocr_to_fhir.py",
    WORKSPACE / "src/verify_export.py",
]
BLOCKED_RETIRED_STUBS = {
    *LEGACY_PATHS,
    WORKSPACE / "enqueue_test_jobs.py",
    WORKSPACE / "test_rmq.py",
    WORKSPACE / ".agents/skills/building-autonomous-dispatchers/scripts/db_worker.py",
    WORKSPACE / ".agents/skills/building-autonomous-dispatchers/scripts/mq_worker.py",
    WORKSPACE / ".agents/skills/orchestrating-clinical-scenarios/scripts/dispatch_documents.py",
}
REPO_GOVERNANCE_ROOTS = [
    WORKSPACE / ".agents/skills",
    WORKSPACE / "knowledge",
    WORKSPACE / "scripts",
]
HISTORICAL_ALLOWLIST_ROOTS = [
    WORKSPACE / "docs/adr",
]
PATTERN_SCANNER_ALLOWLIST = {
    WORKSPACE / "scripts/security/check_security_posture.py",
}
RUNTIME_MANIFESTS = [
    WORKSPACE / "pyproject.toml",
    WORKSPACE / "requirements_core.txt",
]
SHADOW_PIPELINE_DOC_ANCHORS = {
    WORKSPACE / "docs/adr/ADR-026-Destination-Scoped-Dual-Bus-Guardrails.md": {
        "runtime inactive guard": [r"runtime inactive", r"inactive by design", r"guardrail-only"],
        "destination-scoped outbox separation": [r"destination.{0,40}outbox record", r"outbox record.{0,40}destination"],
        "shared-fence prohibition": [r"shared claim", r"shared lease", r"shared publish", r"shared repair"],
        "RabbitMQ authority": [r"rabbitmq command semantics remain authoritative", r"operational rabbitmq command dispatch"],
    },
    WORKSPACE / "docs/adr/ADR-028-Research-Isolation-and-Advisory-Only-Retrieval.md": {
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
    WORKSPACE / "docs/adr/ADR-029-BSI-Audit-Ledger-Shadow-Pipeline-Anchoring.md": {
        "runtime inactive guard": [r"runtime inactive", r"inactive by design", r"guardrail-only"],
        "retention is not immutability": [r"retention.{0,40}not treated as immutability", r"retention.{0,40}does not create immutability"],
        "external anchor requirement": [r"external immutable anchor", r"independently auditable proof mechanism"],
        "repair and replay auditability": [
            r"repair.{0,120}replay",
            r"replay.{0,120}audit",
            r"repair.{0,120}audit",
        ],
        "no live verification claim": [r"no operational verification is claimed", r"requires separate runtime evidence"],
    },
    WORKSPACE / "docs/security/control-mapping.md": {
        "inactive by design": [r"inactive by design"],
        "audit-ledger coverage": [r"audit[- ]ledger"],
        "research-bridge coverage": [r"research[- ]bridge"],
    },
    WORKSPACE / "docs/security/threat-model.md": {
        "inactive by design": [r"inactive by design"],
        "audit-ledger coverage": [r"audit[- ]ledger"],
        "research-bridge coverage": [r"research[- ]bridge"],
    },
}
SHADOW_PIPELINE_DOC_SCAN_ROOTS = [
    WORKSPACE / "docs/adr",
    WORKSPACE / "docs/security",
]

SHADOW_PIPELINE_DOC_FORBIDDEN_PATTERNS = {
    "positive Kafka runtime claim": r"\bkafka\b.{0,40}\b(?:is|are|was|were|already|now|remains)\b.{0,20}\b(?:active|operational|running|enabled|deployed)\b",
    "positive live-evidence claim": r"\blive\s+kafka\s+(?:runtime\s+)?evidence\b.{0,40}\b(?:exists|captured|available|verified|proven)\b",
    "positive shadow-pipeline claim": r"\b(?:audit[- ]ledger|research[- ]bridge)\b.{0,40}\b(?:is|are|was|were|already|now|remains)\b.{0,20}\b(?:active|operational|running)\b",
    "operationally verified": r"\boperationally verified\b",
    "already operational": r"\balready operational\b",
}
RETIREMENT_MARKERS = ("retired", "not approved for runtime use")


def _read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def _is_retired_stub(path: Path, content: str) -> bool:
    if path not in BLOCKED_RETIRED_STUBS:
        return False
    lowered = content.lower()
    return all(marker in lowered for marker in RETIREMENT_MARKERS)


def _is_historical_allowlisted(path: Path) -> bool:
    return any(root == path or root in path.parents for root in HISTORICAL_ALLOWLIST_ROOTS)


def _is_pattern_scanner_allowlisted(path: Path) -> bool:
    return path in PATTERN_SCANNER_ALLOWLIST


def _iter_governed_paths() -> list[Path]:
    governed: list[Path] = []
    for root in REPO_GOVERNANCE_ROOTS:
        governed.extend(
            path
            for path in root.rglob("*")
            if path.is_file() and "__pycache__" not in path.parts and path.suffix in {".md", ".py", ".sh"}
        )
    governed.extend(BLOCKED_RETIRED_STUBS)
    return sorted(set(governed))


def _matches_any(text: str, patterns: list[str]) -> bool:
    return any(re.search(pattern, text, flags=re.IGNORECASE | re.DOTALL) for pattern in patterns)


def _iter_shadow_pipeline_docs() -> list[Path]:
    """Scan ALL .md files in doc roots, not only keyword-preselected ones."""
    docs: set[Path] = set(SHADOW_PIPELINE_DOC_ANCHORS.keys())
    for root in SHADOW_PIPELINE_DOC_SCAN_ROOTS:
        for path in root.glob("*.md"):
            docs.add(path)
    return sorted(docs)


def test_no_sync_db_session_in_async_runtime_paths() -> None:
    forbidden_tokens = [
        "session.query(",
        "get_session_factory(",
        "SessionFactory(",
        "with SessionFactory(",
        "init_db(",
    ]
    for path in ACTIVE_RUNTIME_FILES:
        content = _read(path)
        for token in forbidden_tokens:
            assert token not in content, f"sync DB token '{token}' found in {path}"


def test_no_runtime_create_all_in_active_paths() -> None:
    for path in ACTIVE_RUNTIME_FILES:
        content = _read(path)
        assert "create_all(" not in content, f"runtime DDL found in {path}"


def test_no_sqlite_runtime_fallbacks_or_dependencies() -> None:
    runtime_and_manifests = ACTIVE_RUNTIME_FILES + [
        WORKSPACE / "src/fhirbridge/core/database.py",
        WORKSPACE / "pyproject.toml",
        WORKSPACE / "requirements_core.txt",
    ]
    forbidden_snippets = [
        "sqlite://",
        "sqlite+aiosqlite://",
        "aiosqlite",
        "DEFAULT_DB_PATH",
    ]
    for path in runtime_and_manifests:
        content = _read(path)
        for snippet in forbidden_snippets:
            assert snippet not in content, f"SQLite fallback snippet '{snippet}' found in {path}"


def test_governed_repo_context_rejects_legacy_patterns() -> None:
    forbidden_patterns = [
        "sqlite://",
        "sqlite-backed",
        "aiosqlite",
        "create_all(",
        "default_exchange.publish",
        "guest:guest",
        "admin123",
        "minioadmin",
    ]

    for path in _iter_governed_paths():
        content = _read(path)
        if _is_historical_allowlisted(path):
            continue
        if _is_retired_stub(path, content):
            continue
        if _is_pattern_scanner_allowlisted(path):
            continue
        lowered = content.lower()
        for pattern in forbidden_patterns:
            assert pattern not in lowered, f"governed repo context contains forbidden pattern '{pattern}' in {path}"


def test_no_default_credentials_or_placeholders_in_active_runtime() -> None:
    forbidden_snippets = [
        "guest:guest",
        "admin123",
        'os.getenv("MINIO_ROOT_USER",',
        'os.getenv("MINIO_ROOT_PASSWORD",',
        'os.getenv("RABBITMQ_URL",',
        "CHANGE_ME_FHIR_BEARER_TOKEN",
    ]
    for path in ACTIVE_RUNTIME_FILES:
        content = _read(path)
        for snippet in forbidden_snippets:
            assert snippet not in content, f"default or fallback credential pattern '{snippet}' found in {path}"

    config_content = _read(WORKSPACE / "src/fhirbridge/core/config.py")
    assert 'rabbitmq_url: str = Field(default="", alias="RABBITMQ_URL")' in config_content
    assert 'minio_root_user: str = Field(default="", alias="MINIO_ROOT_USER")' in config_content
    assert 'minio_root_password: str = Field(default="", alias="MINIO_ROOT_PASSWORD")' in config_content
    assert 'fhir_server_url: str = Field(default="", alias="FHIR_SERVER_URL")' in config_content


def test_no_direct_multi_write_publish_in_active_stages() -> None:
    for path in SCALABLE_WORKERS + [WORKSPACE / "src/fhirbridge/ingestion/api.py"]:
        content = _read(path)
        assert "default_exchange.publish" not in content, f"direct broker publish still present in {path}"


def test_no_local_file_writes_in_scalable_workers() -> None:
    forbidden_tokens = ["with open(", ".write_text(", ".write_bytes(", "os.makedirs("]
    for path in SCALABLE_WORKERS:
        content = _read(path)
        for token in forbidden_tokens:
            assert token not in content, f"local file write token '{token}' found in {path}"


def test_dispatcher_contains_claim_lease_guards() -> None:
    dispatcher = _read(WORKSPACE / "src/fhirbridge/core/outbox_dispatcher.py")
    database = _read(WORKSPACE / "src/fhirbridge/core/database.py")

    assert "claim_pending_outbox_events_async" in dispatcher
    assert "renew_outbox_claim_async" in dispatcher
    assert "publish_attempt_id" in dispatcher
    assert "create_reconciliation_task_async" in dispatcher
    assert "quarantine_outbox_event_async" in dispatcher
    assert "OutboxEscalationFailure" in dispatcher
    assert "if escalated" in dispatcher
    assert "post_commit_failure" in dispatcher
    assert "claim_expires_at" in database
    assert "last_lease_renewed_at" in database
    assert "OutboxStatus.ESCALATED" in database
    assert "OutboxStatus.FATAL_ESCALATION_FAILED" in database
    assert "publish_attempt_id.is_(None)" in database
    assert "OutboxEvent.claim_token == claim_token" in database
    assert "OutboxEvent.publish_attempt_id == publish_attempt_id" in database
    assert "skip_locked=True" in database


def test_dashboard_gate_is_bound_to_backend_read_model() -> None:
    content = _read(WORKSPACE / "dashboard/app.py")
    assert "/api/v1/read-models/dashboard" in content
    assert "fetch_dashboard_read_model_state" in content
    assert "evaluate_materialized_version_gate" in content
    assert "visible_raw" not in content


def test_dashboard_manual_review_is_backend_mediated_only() -> None:
    content = _read(WORKSPACE / "dashboard/app.py")
    assert "/api/v1/manual-review/" in content
    forbidden_snippets = [
        "rabbitmq:5672",
        "postgres:5432",
        "minio:9000",
        "sqlalchemy",
        "aioboto3",
        "boto3",
    ]
    for snippet in forbidden_snippets:
        assert snippet not in content, f"dashboard manual review must stay backend-mediated, found '{snippet}'"


def test_retired_stubs_are_explicitly_blocked() -> None:
    for path in BLOCKED_RETIRED_STUBS:
        content = _read(path)
        assert _is_retired_stub(path, content), f"blocked stub is missing explicit retirement markers in {path}"


def test_governed_repo_context_includes_scripts_tree() -> None:
    governed_paths = _iter_governed_paths()
    assert WORKSPACE / "scripts/check_pipeline_status.py" in governed_paths
    assert WORKSPACE / "scripts/security/check_security_posture.py" in governed_paths
    assert WORKSPACE / "scripts/trigger_e2e_pipeline.py" in governed_paths


def test_pattern_scanner_scripts_are_explicitly_allowlisted() -> None:
    scanner_script = WORKSPACE / "scripts/security/check_security_posture.py"
    content = _read(scanner_script).lower()
    assert _is_pattern_scanner_allowlisted(scanner_script)
    assert "guest:guest" in content
    assert "admin123" in content


def test_fhir_export_path_requires_https_and_never_disables_verification() -> None:
    compose = _read(WORKSPACE / "docker-compose.yml").lower()
    config = _read(WORKSPACE / "src/fhirbridge/core/config.py").lower()
    worker = _read(WORKSPACE / "src/fhirbridge/workers/fhir_export_worker.py").lower()

    assert "fhir_server_url=${fhir_server_url:?" in compose
    assert "fhir_server_ca_bundle_path=/etc/ssl/certs/local-ca.pem" in compose
    assert "http://host.docker.internal" not in compose
    assert "must use https://" in config
    assert "host.docker.internal" in config
    assert "return true" not in config
    assert "verify=false" not in worker
    assert "settings.fhir_http_verify()" in worker
    assert "settings.fhir_http_verify()" in worker


def test_minio_runtime_path_requires_https_and_explicit_ca_validation() -> None:
    compose = _read(WORKSPACE / "docker-compose.yml").lower()
    config = _read(WORKSPACE / "src/fhirbridge/core/config.py").lower()
    storage = _read(WORKSPACE / "src/fhirbridge/core/storage.py").lower()

    assert "minio_url=https://minio.docker.localhost:9000" in compose
    assert "minio_ca_bundle_path=/etc/ssl/certs/local-ca.pem" in compose
    assert "http://minio:9000" not in compose
    assert 'minio_url: str = field(default="", alias="minio_url")' in config
    assert 'minio_ca_bundle_path: str = field(default="", alias="minio_ca_bundle_path")' in config
    assert "minio_url must use https://" in config
    assert "def minio_http_verify(" in config
    assert '"verify": settings.minio_http_verify()' in storage
    assert "settings.require_minio_url()" in storage


def test_ingestion_boundary_is_not_host_exposed_and_dashboard_api_path_is_tls_only() -> None:
    compose = _read(WORKSPACE / "docker-compose.yml").lower()
    dashboard = _read(WORKSPACE / "dashboard/app.py").lower()
    traefik = _read(WORKSPACE / "deploy/traefik/dynamic.yml").lower()
    ingestion_block = re.search(r"(?ms)^  ingestion-gateway:\n(.*?)(?:^  [a-z0-9-]+:|\Z)", compose)

    assert ingestion_block is not None

    assert "8000:8000" not in ingestion_block.group(1)
    assert "dashboard_api_base_url=https://ingestion-api.docker.localhost:8443" in compose
    assert "dashboard_api_ca_bundle_path=/etc/ssl/certs/local-ca.pem" in compose
    assert "must use https://" in dashboard
    assert "verify=api_ca_bundle_path" in dashboard
    assert "host(`ingestion.docker.localhost`)" in traefik
    assert "host(`ingestion-api.docker.localhost`)" not in traefik
    assert "https://ingestion-gateway:8443" in traefik


def test_internal_auth_refresh_is_dispatch_bound_not_ttl_only() -> None:
    config = _read(WORKSPACE / "src/fhirbridge/core/config.py")
    auth = _read(WORKSPACE / "src/fhirbridge/core/auth.py")
    dispatcher = _read(WORKSPACE / "src/fhirbridge/core/outbox_dispatcher.py")

    assert 'internal_auth_context_ttl_seconds: int = Field(default=300' in config
    assert "def reissue_bound_context(" in auth
    assert "allow_expired=True" in auth
    assert "reissue_bound_context(" in dispatcher


def test_export_worker_preserves_repair_artifacts_until_after_local_export_state() -> None:
    worker = _read(WORKSPACE / "src/fhirbridge/workers/fhir_export_worker.py")

    assert "delete_object(" not in worker
    assert "job.status = jobstatus.exported" in worker.lower()
    assert '"reason": "status_update_failed_after_fhir_commit"' in worker
    assert '"mapping_object_key": task.mapping.object_key' in worker
    assert '"processing_object_key": task.processing.object_key' in worker


def test_evidence_object_lock_is_hardwired_without_exception_language() -> None:
    compose = _read(WORKSPACE / "docker-compose.yml").lower()
    adr = _read(
        WORKSPACE / "docs/adr/ADR-027-Immutable-Evidence-Anchoring-and-Object-Lock-Exception.md"
    ).lower()
    control_mapping = _read(WORKSPACE / "docs/security/control-mapping.md").lower()
    threat_model = _read(WORKSPACE / "docs/security/threat-model.md").lower()
    ingestion = _read(WORKSPACE / "src/fhirbridge/ingestion/api.py").lower()

    assert "--with-lock" in compose
    assert "minio_object_lock_evidence" not in compose
    assert "objectlockmode" in ingestion
    assert "objectlockretainuntildate" in ingestion
    assert "_delete_claim_check_payload" not in ingestion
    assert "repair marker" in ingestion
    assert "object lock" in adr
    assert "time-boxed exception" not in adr
    assert "nicht nachweisbar" not in adr
    assert "object lock" in control_mapping
    assert "no runtime exception remains on the active evidence path" in control_mapping
    assert "orphan-evidence repair marker" in control_mapping
    assert "object lock" in threat_model
    assert "local evidence-bucket object lock remains" not in threat_model


def test_compose_does_not_activate_kafka_shadow_pipeline_services_or_env() -> None:
    compose = _read(WORKSPACE / "docker-compose.yml").lower()

    forbidden_service_patterns = [
        r"(?m)^  kafka:\s*$",
        r"(?m)^  zookeeper:\s*$",
        r"(?m)^  schema-registry:\s*$",
        r"(?m)^  redpanda:\s*$",
        r"(?m)^  kafdrop:\s*$",
    ]
    forbidden_snippets = [
        "9092:9092",
        "29092:29092",
        "kafka://",
        "bootstrap_servers",
        "schema_registry",
        "kafka_",
    ]

    for pattern in forbidden_service_patterns:
        assert re.search(pattern, compose) is None, f"forbidden Kafka compose service activated: {pattern}"
    for snippet in forbidden_snippets:
        assert snippet not in compose, f"forbidden Kafka compose activation snippet '{snippet}' found"


def test_active_runtime_and_manifests_remain_kafka_free() -> None:
    forbidden_runtime_tokens = [
        "kafka",
        "aiokafka",
        "confluent_kafka",
        "kafkaproducer",
        "kafkaconsumer",
        "aiokafkaproducer",
        "aiokafkaconsumer",
    ]
    forbidden_manifest_tokens = [
        "aiokafka",
        "confluent-kafka",
        "confluent_kafka",
        "kafka-python",
    ]

    for path in KAFKA_GUARDED_RUNTIME_FILES:
        content = _read(path).lower()
        for token in forbidden_runtime_tokens:
            assert token not in content, f"forbidden Kafka runtime token '{token}' found in {path}"

    for path in RUNTIME_MANIFESTS:
        content = _read(path).lower()
        for token in forbidden_manifest_tokens:
            assert token not in content, f"forbidden Kafka manifest token '{token}' found in {path}"


def test_outbox_dispatch_path_remains_rabbitmq_only_without_dual_bus_mix() -> None:
    dispatcher = _read(WORKSPACE / "src/fhirbridge/core/outbox_dispatcher.py").lower()
    database = _read(WORKSPACE / "src/fhirbridge/core/database.py").lower()

    assert "class rabbitmqpublisher" in dispatcher
    assert "get_rabbitmq_connection" in dispatcher
    assert "aio_pika" in dispatcher
    assert "kafka" not in dispatcher
    assert "kafka" not in database
    assert "destinations =" not in database
    assert "destinations_json" not in database


def test_shadow_pipeline_docs_require_inactive_guardrails_and_no_live_claims() -> None:
    for path, anchor_groups in SHADOW_PIPELINE_DOC_ANCHORS.items():
        content = _read(path).lower()
        for anchor_name, patterns in anchor_groups.items():
            assert _matches_any(content, patterns), f"required shadow-pipeline anchor '{anchor_name}' missing in {path}"

    for path in _iter_shadow_pipeline_docs():
        content = _read(path).lower()
        for label, pattern in SHADOW_PIPELINE_DOC_FORBIDDEN_PATTERNS.items():
            assert re.search(pattern, content, flags=re.IGNORECASE | re.DOTALL) is None, (
                f"forbidden Kafka overclaim '{label}' found in {path}"
            )


def test_security_posture_script_has_render_only_compose_placeholders() -> None:
    content = _read(WORKSPACE / "scripts/security/check_security_posture.py").lower()

    assert "compose_render_placeholders" in content
    assert "render-only" in content
    for env_name in (
        "internal_auth_context_secret",
        "minio_root_user",
        "minio_root_password",
        "fhir_auth_bearer",
        "fhir_server_url",
    ):
        assert env_name in content, f"compose render placeholder missing for {env_name}"


def test_compose_raw_text_blocks_unsafe_defaults_for_security_vars() -> None:
    """Compose must use :? (required) not :- (default) for security-critical vars."""
    compose_text = _read(WORKSPACE / "docker-compose.yml")
    guarded_vars = [
        "FHIR_SERVER_URL",
        "INTERNAL_AUTH_CONTEXT_SECRET",
        "MINIO_ROOT_USER",
        "MINIO_ROOT_PASSWORD",
        "FHIR_AUTH_BEARER",
    ]
    for var in guarded_vars:
        assert f"${{{var}:-" not in compose_text, (
            f"docker-compose uses unsafe :- default for {var}"
        )
        assert f"${{{var}: -" not in compose_text, (
            f"docker-compose uses unsafe : - default for {var}"
        )
