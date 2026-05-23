# ADR-030: WSL/Linux Developer Runtime Baseline

## Status

Accepted

## Date

2026-05-20

## Context

The project is prepared for public release and needs reproducible local instructions that do not leak machine-local paths or require host-specific shell behavior. Previous evidence and runbook snippets mixed Linux container commands with Windows-native shell syntax, which repeatedly caused local execution friction and added noise to operational documentation.

The runtime stack itself is Linux-container based. The developer workflow is already oriented around WSL/Linux semantics: `docker compose`, Bash-compatible environment variables, forward-slash paths, and `python3` command execution.

## Decision

1. WSL/Linux is the canonical supported local developer runtime for this repository.
2. Repository documentation, runbooks, ADRs, evidence files, and agent workflows must use Bash-compatible command examples.
3. Public documentation must use `<project-root>` or forward-slash paths instead of machine-local host paths.
4. Python commands must use `python3`, `python3 -m pip`, and `python3 -m pytest` unless a script-specific runner documents a narrower requirement.
5. Windows-native shell syntax and host-local path examples are out of scope for this repository and must not be added to tracked docs.

## Consequences

- Positive: Public-release documentation is simpler, less host-specific, and easier to reproduce in WSL, Linux CI, and Linux containers.
- Positive: Sensitive local path leakage is reduced because examples use placeholders and forward-slash paths.
- Positive: Future troubleshooting can focus on the supported execution baseline instead of maintaining duplicate shell recipes.
- Negative: Contributors using other host shells must translate commands locally without expecting first-class repository documentation for that environment.

## Verification Hooks

- `docs/security/SECURITY-HARDENING-REPORT-2026-03-12.md`
- `docs/runbooks/manual-validation-e2e-2026-03-09.md`
- `.agents/workflows/run-ci-locally.md`
- `.agents/knowledge/wsl_linux_execution_rules.md`
