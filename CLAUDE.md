# FhirBridgeAI Working Context

Active prototype for sovereign AI processing in KRITIS healthcare. 
See README.md for full context.

## Working Conventions

- Use Conventional Commits (feat:, fix:, docs:, chore:, test:, refactor:)
- Current public release is v0.1.0, default branch is main
- 130 passing tests in full suite, 13 skipped, 4 xfailed
- Reviewer smoke: `pytest tests/test_architecture_guards.py -v` (25 passed)
- ADRs in docs/adr/ are first-class and frozen for v0.1.0
- AI usage disclosed per artifact in AI-USAGE.md

## Working Style with AI Assistance

- Prefer minimal diff-based patches over full file rewrites
- Show plan before implementing
- Run tests after each meaningful change
- Stay strictly in scope, don't expand without asking
- Ask if unclear rather than assume

## Out of Scope

- ADR contents (frozen for v0.1.0)
- The 13 skipped tests (architecture has evolved past them)
- Production deployment scripts
- Full E2E integration tests (future v0.2)

## Active Work

Welle 1 of public-release polish: removing reviewer friction.
Identified Reviewer-Friction in src/fhirbridge/core/telemetry.py:
- OTLPSpanExporter imported at module level
- Hardcoded default endpoint http://jaeger:4317
- insecure=True hardcoded
These create implicit network assumptions for fresh-clone reviewers.

Plan it minimal, not as a rewrite.
