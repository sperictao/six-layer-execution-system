# Source Map

Use this file to jump to the original source of any execution-system detail.

## Local Runtime Truth

Core runtime root:

- `/Users/erictao/source/repos/six-layer-execution-system`

Top-level control files:

- `/Users/erictao/source/repos/six-layer-execution-system/AGENTS.md`
- `/Users/erictao/source/repos/six-layer-execution-system/ACTIVE.md`
- `/Users/erictao/source/repos/six-layer-execution-system/HEARTBEAT.md`
- `/Users/erictao/source/repos/six-layer-execution-system/MEMORY.md`
- `/Users/erictao/source/repos/six-layer-execution-system/TOOLS.md`
- `/Users/erictao/source/repos/six-layer-execution-system/SOUL.md`
- `/Users/erictao/source/repos/six-layer-execution-system/USER.md`

Execution-system docs:

- `/Users/erictao/source/repos/six-layer-execution-system/docs/execution-system-spec-v1.md`
- `/Users/erictao/source/repos/six-layer-execution-system/docs/execution-system-maintenance-guardrails.md`
- `/Users/erictao/source/repos/six-layer-execution-system/docs/execution-system-testing-inventory.md`
- `/Users/erictao/source/repos/six-layer-execution-system/docs/execution-system-spec-v1-acceptance-checklist.md`
- `/Users/erictao/source/repos/six-layer-execution-system/docs/execution-system-decomposition-upgrade-plan.md`
- `/Users/erictao/source/repos/six-layer-execution-system/docs/active-ledger-v2.md`

Roadmaps:

- `/Users/erictao/source/repos/six-layer-execution-system/roadmaps/execution-system-spec-v1-roadmap.md`
- `/Users/erictao/source/repos/six-layer-execution-system/roadmaps/execution-system-testing-roadmap.md`
- `/Users/erictao/source/repos/six-layer-execution-system/roadmaps/execution-system-decomposition-upgrade-roadmap.md`
- `/Users/erictao/source/repos/six-layer-execution-system/roadmaps/active-ledger-v2-roadmap.md`

Tasks:

- `/Users/erictao/source/repos/six-layer-execution-system/tasks/execution-system-spec-v1-tasks.md`
- `/Users/erictao/source/repos/six-layer-execution-system/tasks/execution-system-testing-tasks.md`
- `/Users/erictao/source/repos/six-layer-execution-system/tasks/execution-system-decomposition-upgrade-tasks.md`

Decisions:

- `/Users/erictao/source/repos/six-layer-execution-system/decisions/runtime/2026-03-13-execution-system-focus-first.md`

## Local Runtime Scripts

Ledger/parser:

- `/Users/erictao/source/repos/six-layer-execution-system/scripts/active_ledger.py`
- `/Users/erictao/source/repos/six-layer-execution-system/scripts/set_focus_activity.py`
- `/Users/erictao/source/repos/six-layer-execution-system/scripts/validate_focus_first.py`

Checkers:

- `/Users/erictao/source/repos/six-layer-execution-system/scripts/check_active_consistency.py`
- `/Users/erictao/source/repos/six-layer-execution-system/scripts/check_task_slice_schema.py`
- `/Users/erictao/source/repos/six-layer-execution-system/scripts/check_task_dependency_graph.py`
- `/Users/erictao/source/repos/six-layer-execution-system/scripts/check_parallel_safety.py`
- `/Users/erictao/source/repos/six-layer-execution-system/scripts/check_active_wave_state.py`
- `/Users/erictao/source/repos/six-layer-execution-system/scripts/check_execution_system_governance_consistency.py`
- `/Users/erictao/source/repos/six-layer-execution-system/scripts/check_execution_system_status_freshness.py`
- `/Users/erictao/source/repos/six-layer-execution-system/scripts/check_oversized_migration_slices.py`
- `/Users/erictao/source/repos/six-layer-execution-system/scripts/check_closeout_ready.py`
- `/Users/erictao/source/repos/six-layer-execution-system/scripts/check_slice_closeout.py`

Runners:

