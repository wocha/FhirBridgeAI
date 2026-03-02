import os
import sys

# Setup paths to import db config and schema
skill_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".agents", "skills", "building-autonomous-dispatchers", "scripts"))
sys.path.append(skill_dir)

from schema_reference import Base, Job, JobStatus
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

DB_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), "data", "dispatcher.db"))
DATABASE_URL = os.getenv("DATABASE_URL")

if DATABASE_URL:
    engine = create_engine(DATABASE_URL)
else:
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    engine = create_engine(f"sqlite:///{DB_PATH}", connect_args={'check_same_thread': False})

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def enqueue_test_jobs():
    Base.metadata.create_all(bind=engine)

    docs = [
        os.path.abspath(os.path.join(os.path.dirname(__file__), "data", "inbound", "PT-LR-B437D1", "FALL-2019-B6EE", "KDL-AD010103_20190713.pdf")),
        os.path.abspath(os.path.join(os.path.dirname(__file__), "data", "inbound", "PT-LR-B437D1", "FALL-2019-B6EE", "KDL-LB120103_20190706.pdf")),
        os.path.abspath(os.path.join(os.path.dirname(__file__), "data", "inbound", "Testbrief.pdf")),
    ]

    with SessionLocal() as session:
        for doc in docs:
            # Check if file exists, just to be sure
            if not os.path.exists(doc):
                print(f"Warning: File {doc} does not exist!")

            job = Job(
                file_path=doc,
                status=JobStatus.PENDING
            )
            session.add(job)
            print(f"Enqueued {doc}")

        session.commit()
        print("Successfully committed jobs.")

if __name__ == "__main__":
    enqueue_test_jobs()
