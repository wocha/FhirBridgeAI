"""
Batch KDL Synthesizer (Meta-Generation Script).

Uses the local Mistral LLM to auto-generate Pydantic models for various
KDL (Klinische Dokumentenklassen-Liste) document types.
Injects specific contextual standards (DIN, gematik/ISiK) into the prompt.

Usage:
    # Generate all 14 targets:
    python batch_generate_kdl_models.py

    # Generate only the first N targets (for testing):
    python batch_generate_kdl_models.py --limit 3
"""

import argparse
import asyncio
import logging
import os
import sys
import time

# Setup logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("kdl_batch_synthesizer")

# Ensure canonical LlmRetryClient is importable
sys.path.append(
    os.path.abspath(
        os.path.join(os.path.dirname(__file__), "..", "..", "integrating-local-llms", "scripts")
    )
)
try:
    from llm_retry_client import LlmConfig, LlmRetryClient
except ImportError as e:
    logger.error(f"Failed to import LlmRetryClient: {e}")
    sys.exit(1)


# ---------------------------------------------------------------------------
# KDL Target Registry
# Format: (KDL Code, Document Name, Expected Standard/Norm)
# ---------------------------------------------------------------------------

KDL_TARGETS: list[tuple[str, str, str]] = [
    # --- Existing 4 entries (Tier 8) ---
    (
        "AD010103",
        "Entlassungsbericht",
        "DIN 5008 für Geschäftsbriefe sowie KBV/gematik Vorgaben für eArztbriefe",
    ),
    (
        "LB120103",
        "Laborbefund Klinische Chemie",
        "ISiK Laborbefund Profil (strukturierte numerische Werte, Referenzbereiche, SI-Einheiten)",
    ),
    (
        "PT080102",
        "Histologischer Befund Pathologie",
        "TNM-Klassifikation und gängige pathologische Befundstrukturen (Makro/Mikroskopie)",
    ),
    (
        "MP030101",
        "Mutterpass",
        "G-BA Mutterschafts-Richtlinien und Struktur des physischen deutschen Mutterpasses",
    ),
    # --- New 10 entries (Tier 9) ---
    (
        "AN040101",
        "Anaesthesieprotokoll",
        "DGAI-Empfehlung zur Anästhesiedokumentation "
        "(Prämedikationsvisite, Narkoseführung, Aufwachraum-Verlauf)",
    ),
    (
        "VB050101",
        "Verlegungsbericht",
        "DIN 5008 Geschäftsbriefnorm + KBV eArztbrief-Richtlinie "
        "für interne und externe Verlegungen",
    ),
    (
        "KB060101",
        "Konsilbericht",
        "G-BA Qualitätssicherungs-Richtlinie, ISiK ServiceRequest Profil "
        "für konsiliarische Fragestellungen",
    ),
    (
        "RE070101",
        "Reha-Entlassungsbericht",
        "BAR Rahmenempfehlungen zum Reha-Entlassungsbericht "
        "(Reha-Ziele, Therapieergebnisse, sozialmedizinische Epikrise)",
    ),
    (
        "NA080101",
        "Notaufnahmeprotokoll",
        "DIVI Notaufnahmeprotokoll-Standard + CEDIS/MTS Triagesystem "
        "(Vitalparameter, Ersteinschätzung, Verlauf)",
    ),
    (
        "GB090101",
        "Geburtsbericht",
        "G-BA Mutterschafts-Richtlinien Abschnitt Geburt + DGGG-Leitlinien "
        "(Geburtsverlauf, Apgar, Nabelschnur-pH)",
    ),
    (
        "TP100101",
        "Transfusionsprotokoll",
        "Transfusionsgesetz (TFG) §14 Dokumentationspflichten + "
        "BÄK Richtlinie Hämotherapie (Blutgruppe, Kreuzprobe, Chargen)",
    ),
    (
        "WD110101",
        "Wunddokumentation",
        "DNQP Expertenstandard Pflege von Menschen mit chronischen Wunden "
        "(Wundart, -größe, -stadium, Fotodokumentation-Felder)",
    ),
    (
        "SP120101",
        "Sturzprotokoll",
        "DNQP Expertenstandard Sturzprophylaxe in der Pflege "
        "(Sturzhergang, Verletzungen, Risikofaktoren, Maßnahmen)",
    ),
    (
        "MK130101",
        "Medikationsplan",
        "Bundeseinheitlicher Medikationsplan (BMP) gemäß §31a SGB V "
        "(Wirkstoff, Stärke, Darreichungsform, Dosierungsschema, PZN)",
    ),
]


OUTPUT_FILE = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "auto_generated_kdl_models.py")
)


