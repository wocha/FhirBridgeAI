from __future__ import annotations

from pathlib import Path
from urllib.parse import urlparse

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


PLACEHOLDER_VALUES = {
    "",
    "change_me",
    "change_me_min_32_bytes",
    "change_me_base64",
    "replace_me",
    "set_me",
    "todo",
}
FORBIDDEN_RABBITMQ_CREDENTIALS = {("guest", "guest")}
FORBIDDEN_MINIO_CREDENTIALS = {("admin", "admin123"), ("minioadmin", "minioadmin")}
FORBIDDEN_FHIR_EXPORT_HOSTS = {"host.docker.internal", "localhost", "127.0.0.1"}
FORBIDDEN_INTERNAL_TLS_HOSTS = {"host.docker.internal", "localhost", "127.0.0.1"}


class ConfigurationError(RuntimeError):
    """Raised when the runtime configuration violates security policy."""


def _normalize(value: str) -> str:
    return value.strip()


def _is_placeholder(value: str) -> bool:
    return _normalize(value).lower() in PLACEHOLDER_VALUES


def _require_value(value: str, *, env_name: str) -> str:
    normalized = _normalize(value)
    if not normalized:
        raise ConfigurationError(f"{env_name} is required")
    if _is_placeholder(normalized):
        raise ConfigurationError(f"{env_name} must not use placeholder content")
    return normalized


def _require_secret(value: str, *, env_name: str, minimum_length: int = 1) -> str:
    normalized = _require_value(value, env_name=env_name)
    if len(normalized) < minimum_length:
        raise ConfigurationError(f"{env_name} must be at least {minimum_length} characters")
    return normalized


def _require_existing_file(value: str, *, env_name: str) -> str:
    normalized = _require_value(value, env_name=env_name)
    path = Path(normalized)
    if not path.is_file():
        raise ConfigurationError(f"{env_name} must point to an existing file")
    return str(path)


