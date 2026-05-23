# Projekt-Audit 2026-03-17

## Scope

Dieses Audit bewertet den Workspace-Stand am 2026-03-17, nicht nur den letzten Commit.

- Repo: `<project-root>`
- Branch: `master`
- Letzter Commit laut lokalem Git: `5af1866cee8941fbdfb1444e840dfabe41d45e13` vom `2026-03-09 21:39:58 +0100`
- Arbeitsbaum: deutlich "dirty", mit vielen lokalen und unversionierten Architektur-, Security- und Testaenderungen
- Lokale Reproduktionsbelege aus diesem Audit:
  - `pytest -q` am 2026-03-17: `118 passed, 7 skipped`
  - `python scripts/security/check_security_posture.py`: `Security checks passed.`

Wichtig: Dieses Dokument ist eine technische und regulatorische Einschaetzung, keine verbindliche Rechtsberatung.

## Kurzfazit

FhirBridgeAi ist fuer einen lokalen Prototypen bzw. einen architektonischen Vorbau ungewoehnlich weit. Die Kernarchitektur ist nicht mehr "nur Idee", sondern in relevanten Teilen real implementiert: Boundary-Auth mit internem Token-Exchange, Async-Postgres-Runtime, Transactional Outbox, Claim-Check ueber MinIO, Manual Review, FHIR-Export, Read-Model-Gating, Security-Runbooks und ein belastbarer Testsockel.

Trotzdem ist das Projekt nach heutigem Stand nicht KRITIS-ready fuer den produktiven Einsatz in einem deutschen Krankenhaus. Die groessten Gruende sind nicht die Business-Logik, sondern die "letzte Meile" der Compliance und Betriebsreife: fehlende Vollhaertung aller internen Transportwege, fehlende organisatorische Nachweisdokumente nach DSGVO/KRITIS-Massstab, fehlende Live-Evidence fuer einzelne Kontrollpfade, keine manipulationssichere Audit-Ablage und mehrere Dev-/Bootstrap-Ausnahmen, die fuer einen echten Krankenhausbetrieb nicht stehen bleiben duerfen.

## Projekt in einem Satz

Das Projekt ist eine Python-3.12-Microservice-Plattform zur asynchronen Verarbeitung medizinischer Dokumente mit OCR, lokaler LLM-Extraktion, PHI-Pseudonymisierung, Manual Review und optionalem FHIR-Export sowie separater Synthetic-Data-Generierung.

## Architekturuebersicht nach Ist-Stand

### Produktive Kernpfade im Code vorhanden

1. Ingestion-Gateway
   - FastAPI-Boundary mit JWT-Validierung gegen Keycloak-JWKS und internem Token-Exchange
   - Claim-Check fuer Eingangsdokumente nach MinIO
   - Outbox-Handoff statt Direkt-Publish
   - Belege:
     - `src/fhirbridge/ingestion/api.py`
     - `src/fhirbridge/core/auth.py`
     - `src/fhirbridge/core/storage.py`
     - `tests/test_boundary_contracts.py`
     - `tests/test_token_exchange.py`

2. OCR-Stufe
   - PDF aus Evidence-Storage
   - OCR im ProcessPool
   - anschliessende Pseudonymisierung
   - Persistenz von Processing-Artefakt plus PHI-Mapping
   - naechster Stage-Handoff wieder ueber Outbox
   - Belege:
     - `src/fhirbridge/workers/ocr_worker.py`
     - `src/fhirbridge/privacy/pseudonymizer.py`

3. LLM-Extraktion
   - LLM liest nur pseudonymisierte Verarbeitungstexte
   - strukturierte Extraktion in FHIR-nahe JSON-Strukturen
   - semantische Chunks
   - erzwungener Manual-Review-Pfad
   - Belege:
     - `src/fhirbridge/workers/llm_worker.py`
     - `src/fhirbridge/core/llm.py`
     - `src/fhirbridge/core/qdrant_security.py`

4. Manual Review und Read-Model
   - Review ist backend-vermittelt
   - Dashboard spricht nicht direkt mit Broker, DB oder MinIO
   - Version Gate fuer materialisierte Read-Models
   - Belege:
     - `dashboard/app.py`
     - `src/fhirbridge/core/read_models.py`
     - `tests/test_read_model_gate.py`
     - `tests/test_review_endpoint.py`

