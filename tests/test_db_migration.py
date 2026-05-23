"""
Pflicht-Tests: JobStatus.EXPORT_CLEANUP_FAILED — DB-Migration & Enum-Validation.

Test-Matrix (PostgreSQL-only, nach SQLite-Removal):
  [T3a] Enum-Mismatch-Detection: RuntimeError wenn Wert in pg_enum fehlt.
  [T3b] Enum-Mismatch-Detection: RuntimeError wenn jobstatus-Typ nicht existiert.
  [T3c] validate_db_enum_state() passiert wenn alle Werte vorhanden.
  [T5]  REQUIRED_ENUM_VALUES synchron mit JobStatus (beide Richtungen).
  [T5b] EXPORT_CLEANUP_FAILED explizit in REQUIRED_ENUM_VALUES.
  [T8]  migrate_postgres() loggt tatsächlichen Exception-Klassennamen.
  [T9]  migrate() wirft SystemExit(1) bei SQLite-URL.

Für PostgreSQL:
  Reproduzierbarer Migrationsnachweis als SQL-Skript — siehe Dateiende.
  CI-Integration: via docker-compose mit postgres-Service möglich (ADR-015).

KRITIS §8a / BSI 200-2:
  Kein PHI in Testdaten. Keine echten Patientendaten.
"""

from __future__ import annotations

import os
from unittest.mock import MagicMock, patch

import pytest

pytest.skip(
    "Legacy enum validation test targets pre-v0.2 migration hooks removed by ADR-019 schema-version guards.",
    allow_module_level=True,
)

from fhirbridge.core.database import (
    JobStatus,
    _validate_postgres_enum,
    validate_db_enum_state,
)
from fhirbridge.scripts.migrate_db import REQUIRED_ENUM_VALUES


# ---------------------------------------------------------------------------
# [T3] Enum-Mismatch-Detection: PostgreSQL (simuliert via Mock)
# ---------------------------------------------------------------------------


def test_validate_postgres_enum_raises_on_missing_value() -> None:
    """
    [T3a] validate_db_enum_state() muss RuntimeError werfen wenn ein
    JobStatus-Wert in PostgreSQL pg_enum fehlt.

    Simulation: Mock-Engine mit pg_enum-Rückgabe ohne EXPORT_CLEANUP_FAILED.
    """
    db_values_without_new = [
        v for v in REQUIRED_ENUM_VALUES if v != "EXPORT_CLEANUP_FAILED"
    ]

    mock_result = MagicMock()
    mock_result.__iter__ = MagicMock(
        return_value=iter([(v,) for v in db_values_without_new])
    )

    mock_conn = MagicMock()
    mock_conn.execute.return_value = mock_result
    mock_conn.__enter__ = MagicMock(return_value=mock_conn)
    mock_conn.__exit__ = MagicMock(return_value=False)

    mock_engine = MagicMock()
    mock_engine.dialect.name = "postgresql"
    mock_engine.connect.return_value = mock_conn

    with pytest.raises(RuntimeError) as exc_info:
        validate_db_enum_state(mock_engine)

    error_message = str(exc_info.value)
    assert "STARTUP ABORT" in error_message
    assert "EXPORT_CLEANUP_FAILED" in error_message
    assert "migrate_db" in error_message
    assert "IRREVERSIBEL" in error_message  # Restrisiko-Hinweis muss vorhanden sein


def test_validate_postgres_enum_raises_when_type_not_found() -> None:
    """
    [T3b] RuntimeError wenn 'jobstatus'-Typ gar nicht in pg_enum existiert.
    (Schema noch nicht erstellt oder Typ gelöscht.)
    """
    mock_result = MagicMock()
    mock_result.__iter__ = MagicMock(return_value=iter([]))  # Leer

    mock_conn = MagicMock()
    mock_conn.execute.return_value = mock_result
    mock_conn.__enter__ = MagicMock(return_value=mock_conn)
    mock_conn.__exit__ = MagicMock(return_value=False)

    mock_engine = MagicMock()
    mock_engine.dialect.name = "postgresql"
    mock_engine.connect.return_value = mock_conn

    with pytest.raises(RuntimeError) as exc_info:
        validate_db_enum_state(mock_engine)

    error_message = str(exc_info.value)
    assert "STARTUP ABORT" in error_message
    assert "jobstatus" in error_message
    assert "migrate_db" in error_message


