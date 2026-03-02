import os

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from fhirbridge.core.database import Job


def check_status(db_path="data/dispatcher.db"):
    database_url = os.getenv("DATABASE_URL")
    
    if database_url:
        engine = create_engine(database_url)
    else:
        if not os.path.exists(db_path):
            print(f"Error: Database {db_path} does not exist.")
            return
        engine = create_engine(f"sqlite:///{db_path}")
        
    Session = sessionmaker(bind=engine)
    session = Session()

    try:
        total = session.query(Job).count()
        pending = session.query(Job).filter_by(status="PENDING").count()
        ocr_proc = session.query(Job).filter_by(status="OCR_PROCESSING").count()
        llm_ext = session.query(Job).filter_by(status="LLM_EXTRACTION").count()
        done = session.query(Job).filter_by(status="FHIR_GENERATED").count()
        error = session.query(Job).filter_by(status="ERROR").count()

        print("--- Pipeline Status ---")
        print(f"Total Jobs:      {total}")
        print(f"PENDING:         {pending}")
        print(f"OCR_PROCESSING: {ocr_proc}")
        print(f"LLM_EXTRACTION: {llm_ext}")
        print(f"FHIR_GENERATED: {done}")
        print(f"ERROR:           {error}")

        if error > 0:
            print("\nFirst Error Trace (Job #1):")
            ej = session.query(Job).filter_by(status="ERROR").first()
            if ej:
                print(f"File: {ej.filepath}")
                print(f"Trace:\n{ej.error_trace}")

    finally:
        session.close()


if __name__ == "__main__":
    check_status()
