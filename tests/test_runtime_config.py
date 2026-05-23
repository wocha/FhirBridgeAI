from __future__ import annotations

import pytest

from fhirbridge.core.config import ConfigurationError, Settings

pytestmark = pytest.mark.smoke


def test_rabbitmq_default_credentials_fail_fast() -> None:
    settings = Settings(RABBITMQ_URL="amqp://guest:guest@rabbitmq:5672/")

    with pytest.raises(ConfigurationError):
        settings.require_rabbitmq_url()


def test_minio_default_credentials_fail_fast() -> None:
    settings = Settings(
        MINIO_ROOT_USER="admin",
        MINIO_ROOT_PASSWORD="admin123",
    )

    with pytest.raises(ConfigurationError):
        settings.require_minio_credentials()


def test_fhir_auth_placeholder_fails_fast() -> None:
    settings = Settings(FHIR_AUTH_BEARER="CHANGE_ME")

    with pytest.raises(ConfigurationError):
        settings.require_fhir_auth_bearer()


def test_fhir_server_url_requires_https_and_non_local_host() -> None:
    settings = Settings(FHIR_SERVER_URL="http://host.docker.internal:8080/fhir")

    with pytest.raises(ConfigurationError):
        settings.require_fhir_server_url()


def test_minio_url_requires_https_and_non_local_host() -> None:
    settings = Settings(MINIO_URL="http://host.docker.internal:9000")

    with pytest.raises(ConfigurationError):
        settings.require_minio_url()


def test_minio_ca_bundle_is_mandatory_and_must_exist(tmp_path) -> None:
    missing_bundle = tmp_path / "missing-minio-ca.pem"
    settings = Settings(
        MINIO_URL="https://minio.docker.localhost:9000",
        MINIO_CA_BUNDLE_PATH=str(missing_bundle),
    )

    with pytest.raises(ConfigurationError):
        settings.minio_http_verify()


def test_minio_ca_bundle_is_mandatory_when_url_is_configured() -> None:
    settings = Settings(
        MINIO_URL="https://minio.docker.localhost:9000",
        MINIO_CA_BUNDLE_PATH="",
    )

    with pytest.raises(ConfigurationError):
        settings.minio_http_verify()


def test_fhir_server_ca_bundle_is_mandatory_when_url_is_configured() -> None:
    settings = Settings(
        FHIR_SERVER_URL="https://fhir.example.internal/fhir",
        FHIR_SERVER_CA_BUNDLE_PATH="",
    )

    with pytest.raises(ConfigurationError):
        settings.fhir_http_verify()


def test_fhir_server_ca_bundle_is_mandatory_and_must_exist(tmp_path) -> None:
    missing_bundle = tmp_path / "missing-ca.pem"
    settings = Settings(
        FHIR_SERVER_URL="https://fhir.example.internal/fhir",
        FHIR_SERVER_CA_BUNDLE_PATH=str(missing_bundle),
    )

    with pytest.raises(ConfigurationError):
        settings.fhir_http_verify()


def test_qdrant_keys_must_be_distinct() -> None:
    settings = Settings(
        QDRANT_READ_API_KEY="x" * 24,
        QDRANT_WRITE_API_KEY="x" * 24,
    )

    with pytest.raises(ConfigurationError):
        settings.require_qdrant_credentials()
