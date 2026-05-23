# Antigravity Parallel Session Prompts (Goldstandard)

Diese Prompts sind darauf ausgelegt, in neuen, parallelen Chat-Sitzungen verwendet zu werden. Sie setzen sofort den richtigen architektonischen Kontext ("Platform Architect") und delegieren klar definierte, isolierte Aufgabenpakete an den Agenten.

## Der "Best Practice" Initialisierungs-Prompt (Für jede neue Sitzung)

Nutze diesen Block am Anfang *jeder* neuen Sitzung, um den Agenten sofort auf das geforderte Senioritäts-Level (Staff Engineer) und die Architektur-Richtlinien zu eichen.

```text
CONTEXT RESET & ARCHITECTURE RULES: Wir arbeiten nach dem "Antigravity Skill Goldstandard".
Du agierst als Staff/Principal Engineer. Dein Fokus liegt auf einer stabilen, asynchronen Microservice-Architektur, KRITIS-Konformität (Privacy-Preserving AI) und strikter Einhaltung von FHIR/ISiK-Standards.

Regeln für diese Sitzung:
1. Python Enterprise: Strikte Typisierung (PEP 484), Pydantic für alle Datenmodelle, keine Magic Numbers, strukturiertes Error-Handling.
2. Skill-Trennung: `SKILL.md` ist nur der Router. Logik liegt in `scripts/*.py`. Prompts liegen in `templates/`.
3. Delegation: Du analysierst keine echten Massendaten. Das machst du lokal über LLM-Skripte (localhost:11434).
4. Keine Quick-and-Dirty Skripte: Schreibe Code, der auch bei 50.000 parallelen Events nicht crasht (Retry-Loops, Backoff).

[HIER DEINE SPEZIFISCHE AUFGABE EINFÜGEN]
```

---

## Spezifische Task-Prompts für parallele Streams

Du kannst die folgenden Prompts an den obigen "Best Practice" Block anhängen, um parallel an verschiedenen Baustellen zu arbeiten, ohne dass sich die Agenten-Kontexte überschneiden.

### Stream 1: RabbitMQ & Async Queues (Phase 2)

```text
Aufgabe für diese Sitzung: Refactoring des Document Dispatchers auf RabbitMQ.
Lies dir zuerst `src/fhirbridge/workers/dispatcher.py` durch.
Deine Ziele:
1. Ersetze jede verbleibende Legacy-Queue durch `aio-pika` zur asynchronen Anbindung an RabbitMQ.
2. Entwirf eine saubere Consumer-Klasse, die Idempotenz sicherstellt (Nachrichten werden exactly-once verarbeitet).
3. Implementiere robustes Error-Handling (Exponential Backoff mit der Bibliothek `tenacity`), falls das lokale LLM oder die PDF-Engine blockieren.
Bitte erstelle zunächst einen Plan (implementation_plan.md) und zeige mir, wie du den Pika-Consumer strukturieren willst.
```

### Stream 2: KRITIS & Anonymisierung (Phase 3)

```text
Aufgabe für diese Sitzung: Aufbau des Privacy-Preserving AI Layers.

Wir brauchen einen "Antigravity Skill Goldstandard" für die Anonymisierung. Das bedeutet keine halben Sachen. Bitte adressiere folgende Punkte kritisch:

1.  **Das "Rückübersetzungs-Problem" (De-Scrubbing):** Wenn wir Texte vor dem Mistral-Aufruf anonymisieren (z.B. Max Mustermann -> John Doe), muss das Ergebnis des LLMs zwingend wieder in die Originaldaten zurückübersetzt werden, bevor es gespeichert wird. Entwirf neben `scrub_text` zwingend eine `unscrub_text` Methode inkl. eines State-Managements (Dictionary) für den Request-Lebenszyklus.
2.  **Regex vs. Named Entity Recognition (NER):** Reines Regex für deutsche Datumsformate und einfache Lookups für Namen sind fehleranfällig. Prüfe und implementiere (falls sinnvoll) den Einsatz eines lokalen, kleinen NER-Modells (z.B. `spaCy` mit `de_core_news_sm`), um Personen und Orte robuster zu extrahieren.
3.  **Pydantic-Unterstützung:** Der Scrubber darf nicht nur rohe Strings verarbeiten, sondern muss auch rekursiv Pydantic-Objekte (`scrub_dict`/`scrub_model`) bereinigen können, da unser `PatientState` oft als strukturiertes Objekt übergeben wird.

Deine konkreten Ziele für diese Sitzung:
1. Entwirf das Modul `src/fhirbridge/core/anonymizer.py` mit PiiScrubber (inkl. scrub/unscrub Logik).
2. Integriere diesen Scrubber als Interceptor in `src/fhirbridge/core/llm_client.py`.
3. Schreibe robuste pytest Unit-Tests, die beweisen, dass Klartext-Daten sicher pseudonymisiert UND wiederhergestellt werden.

Bitte erstelle zuerst einen Strukturvorschlag als Implementation Plan, wie du diese drei kritischen Punkte lösen willst.
```

### Stream 3: FHIR & ISiK Standards (Phase 4)

```text
Aufgabe für diese Sitzung: Refactoring der Pydantic Modelle auf strikte ISiK-Profile (Telematikinfrastruktur).
Lies dir `src/fhirbridge/models/fhir_models.py` durch.
Deine Ziele:
1. Überarbeite die bestehenden Ressourcen (Patient, Encounter, Observation, Composition), sodass sie zwingend die deutschen ISiK-Basis-Profile validieren.
2. Nutze Pydantic Validators, um sicherzustellen, dass z.B. das `identifier` System für die Krankenversichertennummer (KVNR) exakt der Spezifikation entspricht.
3. Baue Mappings für deutsche ICD-10-GM und OPS-Codes sauber ein.
Bitte skizziere mir erst die Änderungen an den Basis-Modellen.
```

### Stream 4: CI/CD & Open Source Polish (Phase 5)

```text
Aufgabe für diese Sitzung: Bootstrap der DevOps und Open-Source Architektur.
Deine Ziele:
1. Erstelle eine `docker-compose.yml` im Root-Verzeichnis, die RabbitMQ, eine fiktive Postgres-DB und unsere Worker-Services orchestriert.
2. Richte eine `.github/workflows/ci.yml` Pipeline ein, die `mypy`, `black`, `ruff` und `pytest` ausführt.
3. Schreibe einen professionellen `Architecture Decision Record` (ADR) im Ordner `docs/architecture/`, der begründet, warum wir lokale LLMs (Mistral) statt Cloud-APIs (GPT-4) verwenden (Fokus: Data Sovereignty im KRITIS-Umfeld).
Beginne mit der `docker-compose.yml`.
```
