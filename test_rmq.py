import asyncio
import json
import os
import sys

import aio_pika

# Define our DB engine for FINAL status updates.
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), ".agents", "skills", "building-autonomous-dispatchers", "scripts")))
from schema_reference import Base, Job, JobStatus

DB_PATH = os.getenv("DB_PATH", os.path.abspath(os.path.join(os.path.dirname(__file__), "data", "dispatcher.db")))
DATABASE_URL = os.getenv("DATABASE_URL")

if DATABASE_URL:
    engine = create_engine(DATABASE_URL)
else:
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    engine = create_engine(f"sqlite:///{DB_PATH}", connect_args={'check_same_thread': False})

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

async def main():
    # Insert jobs into DB
    Base.metadata.create_all(bind=engine)
    with SessionLocal() as session:
        job1 = Job(file_path="/tmp/Testbrief_Success.pdf", status=JobStatus.PENDING)
        job2 = Job(file_path="/tmp/Testbrief_Fail.pdf", status=JobStatus.PENDING)
        session.add(job1)
        session.add(job2)
        session.commit()
        job1_id = job1.id
        job2_id = job2.id
        print(f"Created Job {job1_id} and {job2_id} in DB.")

    connection = await aio_pika.connect_robust("amqp://mq_admin:secure_mq_pass@localhost:5672/")
    async with connection:
        channel = await connection.channel()
        queue = await channel.declare_queue(
            "fhir_jobs_queue",
            durable=True,
            arguments={
                "x-dead-letter-exchange": "fhir_dlx",
                "x-dead-letter-routing-key": "dlx_routing_key"
            }
        )

        message_body = json.dumps({
            "job_id": job1_id,
            "file_path": "/tmp/Testbrief_Success.pdf"
        }).encode()

        await channel.default_exchange.publish(
            aio_pika.Message(body=message_body),
            routing_key="fhir_jobs_queue"
        )
        print(" [x] Sent Success Message")

        message_body_fail = json.dumps({
            "job_id": job2_id,
            "file_path": "/tmp/Testbrief_Fail.pdf"
        }).encode()

        await channel.default_exchange.publish(
            aio_pika.Message(body=message_body_fail),
            routing_key="fhir_jobs_queue"
        )
        print(" [x] Sent Failure Message")

if __name__ == "__main__":
    asyncio.run(main())
