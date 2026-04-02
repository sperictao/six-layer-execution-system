# Checkers and Protocols

## Canonical Local Entry Points

Use the repo's own scripts instead of recreating logic:

- checks runner: `/Users/erictao/source/repos/six-layer-execution-system/scripts/run_execution_system_checks.py`
- full-suite runner: `/Users/erictao/source/repos/six-layer-execution-system/scripts/run_execution_system_full_tests.py`
- ACTIVE acceptance: `/Users/erictao/source/repos/six-layer-execution-system/scripts/accept_active_ledger_v2.py`
- closeout flow: `/Users/erictao/source/repos/six-layer-execution-system/scripts/complete_slice.sh`

This skill ships a wrapper:

```bash
python3 scripts/run_local_execution_checks.py checks
python3 scripts/run_local_execution_checks.py full-tests
python3 scripts/run_local_execution_checks.py active
python3 scripts/run_local_execution_checks.py closeout-ready
```

## ACTIVE and Ledger

Primary parser and checker:

- `scripts/active_ledger.py`
- `scripts/check_active_consistency.py`
- `scripts/test_check_active_consistency.py`

What `check_active_consistency.py` enforces:

- ledger meta presence
- focus activity existence
- activity type/status/autopilot/focus_rank shape
- roadmap/waiting/simple activity required fields
- focus activity doc pointers
- `last_commit` existence and drift detection
- waiting-focus invariants

## Decomposition and Parallel-Wave Checkers

- `scripts/check_task_slice_schema.py`
- `scripts/check_task_dependency_graph.py`
- `scripts/check_parallel_safety.py`
- `scripts/check_active_wave_state.py`

Related smoke/path tests:

- `scripts/test_check_task_slice_schema.py`
- `scripts/test_check_task_dependency_graph.py`
- `scripts/test_check_parallel_safety.py`
- `scripts/test_check_active_wave_state.py`
- `scripts/test_execution_system_path_parallel_wave.py`

Use these when modifying:

- task slice schema
- dependency graph fields
- `parallel_safe` semantics
- ACTIVE wave-state fields

## Governance, Freshness, and Advisory Layer

- `scripts/check_execution_system_governance_consistency.py`
- `scripts/check_execution_system_status_freshness.py`
- `scripts/check_oversized_migration_slices.py`

Related tests:

- `scripts/test_execution_system_governance_consistency.py`
- `scripts/test_check_execution_system_status_freshness.py`
- `scripts/test_check_oversized_migration_slices.py`
- governance/path drift suite:
  - `scripts/test_execution_system_path_governance_drift.py`
  - `scripts/test_execution_system_path_focus_acceptance_drift.py`
  - `scripts/test_execution_system_path_maintenance_focus_drift.py`
  - `scripts/test_execution_system_path_closeout_ready_focus_drift.py`
  - `scripts/test_execution_system_path_runner_hint_drift.py`

## Closeout and Notification Pipeline

Primary scripts:

- `scripts/check_closeout_ready.py`
- `scripts/create_slice_closeout.py`
- `scripts/check_slice_closeout.py`
- `scripts/queue_slice_notification.py`
- `scripts/flush_slice_notifications.py`
- `scripts/send_slice_notification_payload.py`
- `scripts/requeue_inflight_notifications.py`
- `scripts/ack_slice_notification.py`
- `scripts/complete_slice.sh`

Important caches/state files:

- `memory/last-slice-closeout.json`
- `memory/last-slice-notification.json`
- `memory/notifications-state.json`

Protocol rules:

- `prepare` must run checks + closeout-ready gate before artifact creation
- `payload` prints the canonical outbound payload
- `ack` finalizes delivery and clears caches
- `fail` moves inflight items back to pending
- when a new explicit closeout field is introduced, propagate it across artifact creation, queue/state persistence, payload output, checker validation, smoke tests, and docs in the same slice

Current explicit closeout identity fields:

- `activity_id`
- `current_focus_activity_id`

### Validation Selection Guide for Protocol Changes

Use the smallest test that actually proves the changed contract:

- Change only one closeout artifact field or checker invariant:
  - start with `scripts/test_slice_closeout_state.py`
- Change only the closeout-ready gate semantics:
  - start with `scripts/test_check_closeout_ready.py`
- Change a field that must survive artifact -> queue/state -> payload:
  - add or update a dedicated `scripts/test_execution_system_path_*`
  - current example: `scripts/test_execution_system_path_closeout_payload_identity.py`
- Change what the workspace treats as acceptance-worthy completion semantics:
  - update `docs/execution-system-spec-v1-acceptance-checklist.md` in the same slice
- Change runner composition or protocol behavior with possible drift impact:
  - rerun `python3 scripts/run_local_execution_checks.py full-tests`

For additive schema changes, the preferred order is:

1. artifact writer
2. queue/state persistence
3. payload surface
4. checker/verifier
5. nearest smoke test
6. path test when cross-surface propagation matters
7. spec / acceptance / testing inventory docs

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
