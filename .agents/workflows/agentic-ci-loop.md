---
description: Die "Agentic CI/CD Loop" - Kontinuierliche Verbesserung und Dokumentation nach Abschluss einer Aufgabe.
---

# Agentic Continuous Improvement Loop

Dieser Workflow muss am Ende jeder erfolgreich abgeschlossenen Ticket-/Feature-Arbeit von einem Agenten durchgeführt werden, bevor dieser die Aufgabe an den Nutzer zurückmeldet.

// turbo-all

1. **Architektur-Extraktion (Review Phase)**
   - Lese die letzten vorgenommenen Code-Änderungen.
   - Prüfe: Wurden neue Abhängigkeiten eingeführt? Wurden Architektur-Entscheidungen (Trade-offs) getroffen (z.B., "Wir nutzen hier SQLite statt RabbitMQ, weil X")?

2. **ADR Updates (Architecture Decision Records)**
   - Falls maßgebliche architektonische Entscheidungen getroffen wurden, erstelle oder aktualisiere ein kurzes ADR in `docs/adr/`. Nutze das Format (Title, Status, Context, Decision, Consequences).

3. **Skill-Check & Update**
   - Lese den Skill, der primär für diese Aufgabe genutzt wurde.
   - Gibt es "Hacks", Workarounds oder Best-Practices, die im Chat erarbeitet wurden, aber in den Skripten/Anweisungen des Skills fehlen?
   - Aktualisiere die `SKILL.md` oder die Skripte des Skills, um diesen Vektor für den nächsten Kaltstart des Agenten zu sichern.

4. **Wissensgraphen-Wartung**
   - Wurden neue Vokabeln, Cloud-Zonen (1-7) oder Zusammenhänge etabliert? Aktualisiere die entsprechenden `.md` Dateien im `knowledge/` Verzeichnis.

5. **Self-Audit via System Reviewer**
   - Rufe den in den Skills definierten `system-reviewer` Mechanismus auf, um den neu geschriebenen Code gegen die "Anti-Patterns" (Stateful Sinner, Orphan Data, etc.) zu prüfen.
