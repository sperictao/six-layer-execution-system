#!/usr/bin/env python3
from __future__ import annotations

import subprocess
from dataclasses import dataclass
from pathlib import Path

from execution_system_paths import WORKSPACE

CHECKS = [
    ["python3", str(WORKSPACE / "scripts" / "check_active_consistency.py")],
    ["python3", str(WORKSPACE / "scripts" / "test_check_active_consistency.py")],
    ["python3", str(WORKSPACE / "scripts" / "check_task_slice_schema.py")],
    ["python3", str(WORKSPACE / "scripts" / "test_check_task_slice_schema.py")],
    ["python3", str(WORKSPACE / "scripts" / "check_task_dependency_graph.py")],
    ["python3", str(WORKSPACE / "scripts" / "test_check_task_dependency_graph.py")],
    ["python3", str(WORKSPACE / "scripts" / "check_parallel_safety.py")],
    ["python3", str(WORKSPACE / "scripts" / "test_check_parallel_safety.py")],
    ["python3", str(WORKSPACE / "scripts" / "check_active_wave_state.py")],
    ["python3", str(WORKSPACE / "scripts" / "test_check_active_wave_state.py")],
    ["python3", str(WORKSPACE / "scripts" / "check_execution_system_governance_consistency.py")],
    ["python3", str(WORKSPACE / "scripts" / "test_execution_system_governance_consistency.py")],
    ["python3", str(WORKSPACE / "scripts" / "check_execution_system_status_freshness.py")],
    ["python3", str(WORKSPACE / "scripts" / "test_check_execution_system_status_freshness.py")],
]

ADVISORIES = [
    ["python3", str(WORKSPACE / "scripts" / "check_oversized_migration_slices.py")],
]


@dataclass
class ExecutionSystemSummary:
    hard_fail_status: str
    first_failing_command: str | None
    advisory_commands: list[str]


def recovery_hint_for_command(command: list[str]) -> str:
    script = Path(command[-1]).name
    if script == "check_active_consistency.py":
        return "repair ACTIVE.md or repo drift first"
    if script == "check_task_slice_schema.py":
        return "repair migrated task slice structure first"
    if script == "check_task_dependency_graph.py":
        return "repair slice dependency references or cycles before continuing"
    if script == "check_parallel_safety.py":
        return "repair unsafe parallel_safe declarations or missing shared_write_targets before continuing"
    if script == "check_active_wave_state.py":
        return "repair invalid ACTIVE wave-state fields or revert the pilot activity to lean non-wave execution before continuing"
    if script == "check_execution_system_governance_consistency.py":
        return "inspect spec/AGENTS/HEARTBEAT alignment and repair the drifted recovery rule"
    if script == "check_execution_system_status_freshness.py":
        return "remove baked-in full-suite health claims from durable docs and let live checks speak for current status"
    if script == "check_oversized_migration_slices.py":
        return "inspect warned slices and decide whether to split them or tighten wording"
    return "inspect the command output and repair the surfaced domain"


def build_summary(first_failure: str | None, advisory_hits: list[str]) -> ExecutionSystemSummary:
    return ExecutionSystemSummary(
        hard_fail_status="passed" if first_failure is None else "failed",
        first_failing_command=first_failure,
        advisory_commands=advisory_hits,
    )


def summary_footer(summary: ExecutionSystemSummary) -> list[str]:
    lines = ["EXECUTION_SYSTEM_SUMMARY"]
    lines.append(f"- hard_fail_status: {summary.hard_fail_status}")
    lines.append(
        f"- first_failing_command: {summary.first_failing_command or 'none'}"
    )

    if summary.advisory_commands:
        lines.append(f"- advisory_hits: {len(summary.advisory_commands)}")
        for advisory in summary.advisory_commands:
            lines.append(f"- advisory_command: {advisory}")
            lines.append(f"- recovery_hint: {recovery_hint_for_command(advisory.split())}")
    else:
        lines.append("- advisory_hits: 0")

    if summary.first_failing_command is not None:
        lines.append(
            f"- recovery_hint: {recovery_hint_for_command(summary.first_failing_command.split())}"
        )
    return lines


def collect_summary(print_output: bool = True) -> tuple[int, ExecutionSystemSummary]:
    first_failure: str | None = None
    advisory_hits: list[str] = []

    for command in CHECKS:
        pretty = " ".join(command)
        if print_output:
            print(f"==> {pretty}")
        completed = subprocess.run(command, cwd=WORKSPACE, check=False)
        if completed.returncode != 0:
            first_failure = pretty
            summary = build_summary(first_failure, advisory_hits)
            if print_output:
                print(f"EXECUTION_SYSTEM_CHECKS_FAILED: {pretty}")
                for line in summary_footer(summary):
                    print(line)
            return completed.returncode, summary

    for command in ADVISORIES:
        pretty = " ".join(command)
        if print_output:
            print(f"==> advisory: {pretty}")
        completed = subprocess.run(command, cwd=WORKSPACE, check=False)
        if completed.returncode == 0:
            advisory_hits.append(pretty)

    summary = build_summary(first_failure, advisory_hits)
    if print_output:
        print("EXECUTION_SYSTEM_CHECKS_OK")
        for line in summary_footer(summary):
            print(line)
    return 0, summary


def main() -> int:
    code, _summary = collect_summary(print_output=True)
    return code


if __name__ == "__main__":
    raise SystemExit(main())
