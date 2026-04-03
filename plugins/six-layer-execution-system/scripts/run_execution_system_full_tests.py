#!/usr/bin/env python3
from __future__ import annotations

import subprocess

from execution_system_paths import WORKSPACE
from run_execution_system_checks import discover_repo_tests_root, repo_test_env

REPO_TESTS = [
    ("maintenance-mode-smoke", "test_execution_system_maintenance_mode.py"),
    ("governance-smoke", "test_execution_system_governance_consistency.py"),
    ("status-freshness-smoke", "test_check_execution_system_status_freshness.py"),
    ("system-path-happy", "test_execution_system_path_chain.py"),
    ("system-path-hard-fail", "test_execution_system_path_hard_fail.py"),
    ("system-path-policy-gate", "test_execution_system_path_policy_gate.py"),
    ("system-path-closeout-blocked", "test_execution_system_path_closeout_blocked.py"),
    ("system-path-closeout-payload-identity", "test_execution_system_path_closeout_payload_identity.py"),
    ("system-path-focus-switch", "test_execution_system_path_focus_switch.py"),
    ("system-path-governance-drift", "test_execution_system_path_governance_drift.py"),
    ("system-path-focus-acceptance-drift", "test_execution_system_path_focus_acceptance_drift.py"),
    ("system-path-maintenance-focus-drift", "test_execution_system_path_maintenance_focus_drift.py"),
    ("system-path-closeout-ready-focus-drift", "test_execution_system_path_closeout_ready_focus_drift.py"),
    ("system-path-runner-hint-drift", "test_execution_system_path_runner_hint_drift.py"),
    ("system-path-parallel-wave", "test_execution_system_path_parallel_wave.py"),
    ("active-checker-smoke", "test_check_active_consistency.py"),
    ("task-slice-smoke", "test_check_task_slice_schema.py"),
    ("oversized-advisory-smoke", "test_check_oversized_migration_slices.py"),
    ("summary-footer-smoke", "test_run_execution_system_checks.py"),
    ("inspect-smoke", "test_inspect_execution_system.py"),
    ("closeout-state-smoke", "test_slice_closeout_state.py"),
    ("closeout-ready-smoke", "test_check_closeout_ready.py"),
    ("notification-tools-smoke", "test_notification_script_tools.py"),
    ("wrapper-and-runner-tools-smoke", "test_wrapper_and_runner_tools.py"),
    ("introspection-and-control-tools-smoke", "test_introspection_and_control_tools.py"),
    ("checker-helper-coverage-smoke", "test_checker_helper_coverage.py"),
    ("consistency-and-runner-helper-coverage-smoke", "test_consistency_and_runner_helper_coverage.py"),
    ("edge-branch-coverage-smoke", "test_edge_branch_coverage.py"),
]

PLUGIN_COMMANDS = [
    ("acceptance", ["python3", str(WORKSPACE / "scripts" / "accept_active_ledger_v2.py")]),
    ("runner", ["python3", str(WORKSPACE / "scripts" / "run_execution_system_checks.py")]),
]


def main() -> int:
    tests_root, tests_reason = discover_repo_tests_root()
    if tests_root is None:
        print("EXECUTION_SYSTEM_FULL_TESTS_UNAVAILABLE")
        print("- reason: repo-root tests directory is unavailable")
        print(f"- detail: {tests_reason or 'unknown'}")
        print("- note: full-tests require the source checkout with /tests present")
        return 2

    tests = [
        (name, ["python3", str(tests_root / test_name)])
        for name, test_name in REPO_TESTS
    ] + PLUGIN_COMMANDS

    failures: list[str] = []
    env = repo_test_env()

    for name, cmd in tests:
        print(f"==> [{name}] {' '.join(cmd)}")
        proc = subprocess.run(
            cmd,
            cwd=tests_root.parent,
            env=env,
            text=True,
            capture_output=True,
            check=False,
        )
        output = (proc.stdout + proc.stderr).strip()
        if output:
            print(output)
        if proc.returncode != 0:
            failures.append(name)

    print("EXECUTION_SYSTEM_FULL_TEST_SUMMARY")
    print(f"- total: {len(tests)}")
    print(f"- failed: {len(failures)}")
    print(f"- repo_tests_root: {tests_root}")
    if failures:
        for name in failures:
            print(f"- failed_test: {name}")
        print("EXECUTION_SYSTEM_FULL_TESTS_FAILED")
        return 1

    print("EXECUTION_SYSTEM_FULL_TESTS_OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