async def run_batch_synthesizer(limit: int | None = None) -> None:
    """Run the batch generation loop.

    Args:
        limit: If set, only process the first *limit* targets (useful for
               quick tests without burning through all targets).
    """
    targets = KDL_TARGETS

    # Attempt to load from JSON dictionary
    target_json_path = os.path.join(os.path.dirname(__file__), "kdl_targets.json")
    if os.path.exists(target_json_path):
        import json
        try:
            with open(target_json_path, encoding='utf-8') as f:
                data = json.load(f)
                targets = [(d["code"], d["name"], d["standard"]) for d in data]
            logger.info(f"Loaded {len(targets)} targets from {target_json_path}")
        except Exception as e:
            logger.error(f"Failed to load JSON targets: {e}, falling back to defaults")

    if limit:
        targets = targets[:limit]

    total_count = len(targets)

    logger.info("Starting Batch KDL Synthesizer...")
    logger.info(f"Targeting {total_count} document types. Output file: {OUTPUT_FILE}")

    # We use a lower temperature for code generation
    config = LlmConfig(temperature=0.2, max_tokens=4000)
    client = LlmRetryClient(config=config)

    # Initialize the output file with imports
    if not os.path.exists(OUTPUT_FILE):
        with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
            f.write(
                '"""\nAuto-Generated Pydantic Models for KDL Documents.\n'
                'Generated via Mistral Batch Synthesizer.\n"""\n\n'
            )
            f.write("from typing import List, Optional\n")
            f.write("from pydantic import BaseModel, Field\n\n")
            f.write("class KdlDocumentBase(BaseModel):\n")
            f.write("    kdl_code: str\n")
            f.write("    kdl_name: str\n")
            f.write("    patient_id: str\n")
            f.write("    document_date: str\n\n")

    # ── Timing bookkeeping ──────────────────────────────────────────
    timing_report: list[dict[str, str | float]] = []
    factory_start = time.monotonic()

    for idx, (kdl_code, name, standard) in enumerate(targets, start=1):
        logger.info(
            "[%d/%d] Generating Python Pydantic Schema for: %s (%s)",
            idx, total_count, name, kdl_code,
        )
        logger.info(f"Enforcing Standard: {standard}")

        system_context = (
            "Du bist ein Senior Python Architect für Health-IT (TI, gematik, ISiK). "
            "Deine Aufgabe ist es, robuste, strikt typisierte Pydantic `BaseModel` "
            "Klassen zu schreiben. "
            "Erzeuge ONLY syntaktisch korrekten Python Code, ohne Erklärungen "
            "oder Markdown-Blöcke (kein ```python)."
        )

        class_name = name.replace(" ", "").replace("-", "")

        prompt = (
            f"Stelle dir die fachlichen Anforderungen an das medizinische "
            f"Dokument '{name}' (KDL-Code: {kdl_code}) vor.\n"
            f"Befolge bei der Definition der Felder ZWINGEND diesen Standard: "
            f"{standard}\n\n"
            f"Aufgabe:\n"
            f"Schreibe eine Pydantic Klasse namens `{class_name}`, "
            f"die von `KdlDocumentBase` erbt. "
            f"Definiere alle inhaltlich relevanten Felder. "
            f"Nutze `Field(..., description='...')` um jedes Feld fachlich zu erklären.\n"
            f"Nutze wo sinnvoll Unter-Klassen (z.B. für Tabellenzeilen in "
            f"Laborwerten). Generiere nur den reinen, unformatierten Python-Code."
        )

        entry_start = time.monotonic()
        status = "OK"

        try:
            # We use `generate_text` because we want raw Python code, not JSON.
            generated_code = await client.generate_text(
                prompt=prompt,
                system_context=system_context,
            )

            # Clean up potential markdown formatting the LLM might stubbornly include
            if generated_code.startswith("```python"):
                generated_code = generated_code[9:]
            if generated_code.startswith("```"):
                generated_code = generated_code[3:]
            if generated_code.endswith("```"):
                generated_code = generated_code[:-3]

            generated_code = generated_code.strip()

            with open(OUTPUT_FILE, "a", encoding="utf-8") as f:
                f.write(f"\n# {'-' * 60}\n")
                f.write(f"# KDL: {kdl_code} - {name}\n")
                f.write(f"# Standard: {standard}\n")
                f.write(f"# {'-' * 60}\n\n")
                f.write(generated_code + "\n\n")

        except Exception as e:
            logger.error(f"Failed to generate schema for {kdl_code}: {e}")
            status = f"ERROR: {e}"

        entry_duration = time.monotonic() - entry_start
        elapsed_total = time.monotonic() - factory_start
        timing_report.append({
            "kdl_code": kdl_code,
            "name": name,
            "duration_s": round(entry_duration, 1),
            "status": status,
        })

        logger.info(
            "[%d/%d] %s (%s) — %.1fs  |  Elapsed total: %.1fs",
            idx, total_count, name, kdl_code, entry_duration, elapsed_total,
        )

        if idx < total_count:
            logger.info("Pausing 10s for VRAM cooldown...")
            time.sleep(10)

    # ── Final summary ───────────────────────────────────────────────
    total_elapsed = time.monotonic() - factory_start
    logger.info("")
    logger.info("=" * 70)
    logger.info("  KDL BATCH SYNTHESIZER — TIMING REPORT")
    logger.info("=" * 70)
    logger.info("%-4s  %-10s  %-30s  %8s  %s", "#", "KDL-Code", "Dokument", "Dauer", "Status")
    logger.info("-" * 70)
    for i, entry in enumerate(timing_report, start=1):
        logger.info(
            "%-4d  %-10s  %-30s  %7.1fs  %s",
            i, entry["kdl_code"], entry["name"], entry["duration_s"], entry["status"],
        )
    logger.info("-" * 70)
    ok_count = sum(1 for e in timing_report if e["status"] == "OK")
    err_count = total_count - ok_count
    logger.info(
        "Total: %d OK, %d errors  |  Wall time: %.1fs (%.1f min)",
        ok_count, err_count, total_elapsed, total_elapsed / 60,
    )
    logger.info("=" * 70)


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Batch KDL Synthesizer — auto-generate Pydantic models for KDL document types."
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=None,
        help="Only process the first N targets (useful for quick tests).",
    )
    args = parser.parse_args()
    asyncio.run(run_batch_synthesizer(limit=args.limit))


if __name__ == "__main__":
    main()
