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

- `activities/` (new live activity directories)
- `recycle/` (historical activity directories and index)
- `docs/`
- `references/`
- `scripts/`
- `skills/`
- `local-state/` (ignored machine-local closeout and telemetry state)

---

## Execution-System-Owned Assets

Docs:

- `docs/execution-system-spec-v1.md`
- `docs/execution-system-maintenance-guardrails.md`
- `docs/execution-system-decomposition-upgrade-plan.md`
- `docs/execution-system-spec-v1-acceptance-checklist.md`
- `<repo-root>/tests/execution-system-testing-inventory.md` (source-checkout authority)

Activity history:

- `recycle/history.md`
- `recycle/activities/<activity-id>/`

Scripts:

- ACTIVE parser/checkers
- dependency/parallel-wave checkers
- governance/status checkers
- closeout + handoff scripts
- unified check runner
- unified full-test runner
