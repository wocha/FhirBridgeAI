# ADR-004: FHIR Export Data Sink via RabbitMQ

## Status

Accepted

## Context

Erfolgreich generierte FHIR- und ISiK-Bundles wurden bisher temporär in einer SQLite-Datenbank oder in einer generischen RabbitMQ-Queue als einfache JSON-Strings abgelegt. Dies war jedoch lediglich ein Zwischenschritt, keine echte "Data Sink". Für den produktiven Einsatz im Krankenhausumfeld (z.B. Integration in ein KIS oder ein klinisches Daten-Repository) müssen die generierten und verifizierten FHIR-Ressourcen an einen externen FHIR-Server (z.B. HAPI-FHIR, IBM FHIR, oder eine KIS-Schnittstelle) exportiert werden.

Es bedarf einer dedizierten, entkoppelten asynchronen Export-Komponente, die:

1. Skalierbar hohe Volumina an FHIR-Ressourcen publizieren kann (Asynchronität / Non-blocking I/O).
2. Resilient gegenüber temporären Ausfällen des Ziel-FHIR-Servers ist (Exponential Backoff, Retries).
3. Permanente Fehler (wie Schema-Validierungsfehler auf der Gegenseite oder `400 Bad Request`) sauber abfängt und die betroffenen Nachrichten systematisch isoliert (Dead-Letter-Exchange).

## Decision

Wir implementieren einen neuen, dedizierten Python-basierten Microservice, den **FHIR Export Worker**.

1. **Messaging Middleware**: Der Worker konsumiert Nachrichten asynchron von einer neuen RabbitMQ-Queue namens `fhir_export_queue`. Die Nutzung von RabbitMQ stellt "At-Least-Once Delivery" sicher, sodass bei Netzwerkfehlern während des HTTP-Requests keine medizinischen Daten in-flight verloren gehen.
2. **HTTP Client**: Wir verwenden `httpx.AsyncClient` für non-blocking I/O.
3. **Fehlerbehandlung**:
   - Temporäre Fehler (Timeouts, HTTP 500/502/503/504): Die Nachricht wird über den RabbitMQ NACK-Mechanismus oder intern via Exponential Backoff (z.B. `tenacity`) für einen Retry markiert.
   - Permanente Fehler (HTTP 4xx): Das FHIR-Bundle ist vermutlich syntaktisch oder fachlich invalid für den Zielserver. Die Nachricht wird "ge-nackt" (ohne Requeue) und über die `x-dead-letter-exchange` Konfiguration der Queue in eine Isolation Area verschoben.
4. **Umgebungskonfiguration**: Die Ziel-URL des Servers wird deterministisch (12-Factor App) per Environment Variable `FHIR_SERVER_URL` konfiguriert.

## Consequences

### Positive

- **Entkopplung**: Die rechenintensiven LLM-Pipelines und die I/O-lastigen Export-Vorgänge konkurrieren nicht um dieselben Ressourcen.
- **Resilienz**: Ausfälle oder Latenz-Spitzen des externen KIS/FHIR-Servers blockieren nicht das gesamte LLM-Inference-System.
- **Standardisierung**: Wir nähern uns echten KRITIS-Anforderungen durch sauberes Event-Routing und Error Handling (DLQ).

### Negative / Risks

- **Erhöhte Infrastruktur-Komplexität**: Ein weiterer Worker-Container, der deployt, konfiguriert und überwacht werden muss.
- **Monitoring**: RabbitMQ Message Rates für die Export-Queue müssen separat überwacht werden, um Backpressure oder eine volllaufende DLQ rechtzeitig zu erkennen.
