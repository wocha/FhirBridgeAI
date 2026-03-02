## System Review Checklist

Copy this checklist into your thought process or task boundary to track progress during the review.

- [ ] **Step 1: Identify Anti-Patterns**
  - Did the agent struggle with any code generation?
  - Were there repeated errors or test failures that could be prevented with better context?
  - Did the agent have to ask the user repeatedly for the same kind of configuration?

- [ ] **Step 2: Evaluate Missing Knowledge**
  - Is there domain-specific knowledge or architecture rules that should be codified into a Knowledge Item (KI)?
  - If yes, plan to create a KI with a clear summary and artifacts.

- [ ] **Step 3: Evaluate Skill Opportunities**
  - Were there manual, multi-step processes the agent performed repeatedly?
  - Could these be codified into a new skill with a utility script?
  - Could an existing skill be enhanced with a `changes.json` plan-validate-execute pattern?

- [ ] **Step 4: Draft Recommendations**
  - Formulate a concise list of actionable improvements to present to the user.

- [ ] **Step 5: Apply Skill Authoring Best Practices**
  - Ensure any proposed new skills adhere to:
    - Gerund naming (`creating-xyz` or similar action verb)
    - 3rd person descriptions
    - Proper use of progressive disclosure
    - No magic numbers in robust scripts
