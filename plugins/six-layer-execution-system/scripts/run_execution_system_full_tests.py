#!/usr/bin/env python3
from __future__ import annotations

import subprocess

from active_ledger import parse_ledger
from execution_system_paths import WORKSPACE
from execution_system_suite import (
    FULL_REPO_TEST_SPECS,
    PLUGIN_FULL_TEST_SPECS,
    named_repo_test_commands,
    named_workspace_python_commands,
)
from run_execution_system_checks import discover_repo_tests_root, repo_test_env

PLUGIN_COMMANDS = named_workspace_python_commands(PLUGIN_FULL_TEST_SPECS)

EMPTY_LEDGER_SKIPPED_TESTS = {
    "maintenance-mode-smoke",
    "system-path-happy",
    "system-path-demand-decompose",
    "system-path-focus-switch",
    "system-path-focus-acceptance-drift",
    "system-path-parallel-wave",
    "exec-sys-smoke",
    "closeout-ready-smoke",
}


def ledger_is_empty() -> bool:
    ledger = parse_ledger(WORKSPACE / "ACTIVE.md")
    return ledger.current_focus_activity_id == "none" and not ledger.activity_index


def main() -> int:
    tests_root, tests_reason = discover_repo_tests_root()
    if tests_root is None:
        print("EXECUTION_SYSTEM_FULL_TESTS_UNAVAILABLE")
        print("- reason: repo-root tests directory is unavailable")
        print(f"- detail: {tests_reason or 'unknown'}")
        print("- note: full-tests require the source checkout with /tests present")
        return 2

    skipped: list[str] = []
    repo_specs = list(FULL_REPO_TEST_SPECS)
    if ledger_is_empty():
        repo_specs = [
            spec for spec in repo_specs
            if spec[0] not in EMPTY_LEDGER_SKIPPED_TESTS
        ]
        skipped = [
            name for name, _test_name in FULL_REPO_TEST_SPECS
            if name in EMPTY_LEDGER_SKIPPED_TESTS
        ]

    tests = named_repo_test_commands(tests_root, tuple(repo_specs)) + PLUGIN_COMMANDS

    failures: list[str] = []
    env = repo_test_env()

    for name in skipped:
        print(f"==> [{name}] skipped: empty ledger has no live focus activity")

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
    print(f"- skipped: {len(skipped)}")
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
