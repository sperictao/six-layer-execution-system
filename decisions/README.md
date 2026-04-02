# Decisions

This directory stores durable rationale records.

Use decisions when:
- a long-lived constraint is chosen or changed
- multiple plausible options were compared
- a risky tradeoff was accepted on purpose
- future-you would likely forget why the current shape was chosen

Do not use decisions for:
- daily progress logs
- temporary notes
- raw chat transcript dumps
- duplicating ACTIVE runtime state

Suggested layout:
- `decisions/runtime/` for workspace-wide execution system decisions
- `decisions/<project>/` for project-specific architectural or sequencing decisions
