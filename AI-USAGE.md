# AI Usage Disclosure

This document describes how AI assistance appears to have been used in this repository and how new public-release documentation was prepared. It is a disclosure aid, not a forensic provenance report.

The levels below are provenance labels, not quality grades. They estimate the role of AI from observable repository characteristics: structure, wording consistency, implementation style, comments, tests, and the known documentation request that produced this file.

## Disclosure Levels

| Level | Label | Meaning |
| --- | --- | --- |
| Level 1 | Human-Authored | Primarily authored by a human. AI use, if any, was incidental and did not materially shape the artifact. |
| Level 2 | Human-Directed AI Generation | A human provided goals, constraints, domain context, and review; AI produced substantial draft text or code. |
| Level 3 | AI-Assisted Engineering | Human and AI iterated on implementation, debugging, tests, or refactoring; final responsibility remains with the human maintainer. |
| Level 4 | AI-Generated Prototype or Scaffold | AI likely produced a first-pass artifact or large scaffold that requires human review before reuse. |
| Level 5 | AI-Refined | AI substantially rewrote, normalized, summarized, or release-polished existing material under human instruction. |

## Artifact-Level Estimates

| Artifact | Estimated level | Rationale |
| --- | --- | --- |
| `README.md` | Level 5 | Rewritten for public release from human-provided constraints and repo inspection. The release tone and limitation language were AI-refined and should be owner-reviewed. |
| `AI-USAGE.md` | Level 5 | Created as an AI-refined disclosure document using the requested EigenLint-style pattern and local repository inspection. |
| `LICENSE` | Level 2 | Standard MIT license text instantiated from human-provided copyright holder and year range. |
| `docs/adr/` | Level 2 | ADRs show strong human architectural direction and consistent AI-assisted formulation. The design intent appears human-directed; the prose likely used AI drafting. |
| `docs/architecture/` | Level 2 | Architecture notes and early ADRs appear to encode human-specified privacy and KRITIS constraints with AI-assisted wording. |
| `docs/security/` | Level 2-3 | Threat model, control mapping, hardening, and audit evidence are structured and systematic. They likely combine human security requirements with AI-assisted expansion and consistency work. |
| `docs/runbooks/` | Level 2-3 | Operational runbooks appear human-directed and AI-assisted, especially where procedural language is highly regular. |
| `src/fhirbridge/core/` | Level 2-3 | Core modules contain deliberate architectural patterns, validation, retry, storage, telemetry, and security checks. The consistency and comment style suggest AI-assisted engineering under human direction. |
| `src/fhirbridge/workers/` | Level 2-3 | Worker code reflects human-defined pipeline boundaries with AI-assisted implementation and error-handling patterns. |
| `src/fhirbridge/models/` | Level 2 | FHIR/ISiK models encode specific domain constraints. The structure appears human-directed, with AI likely helping draft Pydantic classes and comments. |
| `src/fhirbridge/ingestion/` | Level 2-3 | API code likely combines human-specified security boundaries with AI-assisted FastAPI implementation. |
| `src/fhirbridge/privacy/` | Level 2-3 | Pseudonymization and privacy utilities appear AI-assisted but guided by explicit Zero-Trust requirements. |
| `dashboard/` | Level 2-3 | The Streamlit dashboard appears to be an AI-assisted operational prototype rather than hand-polished production UI. |
| `deploy/` and `docker-compose.yml` | Level 2-3 | Deployment topology, security comments, and service segmentation suggest human architectural intent with AI-assisted scaffolding and iteration. |
| `scripts/` | Level 2-3 | Utility and security scripts likely mix human-directed validation intent with AI-assisted implementation. |
| `tests/` | Level 1-2 | Tests appear closer to human-authored or human-directed AI generation. Some architecture guard and runtime tests show AI-assisted consistency, but test intent is explicit and reviewable. |
| Synthetic data generators and assets | Level 2-3 | Synthetic generation artifacts appear human-directed with AI-assisted implementation, especially where medical scenario structure and repeatable generation logic meet. |
| `.agents/skills/` | Level 2-4 | Agent skills are specialized operational instructions and scripts. They likely include AI-generated scaffolds plus human domain constraints and iterative refinement. |

## Reflection On AI-Augmented Engineering Practice

FhirBridgeAI is a good example of AI-augmented engineering used as an accelerator for architecture exploration, documentation, boilerplate-heavy implementation, and review discipline. The strongest parts of the repository are not claims of finished product maturity, but the explicit trail of design decisions, safety constraints, and engineering trade-offs.

In regulated healthcare contexts, AI assistance does not reduce the need for human accountability. Any code path that touches PHI, authentication, persistence, message delivery, FHIR export, or clinical semantics requires independent human review, reproducible tests, threat modeling, and operational validation before production use.

The public-release stance of this repository is therefore intentionally modest: AI helped shape and refine parts of the work, but the repository should be reviewed as a prototype and methodology record, not as a validated clinical system.
