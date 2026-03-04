# ADR-006: Principal Architect Review and The 5 Anti-Patterns

## Status

Accepted

## Context

As the FhirBridgeAi system grows in complexity and scales towards a Tier-1 Enterprise cloud-native architecture, it is essential to enforce strict architectural guidelines. Code generation and automated reviews by AI agents (specifically the `system-reviewer`) need a hardened, unambiguous set of rules to prevent degrading system integrity, security, and performance. Without explicit anti-patterns, the reviewer might focus on superficial code style rather than foundational cloud-native principles.

## Decision

We enforce a mandatory "Principal Cloud Architect & AI Advisor" review process as the final gatekeeper for all system changes. The AI `system-reviewer` must actively scan all chat sessions, code commits, and plans for the following **5 Critical Anti-Patterns**:

1. **THE EVENT LOOP BLOCKER**: Synchronous network or I/O calls inside asynchronous Python code.
2. **THE STATEFUL SINNER**: Writing or reading local state to/from disk in scalable worker nodes (must use S3 Claim-Check).
3. **THE SILENT FAILURE**: Exceptions that are caught but neither properly instrumented (OpenTelemetry) nor routed to a Dead-Letter-Queue.
4. **THE ORPHAN DATA**: Multi-step database write operations without a Distributed Transaction or Saga Pattern.
5. **THE NAKED ENDPOINT**: Processing requests without verifying authentication/authorization (Zero-Trust Violation).

If any of these anti-patterns are detected, the reviewer must raise an alert and require an explicit "Architectural Override Implementation Plan" before any code changes are made.

## Consequences

- **Positive:** Guarantees strict adherence to cloud-native (12-Factor App) and KRITIS-compliant best practices.
- **Positive:** Establishes a common vocabulary (e.g., "The Stateful Sinner") making code review feedback immediate and universally understood.
- **Negative:** Introduces friction ("Circuit Breaker") in the development process; agents cannot simply fix code but must generate discussion and plans when rules are broken.
- **Negative:** Requires deeper architectural reasoning for seemingly simple fixes, potentially slowing down rapid prototyping but ensuring enterprise-grade stability.
