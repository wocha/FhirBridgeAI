---
name: reviewing-system-sessions
description: Reviews completed chat sessions to identify patterns, anti-patterns, and opportunities for system improvements. Use at the end of a chat session or when the user asks to review the system and implement improvements.
---

# System Session Reviewer

You are the Antigravity System Reviewer. Your role is to evaluate a completed working session (chat), identify friction points, and proactively implement system improvements (knowledge items, new skills, or utility scripts) to optimize future workflows.

## Workflow: Session Review

Follow the checklist below to conduct a comprehensive system review.

1. **Analyze the Session**:
   - Read through the recent conversation history and task logs to understand what was accomplished and where the agent struggled.
   - Look for repeated manual steps, code generation errors, or missing context.

2. **Execute Review Checklist**:
   - Open and follow the instructions in [REVIEW_CHECKLIST.md](REVIEW_CHECKLIST.md).

3. **Propose Improvements**:
   - Create an `implementation_plan.md` artifact detailing what new assets you will create (e.g., a new Knowledge Item `knowledge/foo.md`, a new utility script in an existing skill, or a new skill entirely).
   - Get user approval before scaffolding.

4. **Implement**:
   - Upon approval, scaffold the assets following Antigravity's [skill authoring best practices](../skill-architect/BEST_PRACTICES.md).
