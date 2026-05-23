"""
Test environment bootstrap for FhirBridgeAI.

This conftest.py runs BEFORE any test-module body code during pytest collection.
It overrides Docker Compose service URLs with test-safe defaults so that worker
modules can be imported without a live Postgres / RabbitMQ / Ollama instance.

Priority rules (pydantic-settings): env-vars > .env file > defaults.
Using os.environ.setdefault preserves any CI-supplied overrides.
"""

from __future__ import annotations

import os
import sys
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[1]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

try:
    import prometheus_client.registry as _prom_registry

    _orig_prometheus_register = _prom_registry.CollectorRegistry.register

    def _test_prometheus_register(self, collector):  # type: ignore[no-untyped-def]
        try:
            return _orig_prometheus_register(self, collector)
        except ValueError as exc:
            if "Duplicated timeseries" in str(exc):
                return None
            raise

    _prom_registry.CollectorRegistry.register = _test_prometheus_register
except Exception:
    pass

# --- Database ---
os.environ.setdefault("DATABASE_URL", "sqlite:///:memory:")

# --- RabbitMQ / Ollama ---
os.environ.setdefault("RABBITMQ_URL", "amqp://guest:guest@localhost:5672/")
os.environ.setdefault("OLLAMA_URL", "http://localhost:11434")

# --- MinIO / S3 claim-check defaults for worker imports ---
os.environ.setdefault("MINIO_ROOT_USER", "test-minio-user")
os.environ.setdefault("MINIO_ROOT_PASSWORD", "test-minio-password")

# --- ADR-020: Keycloak (defaults match config.py defaults, set for explicitness) ---
os.environ.setdefault("KEYCLOAK_URL", "http://localhost:8080")
os.environ.setdefault("KEYCLOAK_REALM", "fhirbridge")
os.environ.setdefault("KEYCLOAK_CLIENT_ID", "fhirbridge-api")

# Clear lru_cache on get_settings()
try:
    from fhirbridge.core.config import get_settings
    get_settings.cache_clear()
except Exception:
    pass

# ADR-019: PostgreSQL-only enforcement has moved into URL resolution and
# schema-version guards in the current runtime. Older release branches exposed
# validate_db_enum_state(); patch it only when that compatibility hook exists.
import fhirbridge.core.database as _fhir_db

_orig_validate = getattr(_fhir_db, "validate_db_enum_state", None)

if _orig_validate is not None:

    def _test_validate_db_enum_state(engine):  # type: ignore[no-untyped-def]
        if engine.dialect.name == "sqlite":
            return  # Skip for unit tests: SQLite has no pg_enum
        return _orig_validate(engine)

    _fhir_db.validate_db_enum_state = _test_validate_db_enum_state
