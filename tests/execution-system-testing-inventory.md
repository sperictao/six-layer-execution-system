# execution system testing inventory

## Purpose

This document records the current execution-system testing assets, their coverage layer,
and the most important remaining gaps.

It is the concrete inventory output for `ET-A.A1`.

This repo-root `tests/` copy is the authoritative source-checkout inventory.
The plugin-local `docs/execution-system-testing-inventory.md` file is now only
a compatibility pointer for standalone plugin copies and older durable references.

All `tests/test_*.py` paths below are repo-root relative development assets.
They now live under `<repo-root>/tests/`, not `<plugin-root>/scripts/`, and are
not distributed with standalone plugin copies.

Validation boundary:
- plugin-local checkers and acceptance entrypoints remain runnable from the
  plugin directory
- repo-local smoke tests and the full-suite runner require the source checkout
  with `/tests` present

---

## 1. Current test assets by layer

### 1.1 Layout / existence checks
Current state:
- partial

What exists:
- the acceptance checklist documents required structure and evidence
- the workspace currently has the expected core files and script entrypoints

What is missing:
- there is no dedicated automated layout checker yet
- file existence is still validated mostly indirectly via runtime checks and manual review

Primary references:
- `docs/execution-system-spec-v1-acceptance-checklist.md`
- `roadmaps/execution-system-testing-roadmap.md`
- `tasks/execution-system-testing-tasks.md`

### 1.2 Semantic / unit-style tests
Current state:
- strong

Existing tests:
- `tests/test_check_active_consistency.py`
- `tests/test_check_demand_card_schema.py`
- `tests/test_check_generated_decomposition_consistency.py`
- `tests/test_check_task_slice_schema.py`
- `tests/test_check_task_dependency_graph.py`
- `tests/test_check_parallel_safety.py`
- `tests/test_check_active_wave_state.py`
- `tests/test_check_oversized_migration_slices.py`
- `tests/test_run_execution_system_checks.py`
- `tests/test_slice_closeout_state.py`
- `tests/test_check_closeout_ready.py`
- `tests/test_execution_system_governance_consistency.py`
- `tests/test_check_execution_system_status_freshness.py`
- `tests/test_notification_script_tools.py`
- `tests/test_wrapper_and_runner_tools.py`
- `tests/test_introspection_and_control_tools.py`
- `tests/test_checker_helper_coverage.py`
- `tests/test_consistency_and_runner_helper_coverage.py`
- `tests/test_edge_branch_coverage.py`

Coverage summary:
- ACTIVE checker semantics
- demand-card schema semantics
- generated decomposition consistency semantics
- migrated task slice schema semantics
- task dependency graph semantics
- parallel safety semantics
- active wave-state pilot semantics
- governance consistency semantics
- status-freshness semantics for durable docs
- oversized advisory semantics with lower noise for focused hook-local slices
- execution summary footer semantics
- closeout artifact state semantics
- canonical closeout payload field semantics
- closeout-ready gate semantics
- notification state and closeout helper tool semantics
- plugin wrapper, repo path, and full-suite runner semantics
- inspection, focus control, maintenance control, and parser helper semantics
- pure checker helper branches across schema/dependency/parallel-wave/freshness/governance surfaces
- active-consistency helper branches and unified runner helper semantics
- notification / closeout / parser edge branches that were previously only hit indirectly

### 1.3 Execution-system path tests
Current state:
- medium; the main matrix exists, but several tests recently drifted from the live ledger semantics and required maintenance-mode updates

Existing tests:
- `tests/test_execution_system_path_chain.py`
- `tests/test_execution_system_path_demand_decompose.py`
- `tests/test_execution_system_path_hard_fail.py`
- `tests/test_execution_system_path_policy_gate.py`
- `tests/test_execution_system_path_closeout_blocked.py`
- `tests/test_execution_system_path_closeout_payload_identity.py`
- `tests/test_execution_system_path_focus_switch.py`
- `tests/test_execution_system_path_governance_drift.py`
- `tests/test_execution_system_path_focus_acceptance_drift.py`
- `tests/test_execution_system_path_maintenance_focus_drift.py`
- `tests/test_execution_system_path_closeout_ready_focus_drift.py`
- `tests/test_execution_system_path_runner_hint_drift.py`
- `tests/test_execution_system_path_parallel_wave.py`
- `tests/test_activity_recycle.py`
- `tests/test_notification_script_tools.py`
- `tests/test_wrapper_and_runner_tools.py`
- `tests/test_introspection_and_control_tools.py`
- `tests/test_checker_helper_coverage.py`
- `tests/test_consistency_and_runner_helper_coverage.py`
- `tests/test_edge_branch_coverage.py`

