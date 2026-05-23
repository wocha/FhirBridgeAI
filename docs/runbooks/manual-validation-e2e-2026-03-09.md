# FhirBridgeAI E2E Manual Validation Runbook (2026-03-09)

## 1) Scope
Dieses Runbook kombiniert:
- automatischen Volltest (pytest)
- manuelle End-to-End Validierung der Live-Umgebung
- Zero-Trust und PHI-Sicherheitschecks

## 2) Aktueller Session-Status
- `pytest`: 31 passed
- Live-Ingestion OpenAPI (im Container): `/ingest/pdf`, `/ingest/text`
- Ohne Bearer-Token: `/ingest/text` liefert `401 Not authenticated`

## 3) Preflight
```bash
docker compose ps
```
Erwartung: `ingestion-gateway`, `rabbitmq`, `postgres`, `minio`, `llm-worker`, `ocr-worker`, `fhir-export-worker`, `jaeger`, `prometheus`, `grafana` sind `Up`.

## 4) Token fuer klinische Rolle holen
Hinweis: Endpoint verlangt Bearer JWT mit klinischer Rolle (`PHYSICIAN`, `NURSE` oder `EMERGENCY`).

```bash
KEYCLOAK_URL="http://localhost:8080"   # falls lokal exposed; sonst via docker exec
REALM="fhirbridge"
CLIENT_ID="fhirbridge-api"
USERNAME="<clinical_user>"
PASSWORD="<clinical_password>"

# Variante A: lokal (wenn Keycloak-Port erreichbar)
token_resp="$(curl -sS -X POST "$KEYCLOAK_URL/realms/$REALM/protocol/openid-connect/token" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  --data-urlencode "grant_type=password" \
  --data-urlencode "client_id=$CLIENT_ID" \
  --data-urlencode "username=$USERNAME" \
  --data-urlencode "password=$PASSWORD")"
ACCESS_TOKEN="$(python3 -c 'import json,sys; print(json.load(sys.stdin)["access_token"])' <<<"$token_resp")"

# Variante B: im Keycloak-Container
# docker exec fhirbridge_keycloak sh -lc "curl -sS -X POST http://localhost:8080/realms/fhirbridge/protocol/openid-connect/token -H 'Content-Type: application/x-www-form-urlencoded' -d 'grant_type=password&client_id=fhirbridge-api&username=<clinical_user>&password=<clinical_password>'"
```

## 5) Positivtest: Text-Ingestion
```bash
curl -k -X POST "https://ingest.docker.localhost/ingest/text" \
  -H "Authorization: Bearer ${ACCESS_TOKEN}" \
  -H "Content-Type: text/plain" \
  --data "Patient Max Mustermann, station A2, V.a. Pneumonie"
```
Erwartung: `202 Accepted` + `document_id`.

## 6) Positivtest: PDF-Ingestion
```bash
curl -k -X POST "https://ingest.docker.localhost/ingest/pdf" \
  -H "Authorization: Bearer ${ACCESS_TOKEN}" \
  -H "Content-Type: application/pdf" \
  --data-binary "@/path/to/sample.pdf"
```
Erwartung: `202 Accepted` + `document_id`.

## 7) Negativtests (Fail-Closed)
### 7.1 Ohne Token
```bash
curl -k -i -X POST "https://ingest.docker.localhost/ingest/text" -H "Content-Type: text/plain" --data "test"
```
Erwartung: `401`.

### 7.2 Falscher Content-Type auf PDF Route
```bash
curl -k -i -X POST "https://ingest.docker.localhost/ingest/pdf" \
  -H "Authorization: Bearer ${ACCESS_TOKEN}" \
  -H "Content-Type: text/plain" \
  --data "not a pdf"
```
Erwartung: `415`.

## 8) Datenfluss-Checks nach erfolgreichem Request
### 8.1 RabbitMQ Queue Activity
```bash
docker exec fhirbridge_rabbitmq rabbitmqctl list_queues name messages messages_ready messages_unacknowledged
```
Erwartung: OCR/Text Queue Traffic sichtbar, keine stetig waachsenden Backlogs.

### 8.2 MinIO Claim-Check
```bash
docker exec fhirbridge_minio sh -lc "mc alias set local http://localhost:9000 admin admin123 >/dev/null 2>&1; mc ls local/ephemeral-payloads --recursive"
```
Erwartung: Nur Object Keys, keine PHI im Queue Payload.

### 8.3 PHI-safe Logging Stichprobe
```bash
docker logs --since 5m fhirbridge_ingestion
docker logs --since 5m fhirbridge_ocr_worker
docker logs --since 5m fhirbridge_llm_worker
```
Erwartung: Keine Patienteninhalte in Logs; nur Fehlercodes/Exception-Typen.

### 8.4 Jaeger Trace
- Jaeger UI oeffnen (`jaeger` Service)
- Trace fuer Ingestion Request suchen
- Span-Kette pruefen: Ingestion -> OCR/LLM -> FHIR Export

## 9) Pass/Fail Matrix
- PASS wenn:
  - beide Positivtests `202` liefern
  - Negativtests korrekt blocken (`401`/`415`)
  - Queue/S3/Logs/Trace konsistent sind
- FAIL wenn:
  - unautorisierte Requests akzeptiert werden
  - PHI in Logs auftaucht
  - Queue publish ohne nachvollziehbaren Claim-Check erfolgt
