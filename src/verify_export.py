import asyncio
import json
import logging
import os
import sys

import aio_pika

# Ensure fhirbridge is in sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "src")))

from fhirbridge.core.database import Job, JobStatus, get_session_factory, init_db
from fhirbridge.core.rabbitmq import FhirExportMessage

logging.basicConfig(level=logging.INFO)


async def main():
    engine = init_db("data/dispatcher.db")
    SessionFactory = get_session_factory(engine)
    import time

    with SessionFactory() as session:
        job = Job(filepath=f"test_export_fail_{time.time()}", status=JobStatus.FHIR_GENERATED)
        session.add(job)
        session.commit()
        job_id = job.id
        logging.info(f"Created Job #{job_id}")

    connection = await aio_pika.connect_robust(
        os.getenv("RABBITMQ_URL", "amqp://guest:guest@rabbitmq:5672/")
    )
    channel = await connection.channel()

    exchange = channel.default_exchange

    msg = FhirExportMessage(
        job_id=job_id,
        bundle_json=json.dumps({"resourceType": "Bundle", "type": "transaction", "entry": []}),
    )

    await exchange.publish(
        aio_pika.Message(body=msg.model_dump_json().encode(), correlation_id=f"job-{job_id}"),
        routing_key="fhir_export_queue",
    )

    logging.info(f"Published test message for Job #{job_id} to fhir_export_queue")
    await connection.close()


if __name__ == "__main__":
    asyncio.run(main())