5. FHIR-Export
   - HTTPS-only, explizites CA-Bundle
   - Deanonymisierung erst unmittelbar vor Export
   - Downstream-Konsistenzpfad mit Reconciliation
   - Belege:
     - `src/fhirbridge/workers/fhir_export_worker.py`
     - `src/fhirbridge/core/config.py`

6. Persistenz- und Zustandsmodell
   - Async Postgres only
   - versionierte Migrationen
   - Outbox, Consumed-Message-Dedupe, Read-Models, Review-Cases, Reconciliation, Security-Audit, Semantic-Chunks
   - Belege:
     - `src/fhirbridge/core/database.py`
     - `src/fhirbridge/core/migrations.py`
     - `tests/test_database_runtime.py`
     - `tests/test_outbox_dispatcher.py`

7. Observability und Security Governance
   - OTel/Jaeger, Prometheus, Grafana
   - Threat Model, Control Mapping, Runbooks, Hardening-Reports
   - statische Security-Posture-Pruefung
   - Belege:
     - `src/fhirbridge/core/telemetry.py`
     - `docs/security/control-mapping.md`
     - `docs/security/threat-model.md`
     - `scripts/security/check_security_posture.py`

### Im Code vorhanden, aber operativ nicht voll nachgewiesen

1. Live-Keycloak-JWKS-Nachweis
   - im Code und in Tests vorhanden
   - live laut ADR noch `nicht nachweisbar`
   - Beleg:
     - `docs/adr/ADR-024-Keycloak-Live-Evidence-Exception.md`

2. Live-Postgres-Rollout-Nachweis
   - Migrationspfad vorhanden
   - live laut ADR noch `nicht nachweisbar`
   - Beleg:
     - `docs/adr/ADR-022-Async-DB-Runtime-and-Controlled-Migrations.md`

3. Live-Qdrant-Tenant-Isolation
   - Guardrails und Tests vorhanden
   - live laut ADR noch `nicht nachweisbar`
   - Beleg:
     - `docs/adr/ADR-023-Qdrant-Live-Evidence-Exception.md`

### Nur dokumentiert oder Guardrail-only

1. Kafka / Audit-Ledger / Research-Bridge
   - bewusst inaktiv
   - ADRs und Guards vorhanden
   - kein Live-Runtime-Claim
   - Belege:
     - `docs/adr/ADR-026-Destination-Scoped-Dual-Bus-Guardrails.md`
     - `docs/adr/ADR-028-Research-Isolation-and-Advisory-Only-Retrieval.md`
     - `docs/adr/ADR-029-BSI-Audit-Ledger-Shadow-Pipeline-Anchoring.md`

2. Containerisierte Inference Plane
   - `ollama` und `vllm` im Compose nur auskommentiert
   - der produktive Inference-Pfad ist damit nicht voll im gehardeten Runtime-Stack verankert
   - Beleg:
     - `docker-compose.yml`
     - `README.md`

### Nicht gefunden als belastbarer Nachweis

1. DSFA / DPIA
2. Verzeichnis von Verarbeitungstaetigkeiten
3. TOM-Dokument
4. Loesch- und Aufbewahrungskonzept fuer alle Datenklassen
5. Berechtigungskonzept ausserhalb der Code-Rollenlogik
6. BCM/BCP mit RTO/RPO
7. Backup-/Restore-Evidenz fuer Postgres und MinIO
8. formale MDR-/SaMD-Einstufung
9. AI-Act-Governance-Paket
10. Patch-/Vulnerability-Management-Prozess fuer Images und Dependencies

## Harte Befunde nach Schweregrad

### 1. Kritisch: RabbitMQ-Handoffs laufen ohne nachgewiesene Transporthaertung

Der zentrale Message-Bus nutzt aktuell `amqp://` und Port `5672`, nicht `amqps://`, und die Runtime-Konfiguration erzwingt fuer RabbitMQ nur Credentials, aber keine TLS-Policy. Das ist fuer einen strengen Zero-Trust- und KRITIS-Massstab zu schwach, weil ueber diesen Pfad interne Auth-Kontexte, Tenant-Zuordnungen und Workflow-Metadaten transportiert werden.

Belege:

- `docker-compose.yml:98`
- `docker-compose.yml:41`
- `src/fhirbridge/core/config.py:94`

