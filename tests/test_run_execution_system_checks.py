#!/usr/bin/env python3
from __future__ import annotations

import os
import json
import subprocess
import tempfile
from pathlib import Path

from execution_system_paths import WORKSPACE, command_str
from scripts.run_execution_system_checks import build_summary, summary_footer
from test_workspace_clone import cloned_workspace, init_git_repo, workspace_env


def expect_contains(name: str, text: str, needle: str) -> None:
    if needle not in text:
        raise AssertionError(f"{name} missing expected text: {needle}\n{text}")


def repo_checkout_without_tests_env() -> tuple[dict[str, str], Path]:
    temp_root = Path(tempfile.mkdtemp(prefix="six-layer-source-checkout-"))
    plugin_link = temp_root / "plugins" / WORKSPACE.name
    plugin_link.parent.mkdir(parents=True, exist_ok=True)
    plugin_link.symlink_to(WORKSPACE, target_is_directory=True)
    env = os.environ.copy()
    env["SIX_LAYER_SOURCE_REPO_ROOT"] = str(temp_root)
    return env, temp_root


def main() -> int:
    dev_runner = Path(__file__).with_name("run_execution_system_checks.py")
    advisory_command = command_str("check_oversized_migration_slices.py")
    active_command = command_str("check_active_consistency.py")
    demand_command = command_str("check_demand_card_schema.py")
    generated_consistency_command = command_str("check_generated_decomposition_consistency.py")
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
        expect_contains("controlled-pass", live_output, "- advisory_commands_run: 1")
        expect_contains("controlled-pass", live_output, "- advisory_hits: 0")
        expect_contains("controlled-pass", live_output, "- repo_smoke_tests: skipped")
        expect_contains("controlled-pass", live_output, "- repo_smoke_tests_reason: repo checkout not detected from plugin layout")
        telemetry_path = workspace / "local-state" / "telemetry.jsonl"
        if not telemetry_path.exists():
            raise AssertionError("run_execution_system_checks should emit telemetry into the workspace")
        try:
            telemetry_lines = telemetry_path.read_text(encoding="utf-8").splitlines()
        except OSError as error:
            raise AssertionError(f"telemetry file should be readable: {telemetry_path}") from error
        except UnicodeDecodeError as error:
            raise AssertionError(f"telemetry file should be valid UTF-8: {telemetry_path}") from error
        telemetry_events = []
        for line in telemetry_lines:
            if not line.strip():
                continue
            try:
                telemetry_events.append(json.loads(line))
            except json.JSONDecodeError as error:
                raise AssertionError(f"telemetry should contain valid JSON lines: {line}") from error
        if not telemetry_events:
            raise AssertionError("run_execution_system_checks should write at least one telemetry event")
        latest_event = telemetry_events[-1]
        if latest_event.get("event_type") != "execution_system_check":
            raise AssertionError(f"unexpected telemetry event: {latest_event}")
        if "timestamp" not in latest_event:
            raise AssertionError(f"telemetry event should include a timestamp: {latest_event}")
        payload = latest_event.get("payload")
        if not isinstance(payload, dict):
            raise AssertionError(f"telemetry event should include a payload object: {latest_event}")
        if "elapsed_seconds" not in payload:
            raise AssertionError(f"telemetry payload should include elapsed_seconds: {latest_event}")

    with cloned_workspace() as workspace:
        env = workspace_env(workspace)
        init_git_repo(workspace)
        state_root = workspace / "custom-state-root"
        env["SIX_LAYER_STATE_ROOT"] = str(state_root)
        proc = subprocess.run(
            ["python3", str(workspace / "scripts" / "run_execution_system_checks.py")],
            text=True,
            capture_output=True,
            check=False,
            env=env,
        )
        output = proc.stdout + proc.stderr
        if proc.returncode != 0:
            raise AssertionError(f"runner should still pass with a custom state root\n{output}")
        telemetry_path = state_root / "telemetry.jsonl"
        if not telemetry_path.exists():
            raise AssertionError(
                "run_execution_system_checks should honor SIX_LAYER_STATE_ROOT for telemetry output"
            )

    unavailable_env, unavailable_root = repo_checkout_without_tests_env()
    unavailable_root_resolved = unavailable_root.resolve()
    try:
        proc = subprocess.run(
            ["python3", str(WORKSPACE / "scripts" / "run_execution_system_checks.py")],
            text=True,
            capture_output=True,
            check=False,
            env=unavailable_env,
        )
        unavailable_output = proc.stdout + proc.stderr
        if proc.returncode != 0:
            raise AssertionError(f"repo-checkout-without-tests should not fail checks\n{unavailable_output}")
        expect_contains("unavailable-live-path", unavailable_output, "EXECUTION_SYSTEM_REPO_SMOKE_TESTS_UNAVAILABLE")
        expect_contains("unavailable-live-path", unavailable_output, "- repo_smoke_tests: unavailable")
        expect_contains(
            "unavailable-live-path",
            unavailable_output,
            f"- repo_smoke_tests_reason: repo checkout detected at {unavailable_root_resolved}, but {unavailable_root_resolved / 'tests'} is missing",
        )

        proc = subprocess.run(
            ["python3", str(dev_runner)],
            text=True,
            capture_output=True,
            check=False,
            env=unavailable_env,
        )
        dev_runner_output = proc.stdout + proc.stderr
        if proc.returncode != 0:
            raise AssertionError(f"tests/run_execution_system_checks.py should behave like the plugin wrapper\n{dev_runner_output}")
        expect_contains("dev-runner-unavailable-path", dev_runner_output, "EXECUTION_SYSTEM_REPO_SMOKE_TESTS_UNAVAILABLE")
        expect_contains("dev-runner-unavailable-path", dev_runner_output, "- repo_smoke_tests: unavailable")

        proc = subprocess.run(
            ["python3", str(WORKSPACE / "scripts" / "run_execution_system_full_tests.py")],
            text=True,
            capture_output=True,
            check=False,
            env=unavailable_env,
        )
        full_tests_output = proc.stdout + proc.stderr
        if proc.returncode != 2:
            raise AssertionError(f"full-tests unavailable path should exit 2\n{full_tests_output}")
        expect_contains("full-tests-unavailable", full_tests_output, "EXECUTION_SYSTEM_FULL_TESTS_UNAVAILABLE")
        expect_contains("full-tests-unavailable", full_tests_output, "- reason: repo-root tests directory is unavailable")
    finally:
        plugin_link = unavailable_root / "plugins" / WORKSPACE.name
        if plugin_link.exists() or plugin_link.is_symlink():
            plugin_link.unlink()
        (unavailable_root / "plugins").rmdir()
        unavailable_root.rmdir()

    passed = "\n".join(
        summary_footer(
            build_summary(
                None,
                [advisory_command],
                advisory_commands_run=1,
                repo_smoke_tests_status="passed",
                repo_smoke_tests_total=9,
                repo_smoke_tests_root="/tmp/source-checkout/tests",
            )
        )
    )
    expect_contains("pass-path", passed, "EXECUTION_SYSTEM_SUMMARY")
    expect_contains("pass-path", passed, "- hard_fail_status: passed")
    expect_contains("pass-path", passed, "- first_failing_command: none")
    expect_contains("pass-path", passed, "- advisory_commands_run: 1")
    expect_contains("pass-path", passed, "- advisory_hits: 1")
    expect_contains("pass-path", passed, f"- advisory_hit_command: {advisory_command}")
    expect_contains("pass-path", passed, "- repo_smoke_tests: passed")
    expect_contains("pass-path", passed, "- repo_smoke_tests_total: 9")
    expect_contains("pass-path", passed, "- repo_smoke_tests_root: /tmp/source-checkout/tests")
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
    expect_contains("fail-path", failed, "- advisory_commands_run: 0")
    expect_contains("fail-path", failed, "- advisory_hits: 0")
    expect_contains("fail-path", failed, "- recovery_hint: repair ACTIVE.md or repo drift first")

    demand_failed = "\n".join(
        summary_footer(
            build_summary(
                demand_command,
                [],
            )
        )
    )
    expect_contains("demand-fail-path", demand_failed, f"- first_failing_command: {demand_command}")
    expect_contains("demand-fail-path", demand_failed, "- recovery_hint: repair malformed demand intake fields before continuing")

    generated_consistency_failed = "\n".join(
        summary_footer(
            build_summary(
                generated_consistency_command,
                [],
            )
        )
    )
    expect_contains(
        "generated-consistency-fail-path",
        generated_consistency_failed,
        f"- first_failing_command: {generated_consistency_command}",
    )
    expect_contains(
        "generated-consistency-fail-path",
        generated_consistency_failed,
        "- recovery_hint: repair generated demand, roadmap, tasks, and ACTIVE drift before continuing",
    )

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
    expect_contains("governance-fail-path", governance_failed, "- recovery_hint: inspect spec/skill alignment and repair the drifted recovery rule")

    skipped = "\n".join(
        summary_footer(
            build_summary(
                None,
                [],
                repo_smoke_tests_status="skipped",
                repo_smoke_tests_reason="repo checkout not detected from plugin layout",
            )
        )
    )
    expect_contains("skipped-path", skipped, "- repo_smoke_tests: skipped")
    expect_contains("skipped-path", skipped, "- repo_smoke_tests_reason: repo checkout not detected from plugin layout")

    unavailable = "\n".join(
        summary_footer(
            build_summary(
                None,
                [],
                repo_smoke_tests_status="unavailable",
                repo_smoke_tests_reason="repo checkout detected at /tmp/source-checkout, but /tmp/source-checkout/tests is missing",
            )
        )
    )
    expect_contains("unavailable-path", unavailable, "- repo_smoke_tests: unavailable")
    expect_contains(
        "unavailable-path",
        unavailable,
        "- repo_smoke_tests_reason: repo checkout detected at /tmp/source-checkout, but /tmp/source-checkout/tests is missing",
    )

    print("EXECUTION_SYSTEM_RUNNER_SMOKE_OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
