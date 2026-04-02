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

Execution-system docs:

- `<plugin-root>/docs/execution-system-spec-v1.md`
- `<plugin-root>/docs/execution-system-maintenance-guardrails.md`
- `<plugin-root>/docs/execution-system-testing-inventory.md`
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
- `<plugin-root>/scripts/accept_active_ledger_v2.py`

Closeout/notification:

- `<plugin-root>/scripts/complete_slice.sh`
- `<plugin-root>/scripts/create_slice_closeout.py`
- `<plugin-root>/scripts/queue_slice_notification.py`
- `<plugin-root>/scripts/flush_slice_notifications.py`
- `<plugin-root>/scripts/send_slice_notification_payload.py`
- `<plugin-root>/scripts/requeue_inflight_notifications.py`
- `<plugin-root>/scripts/ack_slice_notification.py`

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

## Optional Local Install References

- `/Users/erictao/.openclaw/openclaw.json`

## Optional Upstream Runtime References

Package root:

- `/opt/homebrew/lib/node_modules/openclaw`

High-value upstream docs:

- `/opt/homebrew/lib/node_modules/openclaw/README.md`
- `/opt/homebrew/lib/node_modules/openclaw/docs/cli/agents.md`
- `/opt/homebrew/lib/node_modules/openclaw/docs/cli/sandbox.md`
- `/opt/homebrew/lib/node_modules/openclaw/docs/tools/multi-agent-sandbox-tools.md`
- `/opt/homebrew/lib/node_modules/openclaw/docs/zh-CN/pi.md`

Consult package internals only when you need upstream implementation details beyond the docs above.
