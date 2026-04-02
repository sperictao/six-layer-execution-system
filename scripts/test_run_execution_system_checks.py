#!/usr/bin/env python3
from __future__ import annotations

import subprocess

from execution_system_paths import command_str
from scripts.run_execution_system_checks import build_summary, summary_footer
from test_workspace_clone import cloned_workspace, init_git_repo, workspace_env


def expect_contains(name: str, text: str, needle: str) -> None:
    if needle not in text:
        raise AssertionError(f"{name} missing expected text: {needle}\n{text}")


def main() -> int:
    advisory_command = command_str("check_oversized_migration_slices.py")
    active_command = command_str("check_active_consistency.py")
    dependency_command = command_str("check_task_dependency_graph.py")
    parallel_command = command_str("check_parallel_safety.py")
    active_wave_command = command_str("check_active_wave_state.py")
    governance_command = command_str("check_execution_system_governance_consistency.py")
    with cloned_workspace() as workspace:
        env = workspace_env(workspace)
        init_git_repo(workspace)
        proc = subprocess.run(
            ["python3", str(workspace / "scripts" / "run_execution_system_checks.py")],
            text=True,
            capture_output=True,
            check=False,
            env=env,
        )
        live_output = proc.stdout + proc.stderr
        if proc.returncode != 0:
            raise AssertionError(f"collect_summary should pass in the controlled workspace\n{live_output}")
        expect_contains("controlled-pass", live_output, "EXECUTION_SYSTEM_CHECKS_OK")
        expect_contains("controlled-pass", live_output, "EXECUTION_SYSTEM_SUMMARY")
        expect_contains("controlled-pass", live_output, "- hard_fail_status: passed")

    passed = "\n".join(
        summary_footer(
            build_summary(
                None,
                [advisory_command],
            )
        )
    )
    expect_contains("pass-path", passed, "EXECUTION_SYSTEM_SUMMARY")
    expect_contains("pass-path", passed, "- hard_fail_status: passed")
    expect_contains("pass-path", passed, "- first_failing_command: none")
    expect_contains("pass-path", passed, "- advisory_hits: 1")
    expect_contains("pass-path", passed, "- recovery_hint: inspect warned slices and decide whether to split them or tighten wording")

    failed = "\n".join(
        summary_footer(
            build_summary(
                active_command,
                [],
            )
        )
    )
    expect_contains("fail-path", failed, "- hard_fail_status: failed")
    expect_contains("fail-path", failed, f"- first_failing_command: {active_command}")
    expect_contains("fail-path", failed, "- advisory_hits: 0")
    expect_contains("fail-path", failed, "- recovery_hint: repair ACTIVE.md or repo drift first")

    dependency_failed = "\n".join(
        summary_footer(
            build_summary(
                dependency_command,
                [],
            )
        )
    )
    expect_contains("dependency-fail-path", dependency_failed, f"- first_failing_command: {dependency_command}")
    expect_contains("dependency-fail-path", dependency_failed, "- recovery_hint: repair slice dependency references or cycles before continuing")

    parallel_failed = "\n".join(
        summary_footer(
            build_summary(
                parallel_command,
                [],
            )
        )
    )
    expect_contains("parallel-fail-path", parallel_failed, f"- first_failing_command: {parallel_command}")
    expect_contains("parallel-fail-path", parallel_failed, "- recovery_hint: repair unsafe parallel_safe declarations or missing shared_write_targets before continuing")

    active_wave_failed = "\n".join(
        summary_footer(
            build_summary(
                active_wave_command,
                [],
            )
        )
    )
    expect_contains("active-wave-fail-path", active_wave_failed, f"- first_failing_command: {active_wave_command}")
    expect_contains("active-wave-fail-path", active_wave_failed, "- recovery_hint: repair invalid ACTIVE wave-state fields or revert the pilot activity to lean non-wave execution before continuing")

    governance_failed = "\n".join(
        summary_footer(
            build_summary(
                governance_command,
                [],
            )
        )
    )
    expect_contains("governance-fail-path", governance_failed, f"- first_failing_command: {governance_command}")
    expect_contains("governance-fail-path", governance_failed, "- recovery_hint: inspect spec/AGENTS/HEARTBEAT alignment and repair the drifted recovery rule")

    print("EXECUTION_SYSTEM_RUNNER_SMOKE_OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
