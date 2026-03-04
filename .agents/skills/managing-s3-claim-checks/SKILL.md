---
name: managing-s3-claim-checks
description: Architektur-Vorgaben für den Umgang mit großen Dateianhängen in asynchronen Queues.
---

# Async S3 & Claim-Check Pattern

Dieses Dokument definiert den Gold-Standard für den firmenweiten Umgang mit großen Artefakten (PDFs, Röntgenbilder), die asynchron durch RabbitMQ oder andere Broker geleitet werden müssen.

## Das Architekturproblem (Thundering Herd & OOM)

RabbitMQ ist nicht dafür designt, 15 Megabyte große PDF-Dateien als Base64-Strings in Nachrichten zu transportieren. Dies flutet den Arbeitsspeicher (RAM) der Broker und führt zu massiven Latenzen und Systemabstürzen unter Last (z.B. wenn 100 PDFs gleichzeitig hochgeladen werden).

## Die Lösung: Claim-Check Pattern

### Regel 1: Trennung von Payload und Routing

Große Binärdaten (Payloads) dürfen niemals direkt in die Message Queue geschrieben werden. Stattdessen speichern wir sie in einem billigen, horizontal skalierbaren Object-Storage (Standard: MinIO / S3).

### Regel 2: Der "Garderoben-Bon" (Claim-Check)

In die Message Queue (`llm_extraction_queue` etc.) wird statt der PDF-Datei lediglich ein strukturierter Metadaten-Datensatz (Standard: Pydantic DocumentMetaData) publiziert, welcher die URL (`payload_uri`) zum S3-Speicher enthält.
Jeder Worker, der die Notwendigkeit hat, holt sich das Dokument anhand dieser URI selbstständig aus dem Storage ab.

## Implementierung in Python (Asyncio)

### Regel 3: NIEMALS Boto3

Innerhalb der asynchronen FastAPI/RabbitMQ Worker ist die Verwendung der synchronen `boto3` Bibliothek streng untersagt, da jeder Aufruf den Event-Loop blockiert.

### Regel 4: Immer aioboto3

Nutze stattdessen zwingend `aioboto3`.
Ein Verbindungsaufbau muss immer über den asynchronen Context-Manager erfolgen:

```python
import aioboto3

session = aioboto3.Session()
async with session.client('s3', endpoint_url="...", aws_access_key_id="...", aws_secret_access_key="...") as s3:
    await s3.upload_file(file_path, bucket_name, object_name)
```

### Umgebungsvariablen

Der zentrale S3 / MinIO Container wird über folgende Variablen angesprochen:

* `MINIO_URL` (Fallback: `http://localhost:9000`)
* `MINIO_ROOT_USER` (Fallback: `admin`)
* `MINIO_ROOT_PASSWORD` (Fallback: `admin123`)