Covered path:
- hard-fail suite passes
- advisory exists
- acceptance passes
- closeout-ready success is covered when focus is roadmap-backed
- closeout-ready failure is covered when focus is intentionally non-roadmap
- hard-fail negative path
- policy-gate path
- closeout-blocked path
- synthetic closeout artifact -> queue -> payload identity path for explicit `current_focus_activity_id`
- focus-switch path
- governance drift path for resume-trigger recovery alignment
- governance drift path for resume-trigger parallel-dispatch alignment
- governance drift path for focus/acceptance gate alignment under `FOCUS_VALIDATION_POLICY_GATE` / `OK_WITH_POLICY_GATES`
- synthetic single-wave path coverage for execution-system parallel-wave semantics
- confirmed activity recycling path coverage for ACTIVE index removal, activity directory move, and `recycle/history.md`

Missing paths:
- governance drift is covered for the heartbeat rule, but not yet generalized across every governance contract
- future protocol changes may still require new dedicated execution-system path tests

### 1.4 Governance / maintenance checks
Current state:
- strong for the currently documented governance contract

What exists:
- maintenance mode documented
- reopen conditions documented
- re-entry protocol documented
- resume-style trigger rule documented
- resume-trigger recovery alignment documented
- resume-trigger parallel-dispatch alignment documented
- acceptance and focus-first behavior now align with policy-gate semantics
- `scripts/check_execution_system_governance_consistency.py`
- `tests/test_execution_system_governance_consistency.py`
- `tests/test_execution_system_path_governance_drift.py`

What is missing:
- broader governance-drift coverage beyond the current resume-trigger recovery alignment case
- broader inventory/docs coverage so every testing document reflects the same governance scope

---

## 2. Current executable entrypoints

### 2.1 Core acceptance and runner
- `python3 scripts/accept_active_ledger_v2.py`
- `python3 scripts/run_execution_system_checks.py`
- `python3 scripts/run_execution_system_full_tests.py`

Notes:
- `run_execution_system_checks.py` always executes checker scripts and marks
  repo smoke tests as `passed`, `skipped`, or `unavailable`
- `run_execution_system_full_tests.py` reports `unavailable` outside a source
  checkout instead of failing with missing-path errors

### 2.2 Checker / advisory scripts
- `scripts/check_active_consistency.py`
- `scripts/check_demand_card_schema.py`
- `scripts/check_generated_decomposition_consistency.py`
- `scripts/check_task_slice_schema.py`
- `scripts/check_task_dependency_graph.py`
- `scripts/check_parallel_safety.py`
- `scripts/check_active_wave_state.py`
- `scripts/check_execution_system_governance_consistency.py`
- `scripts/check_execution_system_status_freshness.py`
- `scripts/check_oversized_migration_slices.py`
- `scripts/check_slice_closeout.py`
- `scripts/check_closeout_ready.py`

### 2.3 Current smoke scripts
- `tests/test_check_active_consistency.py`
- `tests/test_check_demand_card_schema.py`
- `tests/test_check_generated_decomposition_consistency.py`
- `tests/test_check_task_slice_schema.py`
- `tests/test_check_task_dependency_graph.py`
- `tests/test_check_parallel_safety.py`
- `tests/test_check_active_wave_state.py`
- `tests/test_check_execution_system_governance_consistency.py`
- `tests/test_check_execution_system_status_freshness.py`
- `tests/test_check_oversized_migration_slices.py`
- `tests/test_run_execution_system_checks.py`
- `tests/test_slice_closeout_state.py`
- `tests/test_check_closeout_ready.py`
- `tests/test_execution_system_path_chain.py`
- `tests/test_execution_system_path_demand_decompose.py`
- `tests/test_execution_system_path_hard_fail.py`
- `tests/test_execution_system_path_policy_gate.py`
- `tests/test_execution_system_path_closeout_blocked.py`
- `tests/test_execution_system_path_closeout_payload_identity.py`
- `tests/test_execution_system_path_focus_switch.py`
- `tests/test_execution_system_path_governance_drift.py`
- `tests/test_execution_system_path_focus_acceptance_drift.py`
- `tests/test_execution_system_path_maintenance_focus_drift.py`
- `tests/test_execution_system_path_closeout_ready_focus_drift.py`
- `tests/test_execution_system_path_runner_hint_drift.py`
- `tests/test_execution_system_path_parallel_wave.py`
- `tests/test_activity_recycle.py`

