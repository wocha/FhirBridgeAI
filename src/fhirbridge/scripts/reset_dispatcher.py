"""
Utility script to reset the dispatcher database under explicit operator control.

This script is not part of the active runtime. It drops all tables and then
re-applies the controlled migration set.
"""

from __future__ import annotations

import logging

from fhirbridge.core.config import get_settings
from fhirbridge.core.database import Base, get_sync_engine
from fhirbridge.core.migrations import apply_pending_migrations

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def reset_db(database_url: str | None = None) -> None:
    resolved_database_url = database_url or get_settings().require_database_url()
    logger.info("Connecting to configured PostgreSQL runtime database")
    engine = get_sync_engine(database_url=resolved_database_url)

    try:
        logger.info("Dropping all existing tables...")
        Base.metadata.drop_all(engine)

        logger.info("Re-applying controlled migrations...")
        apply_pending_migrations(engine)
    finally:
        engine.dispose()

    logger.info("Database reset successfully.")


if __name__ == "__main__":
    reset_db()
