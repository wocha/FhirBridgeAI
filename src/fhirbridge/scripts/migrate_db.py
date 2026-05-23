"""Apply controlled schema migrations for the FhirBridgeAI runtime database."""

from __future__ import annotations

import logging

from fhirbridge.core.config import get_settings
from fhirbridge.core.database import get_sync_engine
from fhirbridge.core.migrations import EXPECTED_SCHEMA_VERSION, apply_pending_migrations, get_current_schema_version

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
logger = logging.getLogger(__name__)


def migrate() -> int:
    database_url = get_settings().require_database_url()
    engine = get_sync_engine(database_url=database_url)
    try:
        applied_versions = apply_pending_migrations(engine)
        current_version = get_current_schema_version(engine)
    finally:
        engine.dispose()

    if applied_versions:
        logger.info("Applied schema migration(s): %s", ", ".join(str(version) for version in applied_versions))
    else:
        logger.info("No pending migrations found.")
    logger.info(
        "Schema verification target=%s current=%s",
        EXPECTED_SCHEMA_VERSION,
        current_version,
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(migrate())
