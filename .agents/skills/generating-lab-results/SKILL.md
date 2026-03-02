---
name: generating-lab-results
description: Algorithmic, non-LLM generation of medically plausible laboratory value progressions using deterministic Disease Multipliers. Use when generating synthetic lab results (KDL LB120103) that must be numerically consistent and biologically plausible.
---

# Generating Lab Results Skill

Dieser Skill generiert realistische KDL-Laborbefunde (LB120103) auf rein algorithmischer Basis, da LLMs häufig bei inkonsistenten Zahlenreihen ohne Kontextbezug versagen.

## Zweck

- Algorithmische, nicht-LLM gestützte Generierung von Laborergebnissen.
- Sicherstellung der biologischen Plausibilität und logischen Konsistenz (z.B. Verlauf über mehrere Tage).
- Nutzung von deterministischen "Disease Multipliers" basierend auf aktuellen Patientendiagnosen.

## Architektur

- **Templates:** In `templates/base_labs.json` sind die Referenzwerte eines gesunden Patienten (z.B. CRP = 2.5 mg/l, Leukozyten = 6.5 G/l) definiert.
- **Logik:** In `scripts/simulate_labs.py` ist die Rechenlogik implementiert. Pydantic-Modelle (`DiseaseMultiplier`) definieren, wie stark bestimmte Diagnosen (z.B. "Sepsis") die Referenzwerte beeinflussen (z.B. * 10 für CRP).
- **Abweichungen:** Für Realismus wird leichte Gaußsche Varianz (`random.gauss`) auf die errechneten Basiswerte angewendet, um bei jedem Aufruf leicht unterschiedliche, aber konsistente Werte zu erzeugen.

## Verwendung

Der Skill wird per Skript über `generate_correlating_labs(active_diagnoses, ...)` aufgerufen und liefert ein valides `fhirbridge.models.kdl_document.LabResults` Objekt zurück.
