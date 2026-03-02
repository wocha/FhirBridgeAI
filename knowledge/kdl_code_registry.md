# KDL Code Registry

Central lookup table for all KDL (Klinische Dokumentenlogistik) document codes used in FhirBridgeAI.

## Document Types

| KDL-Code | Dokumenttyp | Deutscher Name | Skill |
|---|---|---|---|
| `AD010103` | Arztbrief | Entlassungsbericht intern | `generating-kdl-discharge-summaries` |
| `AD010111` | Arztbrief | Ambulanzbrief / Kurzbericht | `generating-kdl-discharge-summaries` |
| `DG020000` | Diagnostik | Bildgebungsbefund (allgemein) | `generating-kdl-clinical-findings` |
| `DG020103` | Diagnostik | CT-Befund | `generating-kdl-clinical-findings` |
| `DG020110` | Diagnostik | Röntgenbefund | `generating-kdl-clinical-findings` |
| `LB120103` | Laborbefund | Klinisch-chemische Laborergebnisse | `generating-lab-results` |
| `OP150103` | OP-Dokumentation | OP-Bericht | `generating-kdl-clinical-findings` |
| `PT080102` | Pathologie | Histopathologischer Befund | `generating-kdl-clinical-findings` |
| `VL160105` | Verlaufsdokumentation | Pflegebericht / Pflegeverlauf | `generating-kdl-nursing-ward-docs` |

## Code Schema

KDL codes follow the pattern `XXNNNZZZ`:

| Segment | Meaning | Example |
|---|---|---|
| `XX` | Dokumentgruppe (AD=Arztbrief, DG=Diagnostik, LB=Labor, OP=OP, PT=Pathologie, VL=Verlauf) | `AD` |
| `NNN` | Numerische Untergruppe | `010` |
| `ZZZ` | Spezifische Variante | `103` |

## Usage

Skills reference these codes when setting `kdl_code` on generated `KdlDocumentBase` instances.
The code determines routing, archiving classification, and FHIR `Composition.type` mapping.
