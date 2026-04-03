# Plugin Runtime Reference

## Scope

This reference records plugin runtime surface facts for the current installation.

To generate a live snapshot of the current environment, run:

```bash
python3 scripts/inspect_execution_system.py --format markdown
```

---

## Repository Runtime Surface

Key execution files:

- `skills/six-layer-execution-system/SKILL.md`
- `ACTIVE.md`
- `docs/execution-system-spec-v1.md`
- `docs/execution-system-maintenance-guardrails.md`
- `docs/execution-system-testing-inventory.md` (compatibility pointer)

Key execution directories:

- `contracts/`
- `roadmaps/`
- `tasks/`
- `decisions/`
- `memory/`
- `references/`
- `scripts/`
- `skills/`

---

## Execution-System-Owned Assets

Docs:

- `docs/execution-system-spec-v1.md`
- `docs/execution-system-maintenance-guardrails.md`
- `docs/execution-system-decomposition-upgrade-plan.md`
- `docs/execution-system-spec-v1-acceptance-checklist.md`
- `<repo-root>/tests/execution-system-testing-inventory.md` (source-checkout authority)

Roadmaps:

- `roadmaps/execution-system-spec-v1-roadmap.md`
- `roadmaps/execution-system-testing-roadmap.md`
- `roadmaps/execution-system-decomposition-upgrade-roadmap.md`

Tasks:

- `tasks/execution-system-spec-v1-tasks.md`
- `tasks/execution-system-testing-tasks.md`
- `tasks/execution-system-decomposition-upgrade-tasks.md`

Scripts:

- ACTIVE parser/checkers
- dependency/parallel-wave checkers
- governance/status checkers
- closeout + handoff scripts
- unified check runner
- unified full-test runner