- `/Users/erictao/source/repos/six-layer-execution-system/scripts/run_execution_system_checks.py`
- `/Users/erictao/source/repos/six-layer-execution-system/scripts/run_execution_system_full_tests.py`
- `/Users/erictao/source/repos/six-layer-execution-system/scripts/accept_active_ledger_v2.py`

Closeout/notification:

- `/Users/erictao/source/repos/six-layer-execution-system/scripts/complete_slice.sh`
- `/Users/erictao/source/repos/six-layer-execution-system/scripts/create_slice_closeout.py`
- `/Users/erictao/source/repos/six-layer-execution-system/scripts/queue_slice_notification.py`
- `/Users/erictao/source/repos/six-layer-execution-system/scripts/flush_slice_notifications.py`
- `/Users/erictao/source/repos/six-layer-execution-system/scripts/send_slice_notification_payload.py`
- `/Users/erictao/source/repos/six-layer-execution-system/scripts/requeue_inflight_notifications.py`
- `/Users/erictao/source/repos/six-layer-execution-system/scripts/ack_slice_notification.py`

Representative tests:

- `/Users/erictao/source/repos/six-layer-execution-system/scripts/test_check_active_consistency.py`
- `/Users/erictao/source/repos/six-layer-execution-system/scripts/test_execution_system_governance_consistency.py`
- `/Users/erictao/source/repos/six-layer-execution-system/scripts/test_execution_system_path_chain.py`
- `/Users/erictao/source/repos/six-layer-execution-system/scripts/test_execution_system_path_hard_fail.py`
- `/Users/erictao/source/repos/six-layer-execution-system/scripts/test_execution_system_path_policy_gate.py`
- `/Users/erictao/source/repos/six-layer-execution-system/scripts/test_execution_system_path_parallel_wave.py`
- `/Users/erictao/source/repos/six-layer-execution-system/scripts/test_run_execution_system_checks.py`
- `/Users/erictao/source/repos/six-layer-execution-system/scripts/test_slice_closeout_state.py`

## Local State and Config

- `/Users/erictao/.openclaw/openclaw.json`
- `/Users/erictao/.openclaw/agents/`
- `/Users/erictao/.openclaw/credentials/`
- `/Users/erictao/.openclaw/logs/`
- workspace-local skills are intentionally omitted from this minimal repository copy

## Upstream Installed OpenClaw

Package root:

- `/opt/homebrew/lib/node_modules/openclaw`

High-value upstream docs:

- `/opt/homebrew/lib/node_modules/openclaw/README.md`
- `/opt/homebrew/lib/node_modules/openclaw/docs/cli/agents.md`
- `/opt/homebrew/lib/node_modules/openclaw/docs/cli/sandbox.md`
- `/opt/homebrew/lib/node_modules/openclaw/docs/tools/multi-agent-sandbox-tools.md`
- `/opt/homebrew/lib/node_modules/openclaw/docs/zh-CN/pi.md`

High-value upstream runtime files under `dist/`:

- `/opt/homebrew/lib/node_modules/openclaw/dist/entry.js`
- `/opt/homebrew/lib/node_modules/openclaw/dist/sandbox-DTlKNieF.js`
- `/opt/homebrew/lib/node_modules/openclaw/dist/exec-approvals-BF_Qfdq8.js`
- `/opt/homebrew/lib/node_modules/openclaw/dist/skills-M0AZJeXx.js`
- `/opt/homebrew/lib/node_modules/openclaw/dist/skill-scanner-Cp-qCAUj.js`
- `/opt/homebrew/lib/node_modules/openclaw/dist/agent-runner.runtime-qTIVwaGN.js`
- `/opt/homebrew/lib/node_modules/openclaw/dist/openclaw-tools.runtime-DWvpC-DV.js`
- `/opt/homebrew/lib/node_modules/openclaw/dist/tool-policy-match-DQWWRSN4.js`
- `/opt/homebrew/lib/node_modules/openclaw/dist/workspace-D4K6QX9X.js`
- `/opt/homebrew/lib/node_modules/openclaw/dist/workspace-dirs-DqDLiRvZ.js`

Bundled skills:

- `/opt/homebrew/lib/node_modules/openclaw/skills/`