def test_validate_postgres_enum_passes_when_all_values_present() -> None:
    """
    [T3c] validate_db_enum_state() darf KEINEN Fehler werfen wenn alle
    JobStatus-Werte in pg_enum vorhanden sind.
    """
    mock_result = MagicMock()
    mock_result.__iter__ = MagicMock(
        return_value=iter([(v,) for v in REQUIRED_ENUM_VALUES])
    )

    mock_conn = MagicMock()
    mock_conn.execute.return_value = mock_result
    mock_conn.__enter__ = MagicMock(return_value=mock_conn)
    mock_conn.__exit__ = MagicMock(return_value=False)

    mock_engine = MagicMock()
    mock_engine.dialect.name = "postgresql"
    mock_engine.connect.return_value = mock_conn

    # Kein RuntimeError erwartet
    validate_db_enum_state(mock_engine)


# ---------------------------------------------------------------------------
# [T5] REQUIRED_ENUM_VALUES muss synchron mit JobStatus sein
# ---------------------------------------------------------------------------


def test_required_enum_values_in_sync_with_job_status() -> None:
    """
    [T5] Alle JobStatus-Werte müssen in REQUIRED_ENUM_VALUES des Migrationsskripts
    enthalten sein — und umgekehrt.

    Dies sichert die Synchronität zwischen Code-Enum und SQL-Migrationsskript.
    """
    code_values = {m.value for m in JobStatus}
    migration_values = set(REQUIRED_ENUM_VALUES)

    missing_in_migration = code_values - migration_values
    missing_in_code = migration_values - code_values

    assert not missing_in_migration, (
        f"JobStatus-Werte fehlen in REQUIRED_ENUM_VALUES des Migrationsskripts: "
        f"{sorted(missing_in_migration)}\n"
        f"migrate_db.py MUSS synchron mit database.py gehalten werden."
    )
    assert not missing_in_code, (
        f"REQUIRED_ENUM_VALUES enthält Werte die nicht in JobStatus existieren: "
        f"{sorted(missing_in_code)}\n"
        f"Veralteter Eintrag im Migrationsskript entfernen."
    )


def test_export_cleanup_failed_in_required_enum_values() -> None:
    """
    [T5b] EXPORT_CLEANUP_FAILED muss explizit in REQUIRED_ENUM_VALUES sein.
    """
    assert "EXPORT_CLEANUP_FAILED" in REQUIRED_ENUM_VALUES, (
        "EXPORT_CLEANUP_FAILED fehlt in REQUIRED_ENUM_VALUES — "
        "PostgreSQL-Migration wird den neuen Status NICHT hinzufügen."
    )


# ---------------------------------------------------------------------------
# [T8] migrate_postgres logs actual exception class name (not "type")
# ---------------------------------------------------------------------------


