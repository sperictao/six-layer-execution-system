# Source Map

Use this file to jump to the owning source of an execution-system detail.
Prefer repository-owned files first. Only consult local-install or upstream paths when the task genuinely depends on them.

## Local Runtime Truth

Core runtime root:

- `<plugin-root>`

Source checkout root for repo-local development assets:

- `<repo-root>`

Top-level control files:

- `<plugin-root>/skills/six-layer-execution-system/SKILL.md`
- `<plugin-root>/ACTIVE.md`
- `<plugin-root>/memory/working-buffer.md`
- `<plugin-root>/demands/`

Execution-system docs:

- `<plugin-root>/docs/execution-system-spec-v1.md`
- `<plugin-root>/docs/execution-system-maintenance-guardrails.md`
- `<repo-root>/tests/execution-system-testing-inventory.md`
- `<plugin-root>/docs/execution-system-testing-inventory.md` (compatibility pointer)
- `<plugin-root>/docs/execution-system-spec-v1-acceptance-checklist.md`
- `<plugin-root>/docs/execution-system-decomposition-upgrade-plan.md`
- `<plugin-root>/docs/active-ledger-v2.md`

Roadmaps:

- `<plugin-root>/roadmaps/execution-system-spec-v1-roadmap.md`
- `<plugin-root>/roadmaps/execution-system-testing-roadmap.md`
- `<plugin-root>/roadmaps/execution-system-decomposition-upgrade-roadmap.md`
- `<plugin-root>/roadmaps/active-ledger-v2-roadmap.md`

Tasks:

- `<plugin-root>/tasks/execution-system-spec-v1-tasks.md`
- `<plugin-root>/tasks/execution-system-testing-tasks.md`
- `<plugin-root>/tasks/execution-system-decomposition-upgrade-tasks.md`

Decisions:

- `<plugin-root>/decisions/runtime/2026-03-13-execution-system-focus-first.md`

## Local Runtime Scripts

Ledger/parser:

- `<plugin-root>/scripts/active_ledger.py`
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
- `<repo-root>/tests/run_execution_system_checks.py`
- `<plugin-root>/scripts/run_execution_system_full_tests.py`
- `<plugin-root>/scripts/accept_active_ledger_v2.py`

Closeout/handoff:

- `<plugin-root>/scripts/complete_slice.py`
- `<plugin-root>/scripts/create_slice_closeout.py`
- `<plugin-root>/scripts/build_slice_handoff.py`
- `<plugin-root>/scripts/check_slice_closeout.py`

Demand decomposition:

- `<plugin-root>/scripts/demand_card.py`
- `<plugin-root>/scripts/decomposition_engine.py`
- `<plugin-root>/scripts/exec_sys.py`

Representative repo-local tests:

- `<repo-root>/tests/test_check_active_consistency.py`
- `<repo-root>/tests/test_execution_system_governance_consistency.py`
- `<repo-root>/tests/test_execution_system_path_chain.py`
- `<repo-root>/tests/test_execution_system_path_hard_fail.py`
- `<repo-root>/tests/test_execution_system_path_policy_gate.py`
- `<repo-root>/tests/test_execution_system_path_parallel_wave.py`
- `<repo-root>/tests/test_run_execution_system_checks.py`
- `<repo-root>/tests/test_slice_closeout_state.py`

These tests exist only in the source checkout and are not shipped inside a
standalone plugin copy.

## Agent Runtime Reference

- `<plugin-root>/references/agent-runtime.md` — agent runtime, plugin loading, and environment variable reference
