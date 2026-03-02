# Antigravity Skill Best Practices (Gemini 3.1)

These guidelines define how to build effective skills for Antigravity with Gemini 3.1. They are based on industry best practices optimized for Antigravity's workflow.

## 1. Core Principles

* **Concise is key:** The context window is shared. Only add context Antigravity doesn't already have. Ask: "Does the agent really need this explanation?"
* **Appropriate Degrees of Freedom:**
  * *High freedom (general instructions):* When many paths work and heuristics suffice (e.g., code reviews).
  * *Medium freedom (pseudocode/templates):* When patterns exist but adaptation is needed.
  * *Low freedom (specific scripts):* For fragile, consistency-critical operations (e.g., database migrations).
* **Optimize for Gemini:** Take into account specific strengths. Test for efficiency.

## 2. Structure and Metadata

* **Naming Conventions:**
  * Use consistent patterns, ideally **gerund form** (verb + -ing) or action-oriented names (e.g., `processing-pdfs`, `analyzing-data`).
  * Lowercase, numbers, and hyphens only.
  * Avoid vague names like `helper`, `utils`, or `tools`.
* **Effective Descriptions (`description`):**
  * This field is critical for discovery among hundreds of skills.
  * **Always write in the 3rd person** (e.g., "Extracts text from PDF files..."). Never "I can help you...".
  * Be specific: Describe **what** the skill does and **when** (triggers/context) to use it.
* **Progressive Disclosure:**
  * Keep `SKILL.md` (the main entry point) under 500 lines.
  * Offload detailed references, examples, or complex workflows into separate `.md` files (e.g., `REFERENCE.md`, `EXAMPLES.md`).
  * Reference these files clearly in `SKILL.md` so the agent knows when to use `view_file`.

## 3. Workflows and Feedback Loops

* **Checklists for Complex Tasks:** Break down operations into sequential steps. Provide markdown checklists for the agent to follow.
* **Plan-Validate-Execute:** For risky/complex changes using executable code, have the agent create a structured plan (e.g., `changes.json`) and validate it with a script before executing.

## 4. Content Guidelines and Patterns

* **Template Pattern:** Provide templates for output formats. Clarify if it's strict ("ALWAYS use this exact template") or flexible ("Sensible default, adapt as needed").
* **Examples Pattern:** Use few-shot prompting. If output quality depends on examples, provide input/output pairs.

## 5. Advanced: Scripts and Executables

* **Solve, don't punt:** Bundled scripts (`scripts/`) must handle errors explicitly instead of crashing and leaving the AI to fix them.
* **No "Magic Numbers":** Configuration parameters in scripts must be documented and justified.
* **Verifiable Intermediate Outputs:** Allow the agent to catch errors early via validation scripts.
