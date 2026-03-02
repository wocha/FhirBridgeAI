"""
Database Migration Script.
Adds the manual `ocr_text` and `fhir_json` columns to the existing SQLite database
without deleting existing records.
"""

import logging
import sqlite3
import sys

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")

DB_PATH = "data/dispatcher.db"


def migrate() -> None:
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()

        # Add ocr_text if missing
        try:
            cursor.execute("ALTER TABLE jobs ADD COLUMN ocr_text TEXT;")
            logging.info("Added 'ocr_text' column.")
        except sqlite3.OperationalError as e:
            if "duplicate column name" in str(e).lower():
                logging.info("'ocr_text' already exists.")
            else:
                logging.error(f"Failed to add ocr_text: {e}")

        # Add fhir_json if missing
        try:
            cursor.execute("ALTER TABLE jobs ADD COLUMN fhir_json TEXT;")
            logging.info("Added 'fhir_json' column.")
        except sqlite3.OperationalError as e:
            if "duplicate column name" in str(e).lower():
                logging.info("'fhir_json' already exists.")
            else:
                logging.error(f"Failed to add fhir_json: {e}")

        conn.commit()
        conn.close()
        logging.info("Migration finished.")

    except Exception as e:
        logging.error(f"Database error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    migrate()
