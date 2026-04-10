#!/usr/bin/env python3
from __future__ import annotations

from pathlib import Path

from execution_system_paths import script_path

CHECK_SCRIPT_NAMES = (
    "check_active_consistency.py",
    "check_demand_card_schema.py",
    "check_generated_decomposition_consistency.py",
    "check_task_slice_schema.py",
    "check_task_dependency_graph.py",
    "check_parallel_safety.py",
    "check_active_wave_state.py",
    "check_execution_system_governance_consistency.py",
    "check_execution_system_status_freshness.py",
)

ADVISORY_SCRIPT_NAMES = (
    "check_oversized_migration_slices.py",
)

REPO_SMOKE_TESTS = (
    "test_check_active_consistency.py",
    "test_check_demand_card_schema.py",
    "test_check_generated_decomposition_consistency.py",
    "test_check_task_slice_schema.py",
    "test_check_task_dependency_graph.py",
    "test_check_parallel_safety.py",
    "test_check_active_wave_state.py",
    "test_execution_system_governance_consistency.py",
    "test_check_execution_system_status_freshness.py",
)

FULL_REPO_TEST_SPECS = (
    ("maintenance-mode-smoke", "test_execution_system_maintenance_mode.py"),
    ("governance-smoke", "test_execution_system_governance_consistency.py"),
    ("status-freshness-smoke", "test_check_execution_system_status_freshness.py"),
    ("system-path-happy", "test_execution_system_path_chain.py"),
    ("system-path-demand-decompose", "test_execution_system_path_demand_decompose.py"),
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
    ("demand-card-smoke", "test_check_demand_card_schema.py"),
    ("generated-decomposition-consistency-smoke", "test_check_generated_decomposition_consistency.py"),
    ("task-slice-smoke", "test_check_task_slice_schema.py"),
    ("oversized-advisory-smoke", "test_check_oversized_migration_slices.py"),
    ("summary-footer-smoke", "test_run_execution_system_checks.py"),
    ("inspect-smoke", "test_inspect_execution_system.py"),
    ("exec-sys-smoke", "test_exec_sys.py"),
    ("suite-registry-smoke", "test_execution_system_suite_registry.py"),
    ("closeout-state-smoke", "test_slice_closeout_state.py"),
    ("closeout-ready-smoke", "test_check_closeout_ready.py"),
    ("notification-tools-smoke", "test_notification_script_tools.py"),
    ("wrapper-and-runner-tools-smoke", "test_wrapper_and_runner_tools.py"),
    ("introspection-and-control-tools-smoke", "test_introspection_and_control_tools.py"),
    ("checker-helper-coverage-smoke", "test_checker_helper_coverage.py"),
    ("consistency-and-runner-helper-coverage-smoke", "test_consistency_and_runner_helper_coverage.py"),
    ("edge-branch-coverage-smoke", "test_edge_branch_coverage.py"),
)

PLUGIN_FULL_TEST_SPECS = (
    ("acceptance", "accept_active_ledger_v2.py"),
    ("runner", "run_execution_system_checks.py"),
)

LOCAL_CHECK_MODES = {
    "active": "check_active_consistency.py",
    "checks": "run_execution_system_checks.py",
    "full-tests": "run_execution_system_full_tests.py",
    "closeout-ready": "check_closeout_ready.py",
}

ACCEPTANCE_SCRIPT_CHECK_SPECS = (
    ("execution-system-suite", "run_execution_system_checks.py"),
    ("focus-first", "validate_focus_first.py"),
)

ACCEPTANCE_PY_COMPILE_SPECS = (
    ("parser-pycompile", "active_ledger.py"),
    ("focus-switch-tool-pycompile", "set_focus_activity.py"),
)


def workspace_python_command(script_name: str) -> list[str]:
    return ["python3", str(script_path(script_name))]


def repo_test_command(tests_root: Path, test_name: str) -> list[str]:
    return ["python3", str(tests_root / test_name)]


def workspace_python_commands(script_names: tuple[str, ...]) -> list[list[str]]:
    return [workspace_python_command(script_name) for script_name in script_names]


def named_workspace_python_commands(
    specs: tuple[tuple[str, str], ...]
) -> list[tuple[str, list[str]]]:
    return [
        (name, workspace_python_command(script_name))
        for name, script_name in specs
    ]


def named_repo_test_commands(
    tests_root: Path,
    specs: tuple[tuple[str, str], ...],
) -> list[tuple[str, list[str]]]:
    return [
        (name, repo_test_command(tests_root, test_name))
        for name, test_name in specs
    ]