class Settings(BaseSettings):
    database_url: str = Field(default="", alias="DATABASE_URL")
    rabbitmq_url: str = Field(default="", alias="RABBITMQ_URL")
    ollama_url: str = Field(default="http://127.0.0.1:11434", alias="OLLAMA_URL")
    keycloak_url: str = Field(default="", alias="KEYCLOAK_URL")
    keycloak_realm: str = Field(default="", alias="KEYCLOAK_REALM")
    keycloak_client_id: str = Field(default="", alias="KEYCLOAK_CLIENT_ID")
    keycloak_jwks_url: str = Field(default="", alias="KEYCLOAK_JWKS_URL")
    internal_auth_context_secret: str = Field(default="", alias="INTERNAL_AUTH_CONTEXT_SECRET")
    internal_auth_context_ttl_seconds: int = Field(default=300, alias="INTERNAL_AUTH_CONTEXT_TTL_SECONDS")
    broker_retry_initial_delay_ms: int = Field(default=5000, alias="BROKER_RETRY_INITIAL_DELAY_MS")
    broker_retry_max_delay_ms: int = Field(default=300000, alias="BROKER_RETRY_MAX_DELAY_MS")
    minio_url: str = Field(default="", alias="MINIO_URL")
    minio_ca_bundle_path: str = Field(default="", alias="MINIO_CA_BUNDLE_PATH")
    minio_root_user: str = Field(default="", alias="MINIO_ROOT_USER")
    minio_root_password: str = Field(default="", alias="MINIO_ROOT_PASSWORD")
    minio_evidence_bucket: str = Field(default="evidence-originals", alias="MINIO_EVIDENCE_BUCKET")
    minio_processing_bucket: str = Field(default="processing-artifacts", alias="MINIO_PROCESSING_BUCKET")
    minio_phi_vault_bucket: str = Field(default="phi-vault", alias="MINIO_PHI_VAULT_BUCKET")
    minio_evidence_retention_days: int = Field(default=30, alias="MINIO_EVIDENCE_RETENTION_DAYS")
    fhir_server_url: str = Field(default="", alias="FHIR_SERVER_URL")
    fhir_server_ca_bundle_path: str = Field(default="", alias="FHIR_SERVER_CA_BUNDLE_PATH")
    fhir_auth_bearer: str = Field(default="", alias="FHIR_AUTH_BEARER")
    qdrant_url: str = Field(default="", alias="QDRANT_URL")
    qdrant_collection: str = Field(default="", alias="QDRANT_COLLECTION")
    qdrant_read_api_key: str = Field(default="", alias="QDRANT_READ_API_KEY")
    qdrant_write_api_key: str = Field(default="", alias="QDRANT_WRITE_API_KEY")

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    def require_database_url(self) -> str:
        return _require_value(self.database_url, env_name="DATABASE_URL")

    def require_rabbitmq_url(self) -> str:
        url = _require_value(self.rabbitmq_url, env_name="RABBITMQ_URL")
        parsed = urlparse(url)
        username = parsed.username or ""
        password = parsed.password or ""
        if not username or not password:
            raise ConfigurationError("RABBITMQ_URL must embed explicit non-empty credentials")
        if (username, password) in FORBIDDEN_RABBITMQ_CREDENTIALS:
            raise ConfigurationError("RABBITMQ_URL must not use the default guest credentials")
        if _is_placeholder(username) or _is_placeholder(password):
            raise ConfigurationError("RABBITMQ_URL must not use placeholder credentials")
        return url

    def require_internal_auth_context_secret(self) -> str:
        return _require_secret(
            self.internal_auth_context_secret,
            env_name="INTERNAL_AUTH_CONTEXT_SECRET",
            minimum_length=32,
        )

    def require_minio_credentials(self) -> tuple[str, str]:
        username = _require_value(self.minio_root_user, env_name="MINIO_ROOT_USER")
        password = _require_secret(
            self.minio_root_password,
            env_name="MINIO_ROOT_PASSWORD",
            minimum_length=12,
        )
        if (username, password) in FORBIDDEN_MINIO_CREDENTIALS:
            raise ConfigurationError("MINIO_ROOT credentials must not use the documented defaults")
        if username.lower() in {"admin", "minioadmin"}:
            raise ConfigurationError("MINIO_ROOT_USER must not use a default administrator name")
        return username, password

    def require_minio_url(self) -> str:
        url = _require_value(self.minio_url, env_name="MINIO_URL")
        parsed = urlparse(url)
        if parsed.scheme.lower() != "https":
            raise ConfigurationError("MINIO_URL must use https://")
        if not parsed.netloc:
            raise ConfigurationError("MINIO_URL must include a host")
        hostname = (parsed.hostname or "").lower()
        if hostname in FORBIDDEN_INTERNAL_TLS_HOSTS:
            raise ConfigurationError("MINIO_URL must not target local development hosts")
        return url

    def minio_http_verify(self) -> str:
        self.require_minio_url()
        return _require_existing_file(self.minio_ca_bundle_path, env_name="MINIO_CA_BUNDLE_PATH")

    def object_storage_buckets(self) -> tuple[str, str, str]:
        return (
            _require_value(self.minio_evidence_bucket, env_name="MINIO_EVIDENCE_BUCKET"),
            _require_value(self.minio_processing_bucket, env_name="MINIO_PROCESSING_BUCKET"),
            _require_value(self.minio_phi_vault_bucket, env_name="MINIO_PHI_VAULT_BUCKET"),
        )

    def evidence_retention_days(self) -> int:
        if self.minio_evidence_retention_days < 1:
            raise ConfigurationError("MINIO_EVIDENCE_RETENTION_DAYS must be at least 1")
        return int(self.minio_evidence_retention_days)

    def require_fhir_server_url(self) -> str:
        url = _require_value(self.fhir_server_url, env_name="FHIR_SERVER_URL")
        parsed = urlparse(url)
        if parsed.scheme.lower() != "https":
            raise ConfigurationError("FHIR_SERVER_URL must use https://")
        if not parsed.netloc:
            raise ConfigurationError("FHIR_SERVER_URL must include a host")
        hostname = (parsed.hostname or "").lower()
        if hostname in FORBIDDEN_FHIR_EXPORT_HOSTS:
            raise ConfigurationError("FHIR_SERVER_URL must not target local development hosts")
        return url

    def fhir_http_verify(self) -> str:
        self.require_fhir_server_url()
        return _require_existing_file(
            self.fhir_server_ca_bundle_path,
            env_name="FHIR_SERVER_CA_BUNDLE_PATH",
        )

    def require_fhir_auth_bearer(self) -> str:
        return _require_secret(
            self.fhir_auth_bearer,
            env_name="FHIR_AUTH_BEARER",
            minimum_length=16,
        )

    def require_qdrant_credentials(self) -> tuple[str, str]:
        read_key = _require_secret(
            self.qdrant_read_api_key,
            env_name="QDRANT_READ_API_KEY",
            minimum_length=16,
        )
        write_key = _require_secret(
            self.qdrant_write_api_key,
            env_name="QDRANT_WRITE_API_KEY",
            minimum_length=16,
        )
        if read_key == write_key:
            raise ConfigurationError("Qdrant read and write API keys must be distinct")
        return read_key, write_key


def get_settings() -> Settings:
    return Settings()