Bewertung:

- Architektonisch: rot
- BSI/KRITIS: rot
- DSGVO: gelb bis rot, je nach Personenbezug der Nachrichten und Betriebsumgebung

### 2. Kritisch: Inference- und Telemetrie-Pfad sind noch nicht voll KRITIS-gehaertet

Die LLM-Runtime nutzt standardmaessig HTTP fuer `OLLAMA_URL`, der Client baut `httpx.AsyncClient(...)` ohne explizite TLS-/CA-Policy fuer die Inference-Plane, und die OTel-Exportstrecke ist mit `http://jaeger:4317` plus `insecure=True` konfiguriert. Gleichzeitig ist die Inference-Engine im Compose gar nicht aktiv modelliert, sondern nur dokumentiert bzw. auskommentiert. Das passt nicht zu einem starken "air-gapped, zero-trust" Produktionsclaim.

Belege:

- `src/fhirbridge/core/config.py:64`
- `src/fhirbridge/core/llm.py:101`
- `src/fhirbridge/core/llm.py:354`
- `src/fhirbridge/core/telemetry.py:25`
- `src/fhirbridge/core/telemetry.py:26`
- `docker-compose.yml:489`
- `docker-compose.yml:507`
- `README.md:3`
- `README.md:13`

Einordnung:

- Positiv: Vor der LLM-Stufe wird echte Pseudonymisierung eingesetzt; der LLM sieht im Kern keine direkten Klartext-PHI.
- Negativ: Pseudonymisierte Gesundheitsdaten bleiben personenbezogene Daten im DSGVO-Sinn und gehoeren trotzdem in einen voll gehaerteten internen Transportpfad.

### 3. Kritisch: Organisatorische DSGVO- und Krankenhaus-Compliance ist im Repo nicht auditfaehig nachgewiesen

Der Code enthaelt viele gute technische Datenschutzmassnahmen, aber der Repo enthaelt keine belastbare DSFA/DPIA, kein VVT, kein ausformuliertes TOM-Dokument, kein durchgaengiges Loeschkonzept und kein formales Berechtigungs- oder Rollenmodell fuer den Gesamtbetrieb. Damit ist das Projekt technisch stark, aber regulatorisch noch nicht "krankenhaus-tauglich".

Besonders relevant:

- DSGVO Art. 9: Gesundheitsdaten sind besondere Kategorien personenbezogener Daten.
- DSGVO Art. 25: Datenschutz durch Technikgestaltung und datenschutzfreundliche Voreinstellungen.
- DSGVO Art. 30: Verzeichnis von Verarbeitungstaetigkeiten.
- DSGVO Art. 32: Sicherheit der Verarbeitung.
- DSGVO Art. 35: Datenschutz-Folgenabschaetzung.

Repo-Befund:

- gefunden: Threat Model, Control Mapping, Runbooks, Hardening Reports
- nicht gefunden: DSFA/DPIA, VVT, TOM, Loeschkonzept, BCM/BCP, Restore-Evidenz

### 4. Hoch: Das rechtliche Control Mapping ist noch nicht auf die aktuelle deutsche Rechtslage 2025/2026 umgestellt

Die Projektdokumentation argumentiert breit mit BSI-200-x, "KRITIS", "Stand der Technik" und historischer `§ 8a BSIG`-Logik. Deutschland hat aber inzwischen ein neues BSIG vom 2. Dezember 2025, in Kraft seit 6. Dezember 2025. Ein aktualisiertes, explizites Mapping des Projekts auf die neue Gesetzesstruktur sehe ich im Repo nicht.

Belege:

