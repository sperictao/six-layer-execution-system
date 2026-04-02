#!/usr/bin/env python3
from __future__ import annotations

import os
import subprocess
from pathlib import Path

from execution_system_paths import WORKSPACE
PYTHONPATH = str(WORKSPACE)

TESTS = [
    ("maintenance-mode-smoke", ["python3", str(WORKSPACE / "scripts" / "test_execution_system_maintenance_mode.py")]),
    ("governance-smoke", ["python3", str(WORKSPACE / "scripts" / "test_execution_system_governance_consistency.py")]),
    ("status-freshness-smoke", ["python3", str(WORKSPACE / "scripts" / "test_check_execution_system_status_freshness.py")]),
    ("system-path-happy", ["python3", str(WORKSPACE / "scripts" / "test_execution_system_path_chain.py")]),
    ("system-path-hard-fail", ["python3", str(WORKSPACE / "scripts" / "test_execution_system_path_hard_fail.py")]),
    ("system-path-policy-gate", ["python3", str(WORKSPACE / "scripts" / "test_execution_system_path_policy_gate.py")]),
    ("system-path-closeout-blocked", ["python3", str(WORKSPACE / "scripts" / "test_execution_system_path_closeout_blocked.py")]),
    ("system-path-closeout-payload-identity", ["python3", str(WORKSPACE / "scripts" / "test_execution_system_path_closeout_payload_identity.py")]),
    ("system-path-focus-switch", ["python3", str(WORKSPACE / "scripts" / "test_execution_system_path_focus_switch.py")]),
    ("system-path-governance-drift", ["python3", str(WORKSPACE / "scripts" / "test_execution_system_path_governance_drift.py")]),
    ("system-path-focus-acceptance-drift", ["python3", str(WORKSPACE / "scripts" / "test_execution_system_path_focus_acceptance_drift.py")]),
    ("system-path-maintenance-focus-drift", ["python3", str(WORKSPACE / "scripts" / "test_execution_system_path_maintenance_focus_drift.py")]),
    ("system-path-closeout-ready-focus-drift", ["python3", str(WORKSPACE / "scripts" / "test_execution_system_path_closeout_ready_focus_drift.py")]),
    ("system-path-runner-hint-drift", ["python3", str(WORKSPACE / "scripts" / "test_execution_system_path_runner_hint_drift.py")]),
    ("system-path-parallel-wave", ["python3", str(WORKSPACE / "scripts" / "test_execution_system_path_parallel_wave.py")]),
    ("active-checker-smoke", ["python3", str(WORKSPACE / "scripts" / "test_check_active_consistency.py")]),
    ("task-slice-smoke", ["python3", str(WORKSPACE / "scripts" / "test_check_task_slice_schema.py")]),
    ("oversized-advisory-smoke", ["python3", str(WORKSPACE / "scripts" / "test_check_oversized_migration_slices.py")]),
    ("summary-footer-smoke", ["python3", str(WORKSPACE / "scripts" / "test_run_execution_system_checks.py")]),
    ("closeout-state-smoke", ["python3", str(WORKSPACE / "scripts" / "test_slice_closeout_state.py")]),
    ("closeout-ready-smoke", ["python3", str(WORKSPACE / "scripts" / "test_check_closeout_ready.py")]),
    ("acceptance", ["python3", str(WORKSPACE / "scripts" / "accept_active_ledger_v2.py")]),
    ("runner", ["python3", str(WORKSPACE / "scripts" / "run_execution_system_checks.py")]),
]


def main() -> int:
    failures: list[str] = []
    env = os.environ.copy()
    env["PYTHONPATH"] = PYTHONPATH

    for name, cmd in TESTS:
        print(f"==> [{name}] {' '.join(cmd)}")
        proc = subprocess.run(cmd, cwd=WORKSPACE, env=env, text=True, capture_output=True, check=False)
        output = (proc.stdout + proc.stderr).strip()
        if output:
            print(output)
        if proc.returncode != 0:
            failures.append(name)

    print("EXECUTION_SYSTEM_FULL_TEST_SUMMARY")
    print(f"- total: {len(TESTS)}")
    print(f"- failed: {len(failures)}")
    if failures:
        for name in failures:
            print(f"- failed_test: {name}")
        print("EXECUTION_SYSTEM_FULL_TESTS_FAILED")
        return 1

    print("EXECUTION_SYSTEM_FULL_TESTS_OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
