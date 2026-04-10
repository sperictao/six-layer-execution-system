#!/usr/bin/env python3
from __future__ import annotations

from execution_system_suite import (
    ACCEPTANCE_PY_COMPILE_SPECS,
    ACCEPTANCE_SCRIPT_CHECK_SPECS,
    ADVISORY_SCRIPT_NAMES,
    CHECK_SCRIPT_NAMES,
    LOCAL_CHECK_MODES,
    PLUGIN_FULL_TEST_SPECS,
    REPO_SMOKE_TESTS,
    named_workspace_python_commands,
    workspace_python_command,
    workspace_python_commands,
)
import scripts.accept_active_ledger_v2 as acceptance
import scripts.run_execution_system_checks as checks
import scripts.run_execution_system_full_tests as full_tests
import scripts.run_local_execution_checks as local_checks


def expect_equal(name: str, actual, expected) -> None:
    if actual != expected:
        raise AssertionError(f"{name} drifted\nactual={actual!r}\nexpected={expected!r}")


def main() -> int:
    expect_equal("CHECKS", checks.CHECKS, workspace_python_commands(CHECK_SCRIPT_NAMES))
    expect_equal("ADVISORIES", checks.ADVISORIES, workspace_python_commands(ADVISORY_SCRIPT_NAMES))
    expect_equal("REPO_SMOKE_TESTS", tuple(checks.REPO_SMOKE_TESTS), REPO_SMOKE_TESTS)

    expected_local = {
        mode: workspace_python_command(script_name)
        for mode, script_name in LOCAL_CHECK_MODES.items()
    }
    expect_equal("LOCAL_CHECK_COMMANDS", local_checks.COMMANDS, expected_local)

    expect_equal(
        "PLUGIN_COMMANDS",
        full_tests.PLUGIN_COMMANDS,
        named_workspace_python_commands(PLUGIN_FULL_TEST_SPECS),
    )
    expected_acceptance_script_checks = named_workspace_python_commands(ACCEPTANCE_SCRIPT_CHECK_SPECS)
    expect_equal(
        "ACCEPTANCE_SCRIPT_CHECKS",
        acceptance.CHECKS[: len(expected_acceptance_script_checks)],
        expected_acceptance_script_checks,
    )
    expected_py_compile_names = [name for name, _ in ACCEPTANCE_PY_COMPILE_SPECS]
    actual_py_compile_names = [name for name, _ in acceptance.CHECKS[len(expected_acceptance_script_checks) :]]
    expect_equal("ACCEPTANCE_PY_COMPILE_NAMES", actual_py_compile_names, expected_py_compile_names)

    print("EXECUTION_SYSTEM_SUITE_REGISTRY_SMOKE_OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