- neues BSIG: [gesetze-im-internet.de/bsig_2025/BJNR12D0B0025.html](https://www.gesetze-im-internet.de/bsig_2025/BJNR12D0B0025.html)
- aktuelle BSI-KritisV: [gesetze-im-internet.de/bsi-kritisv/BJNR095800016.html](https://www.gesetze-im-internet.de/bsi-kritisv/BJNR095800016.html)
- repo-internes Mapping: `docs/security/control-mapping.md`

Bewertung:

- Technisches Mapping ist da.
- Rechtliches Mapping auf den Stand 2026 ist noch unvollstaendig.

### 5. Hoch: Audit- und Security-Evidence ist noch nicht manipulationssicher genug

Security-Audit-Ereignisse werden aktuell in Postgres gespeichert. Gleichzeitig sagt die Projektdokumentation selbst, dass ein manipulationssicher verankerter Audit-Ledger erst fuer spaeter vorbereitet ist und derzeit bewusst nicht live ist. Fuer ein KRITIS-Krankenhaus reicht ein nur mutables Audit-Backend auf Dauer nicht.

Belege:

- `src/fhirbridge/core/database.py:201`
- `docs/security/control-mapping.md:15`
- `docs/security/threat-model.md:29`
- `docs/security/threat-model.md:60`

### 6. Hoch: Identitaets- und Bootstrap-Pfade enthalten noch Dev-Ausnahmen

Keycloak laeuft im Compose noch mit `start-dev`. Zusaetzlich verspricht `.env.example`, dass Bootstrap-Passwoerter beim ersten Login erzwungen geaendert werden, aber das Bootstrap-Skript setzt `requiredActions=[]` und erzwingt gerade keine Passwortaenderung.

Belege:

- `docker-compose.yml:379`
- `docker-compose.yml:381`
- `.env.example:63`
- `deploy/keycloak/bootstrap.sh:126`
- `deploy/keycloak/bootstrap.sh:131`

Bewertung:

- fuer lokale Dev/Test-Sessions akzeptabel
- fuer Krankenhaus-Produktivbetrieb nicht akzeptabel

### 7. Hoch: Container-Haertung ist inkonsistent

Das Ingestion-Image wechselt explizit auf `appuser`, die anderen produktiven Images aber nicht. Damit ist die Sicherheitsbaseline ueber die Services hinweg inkonsistent.

Belege:

- positiv: `Dockerfile.ingestion:23`
- ohne `USER`: `Dockerfile`, `Dockerfile.export`, `Dockerfile.dashboard`

### 8. Mittel: FHIR-Export nutzt ein statisches Bearer-Token statt kurzlebiger Service-Identitaet

Der Exportpfad ist positiv durch HTTPS und CA-Validierung abgesichert. Die Authentisierung gegen den Ziel-FHIR-Server basiert aber auf einem statischen `FHIR_AUTH_BEARER`. Das ist fuer produktive Krankenhausumgebungen schwacher als Client-Credentials oder mTLS-basierte Service-Identitaeten mit Rotation.

Belege:

- `src/fhirbridge/workers/fhir_export_worker.py:77`
- `src/fhirbridge/core/config.py:174`

### 9. Mittel: Repo-Doku ueberzeichnet den Haertungsgrad an einzelnen Stellen

Die README spricht von "air-gapped", "100% locally executed LLM inference" und "strict compliance". Gleichzeitig ist die Inference-Engine nicht im aktiven Compose modelliert, `.env.example` enthaelt veraltete/insecure Defaults fuer MinIO und HTTP fuer Ollama, und einzelne Live-Nachweise sind laut ADRs explizit noch offen.

Belege:

- `README.md:3`
- `README.md:9`
- `README.md:13`
- `.env.example:15`
- `.env.example:22`
- `docs/adr/ADR-022-Async-DB-Runtime-and-Controlled-Migrations.md:38`
- `docs/adr/ADR-023-Qdrant-Live-Evidence-Exception.md:24`
- `docs/adr/ADR-024-Keycloak-Live-Evidence-Exception.md:24`

## Was bereits stark ist

1. Boundary-only JWT plus internes Token-Exchange
   - sehr gute Zero-Trust-Richtung
   - keine Enduser-JWTs in Worker-Payloads

2. Transactional Outbox mit Lease-Renewal und Fail-Closed-Fencing
   - fuer verteilte Zustandskonsistenz klar ueber Durchschnitt

3. Claim-Check-Pattern mit Bucket-Trennung
   - Evidence, Processing und PHI-Vault sind logisch getrennt
   - Evidence bekommt Object-Lock-Metadaten

4. Manual Review als Pflichtpfad
   - fuer Krankenhausumgebungen fachlich und regulatorisch sinnvoll

5. Saubere Test- und Guard-Story
   - aktueller lokaler Lauf: `118 passed, 7 skipped`
   - Security-Posture-Skript gruen

6. Gute Selbstdisziplin in der Dokumentation
   - die Repo-Doku verschweigt offene Live-Nachweise nicht, sondern markiert sie als `nicht nachweisbar`

## Bewertung nach Regelwerk

### DSGVO

Status: `teilweise gut vorbereitet, aber nicht audit-ready`

Positiv:

- Pseudonymisierung vor der LLM-Stufe
- Backend-vermittelter Manual-Review-Pfad
- Rollentrennung im Boundary-Code
- HTTPS/CA-Validierung fuer FHIR-Export und Dashboard-API

Fehlt oder ist zu schwach:

- Art. 30 VVT
- Art. 35 DSFA/DPIA
- vollstaendiges TOM-Dokument
- Loesch-/Aufbewahrungsregeln fuer alle Artefaktklassen
- formaler Nachweis fuer Zweckbindung, Rechtsgrundlagen und Rollen von Verantwortlichem/Auftragsverarbeiter

### BSI / KRITIS / Krankenhausbetrieb

Status: `architektonisch stark, operativ noch nicht auf KRITIS-Niveau`

Positiv:

- starke Segregation der Servicezonen
- Transactional Outbox statt Mehrfachschreib-Antipattern
- Runbooks fuer Reconciliation und Security-Incidents
- Security-Checks und ADR-basierte Governance

Fehlt oder ist zu schwach:

- TLS/mTLS fuer RabbitMQ
- voll gehaertete Inference-Plane
- BCMS/Notfallmanagement mit RTO/RPO
- Backup-/Restore-Nachweise
- manipulationssichere Audit-Ablage
- updatebares Mapping auf aktuelle BSIG-2025-Struktur

### SGB V / ISiK / Interoperabilitaet

Status: `fachlich in guter Richtung, aber nicht formell nachgewiesen`

Positiv:

- FHIR- und ISiK-Naehe ist im Modell- und Exportpfad klar erkennbar
- gematik ISiK wird im Projekt erkennbar als Zielbild genutzt

Offen:

- kein sichtbarer formaler Nachweis gegen offizielle ISiK-Testartefakte oder Hersteller-Testwochen
- kein formales Konformitaetspaket fuer Produkt- oder Release-Freigabe

### MDR / Medical Device Regulation

Status: `haengt voll an der Intended Use`

Einschaetzung:

- Wenn das System rein fuer synthetische Daten, Forschung, interne Qualitaetssicherung oder streng advisory-only genutzt wird, ist eine MDR-Pflicht nicht automatisch gesetzt.
- Wenn das System aber in echten Krankenhausablaeufen klinische Informationen fuer Diagnose, Monitoring, Prognose, Therapie oder strukturierte Exportentscheidungen bereitstellt, dann ist eine MDR-/SaMD-Einstufung sehr wahrscheinlich zu pruefen.

Das Projekt hat bereits einen echten klinischen Exportpfad. Genau deshalb darf die Intended Use nicht implizit bleiben.

### EU AI Act

Status: `Governance jetzt vorbereiten, auch wenn Hauptpflichten erst spaeter voll greifen`

Zeitpunkte laut EU-Kommission/EUR-Lex:

- Inkrafttreten: `2024-08-01`
- Verbote und AI-Literacy-Pflichten seit: `2025-02-02`
- die meisten Regeln gelten ab: `2026-08-02`
- fuer High-Risk-AI in regulierten Produkten gelten teils spaetere Uebergangsfristen

Repo-Befund:

- kein sichtbares AI-Governance-Paket
- keine dokumentierte Rollen- und Verantwortungsmatrix fuer Anbieter/Deployer/Operator
- keine systematische Model-Governance, Drift-, Bias- oder Human-Oversight-Dokumentation ausser Manual Review

## Live-Evidence und Ausnahmen

Die folgenden Punkte sind im Repo sauber als offen markiert:

1. Postgres-Rollout-Evidence offen bis `2026-04-30`
   - `docs/adr/ADR-022-Async-DB-Runtime-and-Controlled-Migrations.md:40`

2. Keycloak-JWKS-Live-Evidence offen bis `2026-04-30`
   - `docs/adr/ADR-024-Keycloak-Live-Evidence-Exception.md:26`

3. Qdrant-Isolation-Live-Evidence offen bis `2026-05-15`
   - `docs/adr/ADR-023-Qdrant-Live-Evidence-Exception.md:26`

Das ist positiv ehrlich dokumentiert. Fuer einen echten KRITIS-Audit waeren diese Punkte trotzdem rote Nachweisluecken, solange sie nicht geschlossen sind.

## Gesamturteil nach Reifegrad

### Technische Architektur

`gut bis sehr gut`

Die Kernentscheidungen sind fuer ein Gesundheits-/KRITIS-nahes System erstaunlich sauber.

### Betriebsreife

`mittel`

Die Plattform wirkt wie eine ernsthafte Pre-Production-Basis, aber noch nicht wie ein freigegebener Krankenhausbetrieb.

### Datenschutz- und Rechtsreife

`mittel bis schwach`

Die Technik unterstuetzt Datenschutz gut, aber die formalen Pflichten und Nachweise fehlen.

### KRITIS-Tauglichkeit

`noch nicht gegeben`

Nicht wegen fehlender Architektur, sondern wegen fehlender Vollhaertung, fehlender Nachweiskette und fehlender organisatorischer Controls.

## Priorisierte Naechste Schritte

1. RabbitMQ auf TLS/mTLS und CA-validierte Service-Identitaeten umstellen.
2. Inference-Plane in den gehardeten Runtime-Stack ziehen oder den "air-gapped/zero-trust"-Claim herunterstufen.
3. DSFA, VVT, TOM, Loeschkonzept, Berechtigungskonzept und BCM/Restore-Nachweise als Repo-Artefakte aufbauen.
4. BSIG-2025/NIS2/BSI-KritisV-Mapping aktualisieren.
5. Keycloak aus `start-dev` herausfuehren und Bootstrap-Passwortprozess korrigieren.
6. Alle Runtime-Container auf Non-Root und engere Laufzeitrechte umstellen.
7. Manipulationssichere Audit-Ablage oder externe immutable Anchoring-Strategie nachziehen.
8. Intended Use fuer MDR und AI Act schriftlich festziehen.

## Externe Referenzen

- DSGVO / GDPR: [EUR-Lex, Regulation (EU) 2016/679](https://eur-lex.europa.eu/search.html?AU_CODED=EP_CONSIL&DC_CODED=3028&DTS_DOM=EU_LAW&FM_CODED=REG&SUBDOM_INIT=ALL_ALL&lang=en&qid=1748980644489&type=advanced)
- AI Act: [EUR-Lex, Regulation (EU) 2024/1689](https://eur-lex.europa.eu/eli/reg/2024/1689/)
- MDR: [EUR-Lex, Regulation (EU) 2017/745](https://eur-lex.europa.eu/eli/reg/2017/745/2024-07-09/eng)
- NIS2: [EUR-Lex, Directive (EU) 2022/2555](https://eur-lex.europa.eu/eli/dir/2022/2555/en)
- BSIG 2025: [gesetze-im-internet.de/bsig_2025/BJNR12D0B0025.html](https://www.gesetze-im-internet.de/bsig_2025/BJNR12D0B0025.html)
- BSI-KritisV: [gesetze-im-internet.de/bsi-kritisv/BJNR095800016.html](https://www.gesetze-im-internet.de/bsi-kritisv/BJNR095800016.html)
- SGB V § 373: [gesetze-im-internet.de/sgb_5/__373.html](https://www.gesetze-im-internet.de/sgb_5/__373.html)
- gematik ISiK: [fachportal.gematik.de/zielgruppen/primaersystemhersteller/isik](https://fachportal.gematik.de/zielgruppen/primaersystemhersteller/isik)
- BSI KRITIS Nachweise: [bsi.bund.de KRITIS Downloads](https://www.bsi.bund.de/DE/Themen/Regulierte-Wirtschaft/Kritische-Infrastrukturen/Service-fuer-KRITIS-Betreiber/KRITIS-Downloads/kritis-downloads.html)
- BSI zu B3S: [bsi.bund.de Branchenspezifische Sicherheitsstandards](https://www.bsi.bund.de/DE/Themen/Regulierte-Wirtschaft/Kritische-Infrastrukturen/Sektorspezifische-Infos-fuer-KRITIS-Betreiber/Finanz-und-Versicherungswesen/Branchenspezifische-Sicherheitsstandards/branchenspezifische-sicherheitsstandards_node.html)
