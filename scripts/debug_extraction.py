import json
import os

from fhirbridge.core.database import Job, create_engine, sessionmaker


def debug_extraction(pat_id="PAT_2002_1114"):
    database_url = os.getenv("DATABASE_URL")
    if database_url:
        engine = create_engine(database_url)
    else:
        engine = create_engine("sqlite:///data/dispatcher.db")
        
    Session = sessionmaker(bind=engine)
    session = Session()

    jobs = session.query(Job).filter(Job.filepath.contains(pat_id)).all()

    print(f"--- Debugging Extraction for {pat_id} ---")
    for j in jobs:
        print(f"\nFile: {os.path.basename(j.filepath)}")
        print(f"Status: {j.status}")
        if j.ocr_text:
            print(f"OCR Snippet (100 chars): {j.ocr_text[:100]}...")
        else:
            print("OCR Text: [EMPTY]")

        if j.fhir_json:
            fhir = json.loads(j.fhir_json)
            # Check for specific fields
            pat = fhir.get("Patient", {})
            name = pat.get("name", [{}])[0].get("family", "Unknown")
            bd = pat.get("birthDate", "Unknown")
            enc = fhir.get("Encounter", {})
            fall = enc.get("identifier", [{}])[0].get("value", "Unknown")
            diags = enc.get("diagnosis", [])
            diag_count = len(diags)

            print(f"Extracted: Name={name}, BD={bd}, Fall={fall}, Diags={diag_count}")
        else:
            print("FHIR JSON: [EMPTY]")

    session.close()


if __name__ == "__main__":
    debug_extraction()