---

## 3. Current strength assessment

### Strong coverage
- hard-fail checker semantics
- demand-card schema semantics
- generated decomposition consistency semantics
- dependency-graph and parallel-safety checker semantics
- advisory semantics
- summary footer semantics
- closeout artifact state semantics
- canonical closeout payload field semantics
- governance consistency semantics
- execution-system negative-path coverage for hard-fail / policy-gate / closeout-blocked / focus-switch / governance-drift
- explicit closeout payload identity path coverage for `current_focus_activity_id`
- focus/acceptance gate alignment drift coverage
- maintenance-mode vs approved non-execution-system focus drift coverage
- closeout-ready vs evolving focus activity drift coverage
- runner/summary-hint drift coverage
- synthetic single-wave parallel-wave path coverage
- acceptance and runner integration at the happy-path level
- notification helper tooling coverage
- wrapper, runner, inspection, and control-tooling coverage
- checker helper branch coverage
- active-consistency and runner helper branch coverage
- notification / closeout / parser edge-branch coverage

### Medium coverage
- end-to-end execution-system path coverage as a whole
- governance drift recovery messaging in the unified runner
- active wave-state hard-fail runner integration semantics and recovery messaging
- maintenance-mode transitions where the live focus is a first-class `waiting` activity instead of a runnable roadmap or non-execution-system activity
- final line-level branch closure until a fresh 100% report confirms there are no remaining helper gaps

### Weak coverage
- broader governance-drift matrix beyond the current resume-trigger recovery alignment case
- future protocol additions that could introduce new negative paths
- any residual script-level branch gaps surfaced by the next line-coverage audit

---

## 4. Immediate backlog implications

### Highest-value missing tests
1. broader governance-drift matrix tests beyond the current resume-trigger recovery alignment case
2. any remaining negative-path execution-system path cases discovered during future protocol changes
3. any residual script-level branch gaps discovered by the next line-coverage report

### Why these matter
- most of the original execution-system path matrix gaps are now covered
- the unified full-test entrypoint now exists, so the next risk is protocol drift rather than missing aggregation
- governance rules will likely keep evolving, so generalized drift tests will age better than one-off wording checks

---

## 5. Acceptance of ET-A.A1

`ET-A.A1` should be considered complete when:
- current tests are explicitly categorized by layer
- major missing paths are explicitly listed
- the testing roadmap and tasks docs remain aligned with this inventory

Current conclusion:
- this inventory reflects the current suite shape, but test health must be re-verified against the live ledger before claiming the path matrix is materially complete
- the unified full-test entrypoint is present and aligned with the current suite structure
- synthetic single-wave parallel-wave path coverage is landed in `tests/test_execution_system_path_parallel_wave.py`, but must stay synchronized with live fixture anchors
- focus/acceptance gate alignment drift coverage is landed in `tests/test_execution_system_path_focus_acceptance_drift.py`
- maintenance-mode drift coverage is landed in `tests/test_execution_system_path_maintenance_focus_drift.py`
- closeout-ready drift coverage is landed in `tests/test_execution_system_path_closeout_ready_focus_drift.py`
- closeout payload identity coverage is landed in `tests/test_execution_system_path_closeout_payload_identity.py`
- runner/summary-hint drift coverage is landed in `tests/test_execution_system_path_runner_hint_drift.py`
- notification state and closeout helper coverage is landed in `tests/test_notification_script_tools.py`
- wrapper / runner / path coverage is landed in `tests/test_wrapper_and_runner_tools.py`
- inspection / parser / control-tool coverage is landed in `tests/test_introspection_and_control_tools.py`
- checker helper branch coverage is landed in `tests/test_checker_helper_coverage.py`
- active-consistency and runner helper branch coverage is landed in `tests/test_consistency_and_runner_helper_coverage.py`
- notification / closeout / parser edge-branch coverage is landed in `tests/test_edge_branch_coverage.py`
- the next best slice is broader governance-drift hardening around live-ledger semantics, especially waiting-focus legality and stale health reporting
