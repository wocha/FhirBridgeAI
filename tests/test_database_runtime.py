from __future__ import annotations

import asyncio

import pytest

from fhirbridge.core import database
from fhirbridge.core.database import (
    ReadModelState,
    _to_async_database_url,
    get_async_engine,
    get_or_create_read_model_async,
    get_sync_engine,
)

pytestmark = pytest.mark.smoke


class _ScalarResult:
    def __init__(self, value):
        self._value = value

    def scalar_one_or_none(self):
        return self._value


class _StubAsyncSession:
    def __init__(self, existing_projection: ReadModelState | None = None) -> None:
        self.existing_projection = existing_projection
        self.added: list[ReadModelState] = []
        self.flush_count = 0

    async def execute(self, _query):
        return _ScalarResult(self.existing_projection)

    def add(self, obj: ReadModelState) -> None:
        self.added.append(obj)

    async def flush(self) -> None:
        self.flush_count += 1


def test_sync_engine_rejects_sqlite_url() -> None:
    with pytest.raises(RuntimeError, match="PostgreSQL only"):
        get_sync_engine(database_url="sqlite:///runtime.db")


def test_async_engine_uses_asyncpg_driver() -> None:
    pytest.importorskip("asyncpg")
    engine = get_async_engine(database_url="postgresql://user:secret@example.test:5432/fhirbridge")
    try:
        assert engine.url.drivername == "postgresql+asyncpg"
    finally:
        asyncio.run(engine.dispose())


def test_async_engine_rewrites_sslmode_for_asyncpg() -> None:
    async_url = _to_async_database_url("postgresql://user:secret@example.test:5432/fhirbridge?sslmode=require")

    assert "postgresql+asyncpg://" in async_url
    assert "sslmode" not in async_url
    assert "ssl=require" in async_url


def test_verify_runtime_schema_async_delegates_to_migration_guard(monkeypatch: pytest.MonkeyPatch) -> None:
    called: dict[str, object] = {}

    async def _fake_verify(engine) -> int:
        called["engine"] = engine
        return 1

    monkeypatch.setattr(database, "verify_schema_version_async", _fake_verify)
    fake_engine = object()

    asyncio.run(database.verify_runtime_schema_async(fake_engine))  # type: ignore[arg-type]

    assert called["engine"] is fake_engine


def test_get_or_create_read_model_async_returns_existing_projection() -> None:
    projection = ReadModelState(projection_name="dashboard", job_id=7, required_version=3, visible_version=3, status="FHIR_GENERATED")
    session = _StubAsyncSession(existing_projection=projection)

    resolved = asyncio.run(get_or_create_read_model_async(session, job_id=7))  # type: ignore[arg-type]

    assert resolved is projection
    assert session.added == []
    assert session.flush_count == 0


def test_get_or_create_read_model_async_creates_projection_when_missing() -> None:
    session = _StubAsyncSession(existing_projection=None)

    projection = asyncio.run(get_or_create_read_model_async(session, job_id=11))  # type: ignore[arg-type]

    assert projection.job_id == 11
    assert projection.projection_name == "dashboard"
    assert session.added == [projection]
    assert session.flush_count == 1
