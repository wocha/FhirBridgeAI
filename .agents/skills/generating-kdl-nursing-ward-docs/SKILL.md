---
name: generating-kdl-nursing-ward-docs
description: Skill for algorithmically generating daily nursing logs (KDL VL160105 / Pflegeberichte) to efficiently volumize synthetic longitudinal patient records.
---

# Generating NURSING_LOG events

This skill provides a programmatic, algorithmic way to generate synthetic daily nursing logs without using expensive LLM calls. The system relies on hardcoded diagnostic matching to output realistic daily shift protocol entries.

## Usage

The generator can be found at `.agents/skills/generating-kdl-nursing-ward-docs/scripts/simulate_nursing.py`.

```python
from _agents.skills.generating_kdl_nursing_ward_docs.scripts.simulate_nursing import generate_daily_nursing_log

nursing_doc = generate_daily_nursing_log(patient_state, current_date, fall_id)
# Returns a NursingWardDoc ready for PdfEngine
```
