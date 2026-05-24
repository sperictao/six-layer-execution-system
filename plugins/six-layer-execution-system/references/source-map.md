# Source Map (v3)

Use this file to jump to the owning source of an execution-system detail.
Prefer repository-owned files first. Only consult local-install or upstream paths when the task genuinely depends on them.

## Local Runtime Truth

Core runtime root:

- `<plugin-root>`

Source checkout root for repo-local development assets:

- `<repo-root>`

## Top-level Control Files

- `<plugin-root>/ACTIVE.md` — thin index (v3), ~58 lines
- `<plugin-root>/skills/six-layer-execution-system/SKILL.md` — prompt rule source of truth
- `<plugin-root>/local-state/last-slice-closeout.json` — local closeout artifact when present; ignored state, not distributed truth

## Per-Activity Resources (v3)

New live activities are created under `<plugin-root>/activities/<activity-id>/`:

```
activities/<activity-id>/
  card.md          ← activity card (was inline in ACTIVE.md v2)
  0-demand.md      ← demand intake (optional)
  1-contract.md    ← contract (optional)
  2-roadmap.md     ← roadmap
  3-tasks/         ← per-slice tasks files
  4-decisions/     ← decision records (optional)
  5-memory/        ← activity-specific memory (optional)
```

Current live activity state is not maintained in this source map. Read `ACTIVE.md`.
When `current_focus_activity_id` is `none`, no live activity is runnable.

## Recycled Resources

Confirmed recycled activities live under `<plugin-root>/recycle/activities/<activity-id>/`.
The durable historical index is `<plugin-root>/recycle/history.md`.
Recycled content is historical context, not live runtime truth.

## Cross-Activity Resources

- `<plugin-root>/docs/` — specs and design documents
- `<plugin-root>/references/` — templates, protocols, source maps
- `<plugin-root>/scripts/` — checkers, runners, utilities
- `<plugin-root>/skills/` — skill definitions

## Execution-System Docs

- `<plugin-root>/docs/execution-system-spec-v1.md`
- `<plugin-root>/docs/execution-system-maintenance-guardrails.md`
- `<plugin-root>/docs/execution-system-spec-v1-acceptance-checklist.md`
- `<plugin-root>/docs/execution-system-decomposition-upgrade-plan.md`
- `<plugin-root>/docs/active-ledger-v2.md`
- `<plugin-root>/docs/execution-system-testing-inventory.md`

## Scripts

Ledger/parser:
- `<plugin-root>/scripts/active_ledger.py` — v3: reads ACTIVE.md index + `activities/*/card.md`
- `<plugin-root>/scripts/set_focus_activity.py`
- `<plugin-root>/scripts/validate_focus_first.py`

Checkers:
- `<plugin-root>/scripts/check_active_consistency.py`
- `<plugin-root>/scripts/check_demand_card_schema.py`
- `<plugin-root>/scripts/check_task_slice_schema.py`
- `<plugin-root>/scripts/check_task_dependency_graph.py`
- `<plugin-root>/scripts/check_parallel_safety.py`
- `<plugin-root>/scripts/check_active_wave_state.py`
- `<plugin-root>/scripts/check_execution_system_governance_consistency.py`
- `<plugin-root>/scripts/check_execution_system_status_freshness.py`
- `<plugin-root>/scripts/check_oversized_migration_slices.py`
- `<plugin-root>/scripts/check_closeout_ready.py`
- `<plugin-root>/scripts/check_slice_closeout.py`

Runners:
- `<plugin-root>/scripts/run_execution_system_checks.py`
- `<plugin-root>/scripts/run_execution_system_full_tests.py`

Closeout/handoff:
- `<plugin-root>/scripts/complete_slice.py`
- `<plugin-root>/scripts/create_slice_closeout.py`
- `<plugin-root>/scripts/build_slice_handoff.py`

Demand decomposition:
- `<plugin-root>/scripts/demand_card.py`
- `<plugin-root>/scripts/decomposition_engine.py`
- `<plugin-root>/scripts/exec_sys.py`

Initialization:
- `<plugin-root>/scripts/init_execution_system.py` — initializes a new execution-system root from the current plugin template

## Repo-Local Tests

These tests exist only in the source checkout and are not shipped inside a standalone plugin copy.

- `<repo-root>/tests/test_check_active_consistency.py`
- `<repo-root>/tests/test_execution_system_governance_consistency.py`
- `<repo-root>/tests/test_execution_system_path_chain.py`
- `<repo-root>/tests/test_execution_system_path_hard_fail.py`
- `<repo-root>/tests/test_execution_system_path_policy_gate.py`
- `<repo-root>/tests/test_execution_system_path_parallel_wave.py`
- `<repo-root>/tests/test_run_execution_system_checks.py`
- `<repo-root>/tests/test_slice_closeout_state.py`

## Agent Runtime Reference

- `<plugin-root>/references/agent-runtime.md` — agent runtime, plugin loading, and environment variable reference
