# AI Usage Disclosure

This project was developed with AI augmentation. This document discloses the
level of AI involvement per artifact category.

## Disclosure Levels

- **Level 1 - Human-Authored**: Written entirely by human, no AI input
- **Level 2 - Human-Directed AI Generation**: Human spec, AI drafting, human
  review
- **Level 3 - Human-AI Collaborative**: Iterative co-development
- **Level 4 - AI-Generated, Human-Reviewed**: AI primary, human gate
- **Level 5 - AI-Refined**: Light AI polish on human-authored content

## Per-Artifact Disclosure

| Artifact Category | Primary Level | Notes |
|---|---|---|
| 30 Architecture Decision Records | Level 2 | Human-specified decisions, AI-drafted reasoning, human review |
| Core Modules (outbox_dispatcher, migrations, etc.) | Level 2-3 | Mixed depending on complexity |
| Test Infrastructure | Level 2-3 | Tests written with AI assistance, contracts human-defined |
| Security Scripts | Level 2 | Human security requirements, AI implementation |
| Documentation (this README, etc.) | Level 2 | Human-directed, AI-drafted |
| Configuration Files | Level 1-2 | Mostly human, some AI templates |

## Reflection

AI-augmented engineering in regulated contexts requires explicit scope
discipline. This project was developed using AI tools (primarily Claude and
Codex) with strict prompt scoping, parallel branch isolation, and post-hoc
verification. AI suggestions were treated as drafts requiring human
validation, not as authoritative implementations.

The methodology and verification approach is documented in EigenState
(sibling project). Iterative refinement happens in commits visible in the
public history.
