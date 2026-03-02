"""
Utility script to safely reset the SQLite dispatcher database.
Drops and recreates all tables via SQLAlchemy to bypass Windows file locking
issues that occur when using `rm` while Streamlit or other processes hold a lock.
"""

import logging

from fhirbridge.core.database import Base, get_engine, init_db

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def reset_db(db_path: str = "data/dispatcher.db") -> None:
    logger.info(f"Connecting to database: {db_path}")
    engine = get_engine(db_path)

    logger.info("Dropping all existing tables...")
    Base.metadata.drop_all(engine)

    logger.info("Recreating tables...")
    init_db(db_path)

    logger.info("Database reset successfully.")


if __name__ == "__main__":
    reset_db()
