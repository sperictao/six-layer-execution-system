#!/usr/bin/env python3
from __future__ import annotations

import subprocess

from execution_system_suite import (
    FULL_REPO_TEST_SPECS,
    PLUGIN_FULL_TEST_SPECS,
    named_repo_test_commands,
    named_workspace_python_commands,
)
from run_execution_system_checks import discover_repo_tests_root, repo_test_env

PLUGIN_COMMANDS = named_workspace_python_commands(PLUGIN_FULL_TEST_SPECS)


def main() -> int:
    tests_root, tests_reason = discover_repo_tests_root()
    if tests_root is None:
        print("EXECUTION_SYSTEM_FULL_TESTS_UNAVAILABLE")
        print("- reason: repo-root tests directory is unavailable")
        print(f"- detail: {tests_reason or 'unknown'}")
        print("- note: full-tests require the source checkout with /tests present")
        return 2

    tests = named_repo_test_commands(tests_root, FULL_REPO_TEST_SPECS) + PLUGIN_COMMANDS

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
