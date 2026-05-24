# Checkers and Protocols

## Canonical Local Entry Points

Use the repo's own scripts instead of recreating logic:

- checks runner: `<plugin-root>/scripts/run_execution_system_checks.py`
- repo-local development runner: `<repo-root>/tests/run_execution_system_checks.py`
- full-suite runner: `<plugin-root>/scripts/run_execution_system_full_tests.py`
- ACTIVE acceptance: `<plugin-root>/scripts/accept_active_ledger_v2.py`
- closeout flow: `<plugin-root>/scripts/complete_slice.py`

This skill ships a wrapper:

```bash
python3 scripts/run_local_execution_checks.py checks
python3 scripts/run_local_execution_checks.py full-tests
python3 scripts/run_local_execution_checks.py active
python3 scripts/run_local_execution_checks.py closeout-ready
```

Repo-local development tests live under `<repo-root>/tests/`.

- `run_execution_system_checks.py` always runs plugin-local checkers.
- It runs repo smoke tests only when the source checkout root is detectable and
  `/tests` exists.
- `run_execution_system_full_tests.py` requires that source checkout; outside
  it, the runner reports `unavailable` instead of failing with path or import
  errors.

## ACTIVE and Ledger

Primary parser and checker:

- `scripts/active_ledger.py`
- `scripts/check_active_consistency.py`
- `tests/test_check_active_consistency.py`

What `check_active_consistency.py` enforces:

- ledger meta presence
- focus activity existence
- activity type/status/autopilot/focus_rank shape
- roadmap/waiting/simple activity required fields
- focus activity doc pointers
- `last_commit` existence and drift detection
- waiting-focus invariants

## Demand Intake

- `scripts/check_demand_card_schema.py`
- `scripts/demand_card.py`
- `scripts/decomposition_engine.py`
- `scripts/exec_sys.py demand decompose`

Current implemented boundary:

- turns a natural-language request into generated `activities/<activity-id>/` artifacts and an `ACTIVE.md` entry
- keeps generation deterministic and repo-local
- classifies demand shape and picks a bounded decomposition strategy before rendering artifacts
- keeps high-risk or confirmation-required generated activities non-autopilot and activation-gated until explicitly confirmed
- validates demand-card schema separately from runtime truth

## Decomposition and Parallel-Wave Checkers

- `scripts/check_task_slice_schema.py` — validates per-slice files under `activities/<activity-id>/3-tasks/` for required fields (`phase_id`, `rollback_strategy`) and status-aware checks (`actual_execution_plan` when in_progress, `actual_outcome` when done)
- `scripts/check_task_dependency_graph.py`
- `scripts/check_parallel_safety.py`
- `scripts/check_active_wave_state.py`

Related smoke/path tests:

- `tests/test_check_task_slice_schema.py`
- `tests/test_check_generated_decomposition_consistency.py`
- `tests/test_check_task_dependency_graph.py`
- `tests/test_check_parallel_safety.py`
- `tests/test_check_active_wave_state.py`
- `tests/test_execution_system_path_demand_decompose.py`
- `tests/test_execution_system_path_parallel_wave.py`

Use these when modifying:

- task slice schema
- generated demand / roadmap / tasks / ACTIVE propagation
- dependency graph fields
- `parallel_safe` semantics
- ACTIVE wave-state fields

## Governance, Freshness, and Advisory Layer

- `scripts/check_execution_system_governance_consistency.py`
- `scripts/check_execution_system_status_freshness.py`
- `scripts/check_oversized_migration_slices.py`

Related tests:

- `tests/test_execution_system_governance_consistency.py`
- `tests/test_check_execution_system_status_freshness.py`
- `tests/test_check_oversized_migration_slices.py`
- governance/path drift suite:
  - `tests/test_execution_system_path_governance_drift.py`
  - `tests/test_execution_system_path_focus_acceptance_drift.py`
  - `tests/test_execution_system_path_maintenance_focus_drift.py`
  - `tests/test_execution_system_path_closeout_ready_focus_drift.py`
  - `tests/test_execution_system_path_runner_hint_drift.py`

## Closeout and Handoff Pipeline

Primary scripts:

- `scripts/check_closeout_ready.py`
- `scripts/create_slice_closeout.py`
- `scripts/build_slice_handoff.py`
- `scripts/check_slice_closeout.py`
- `scripts/complete_slice.py`

Important caches/state files:

- `local-state/last-slice-closeout.json`

Protocol rules:

- `prepare` must run checks + closeout-ready gate before artifact creation
- `payload` prints the canonical handoff payload
- when a new explicit closeout field is introduced, propagate it across artifact creation, payload output, checker validation, smoke tests, and docs in the same slice

Current explicit closeout identity fields:

- `activity_id`
- `current_focus_activity_id`

### Validation Selection Guide for Protocol Changes

Use the smallest test that actually proves the changed contract:

- Change only one closeout artifact field or checker invariant:
  - start with `tests/test_slice_closeout_state.py`
- Change only the closeout-ready gate semantics:
  - start with `tests/test_check_closeout_ready.py`
- Change a field that must survive artifact -> payload:
  - add or update a dedicated `tests/test_execution_system_path_*`
  - current example: `tests/test_execution_system_path_closeout_payload_identity.py`
- Change what the workspace treats as acceptance-worthy completion semantics:
  - update `docs/execution-system-spec-v1-acceptance-checklist.md` in the same slice
- Change runner composition or protocol behavior with possible drift impact:
  - rerun `python3 scripts/run_local_execution_checks.py full-tests`

For additive schema changes, the preferred order is:

1. artifact writer
2. payload surface
3. checker/verifier
4. nearest smoke test
5. path test when cross-surface propagation matters
6. spec / acceptance / testing inventory docs

## Full Test Matrix

The full runner currently aggregates:

- maintenance-mode smoke
- governance smoke
- status-freshness smoke
- happy-path chain
- hard-fail path
- policy-gate path
- closeout-blocked path
- focus-switch path
- governance-drift path
- focus/acceptance drift path
- maintenance-focus drift path
- closeout-ready focus drift path
- runner-hint drift path
- parallel-wave path
- checker smokes
- advisory smoke
- summary-footer smoke
- closeout-state smoke
- acceptance
- unified runner

Default validation boundary:

- prefer `checks` for normal edits
- use `full-tests` for protocol or runner changes
- keep background/unit style validation bounded around 60 seconds unless the task truly needs more

All direct `tests/test_*.py` references in this document are repo-root relative.
Run them from the source checkout root, not from inside `plugins/six-layer-execution-system/`.