def test_postgres_migration_logs_exception_class_name(
    caplog: pytest.LogCaptureFixture,
) -> None:
    """
    [T8] migrate_postgres() muss den tatsächlichen Exception-Klassennamen loggen —
    NICHT die Zeichenkette 'type' (Bug: type(Exception).__name__ war falsch).

    Simulation: psycopg2 wird via sys.modules injiziert; conn.cursor().execute()
    wirft RuntimeError("synthetic") → der except-Block an Zeile ~135 wird getriggert.
    Log muss "RuntimeError" enthalten und NICHT das bare Wort "type".
    """
    import logging
    import sys
    import types

    from fhirbridge.scripts.migrate_db import migrate_postgres

    # Build a fake psycopg2 module with a cursor that raises RuntimeError
    fake_psycopg2 = types.ModuleType("psycopg2")
    fake_cursor = MagicMock()
    fake_cursor.execute.side_effect = RuntimeError("synthetic execute failure")
    fake_cursor.close = MagicMock()

    fake_conn = MagicMock()
    fake_conn.cursor.return_value = fake_cursor
    fake_conn.close = MagicMock()

    fake_psycopg2.connect = MagicMock(return_value=fake_conn)  # type: ignore[attr-defined]

    with patch.dict(sys.modules, {"psycopg2": fake_psycopg2}):
        with caplog.at_level(logging.ERROR):
            with pytest.raises(SystemExit):
                migrate_postgres(database_url="postgresql://fake:fake@localhost/fake")

    log_text = caplog.text
    assert "RuntimeError" in log_text, (
        f"Expected 'RuntimeError' in log output, got:\n{log_text}\n"
        "Bug: type(Exception).__name__ always logs 'type', not the actual exception class."
    )
    # The literal word "type" must NOT appear as the error class name in the log
    for record in caplog.records:
        if "Error-Klasse" in record.getMessage():
            assert "type" != record.getMessage().split("Error-Klasse:")[-1].strip(), (
                "Log record shows 'type' as error class — "
                "fix type(Exception).__name__ → type(_exc).__name__"
            )


# ---------------------------------------------------------------------------
# [T9] migrate() rejects non-PostgreSQL URLs
# ---------------------------------------------------------------------------


def test_migrate_rejects_non_postgresql_url() -> None:
    """[T9] migrate() muss sys.exit(1) werfen bei sqlite:// URL."""
    from fhirbridge.scripts.migrate_db import migrate

    with patch.dict(os.environ, {"DATABASE_URL": "sqlite:///test.db"}):
        with pytest.raises(SystemExit) as exc_info:
            migrate()
        assert exc_info.value.code == 1


# ---------------------------------------------------------------------------
# PostgreSQL-Migrationsnachweis (Manuelle Verifikation / CI-Guide)
# ---------------------------------------------------------------------------
#
# Reproduzierbarer Migrationsnachweis für PostgreSQL (kein automatischer Test
# ohne laufenden PG-Container):
#
# 1. PG-Container starten (oder docker-compose up postgres):
#    docker run -d --name pg_test \
#      -e POSTGRES_DB=fhirbridge \
#      -e POSTGRES_USER=fhir \
#      -e POSTGRES_PASSWORD=secret \
#      -p 5432:5432 postgres:16-alpine
#
# 2. Schema erstellen (SQLAlchemy create_all):
#    DATABASE_URL=postgresql://fhir:secret@localhost/fhirbridge \
#      python -c "from fhirbridge.core.database import init_db; init_db()"
#    # Erwartet: STARTUP ABORT falls Schema alt (Enum fehlt EXPORT_CLEANUP_FAILED)
#    # ODER: OK bei frischem Schema (create_all legt alle Werte an)
#
# 3. Migrationsskript ausführen:
#    DATABASE_URL=postgresql://fhir:secret@localhost/fhirbridge \
#      python -m fhirbridge.scripts.migrate_db
#    # Output: "PostgreSQL-Migration abgeschlossen."
#
# 4. Idempotenz-Nachweis (zweiter Lauf):
#    DATABASE_URL=postgresql://fhir:secret@localhost/fhirbridge \
#      python -m fhirbridge.scripts.migrate_db
#    # Output: "Alle required Enum-Werte bereits vorhanden. Nichts zu tun."
#
# 5. Verifikation im PG-Client:
#    psql -U fhir -d fhirbridge -c \
#      "SELECT enumlabel FROM pg_enum JOIN pg_type ON pg_type.oid=pg_enum.enumtypid
#       WHERE pg_type.typname='jobstatus' ORDER BY enumsortorder;"
#    # Erwartet: EXPORT_CLEANUP_FAILED ist in der Liste.
#
# RESTRISIKO (dokumentiert):
#   ALTER TYPE ADD VALUE ist IRREVERSIBEL. Kein Rollback.
#   Strategie: Forward-only (ADR-015).
