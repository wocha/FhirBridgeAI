from __future__ import annotations

from fhirbridge.core.config import get_settings
from fhirbridge.core.database import Job, JobStatus, get_session_factory, get_sync_engine, verify_runtime_schema


def check_status() -> None:
    engine = get_sync_engine(database_url=get_settings().require_database_url())
    try:
        verify_runtime_schema(engine)
        session_factory = get_session_factory(engine)
        with session_factory() as session:
            status_counts = {
                status.value: session.query(Job).filter_by(status=status).count()
                for status in JobStatus
            }
            total = session.query(Job).count()

            print("--- Pipeline Status ---")
            print(f"Total Jobs: {total}")
            for status_name, count in sorted(status_counts.items()):
                print(f"{status_name}: {count}")
    finally:
        engine.dispose()


if __name__ == "__main__":
    check_status()
