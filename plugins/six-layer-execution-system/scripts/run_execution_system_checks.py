#!/usr/bin/env python3
from __future__ import annotations

import os
import subprocess
from dataclasses import dataclass
from pathlib import Path

from active_ledger import parse_ledger
from execution_system_paths import WORKSPACE
from execution_system_paths import resolve_workspace_path
from execution_system_suite import (
    ADVISORY_SCRIPT_NAMES,
    CHECK_SCRIPT_NAMES,
    REPO_SMOKE_TESTS,
    repo_test_command,
    workspace_python_command,
    workspace_python_commands,
)
import telemetry

BASE_CHECKS = workspace_python_commands(CHECK_SCRIPT_NAMES)
# Backward-compatible export for tests and callers that inspect the static registry.
CHECKS = BASE_CHECKS
ADVISORIES = workspace_python_commands(ADVISORY_SCRIPT_NAMES)
GENERATED_TASK_DOC_CHECK_SCRIPT_NAMES = (
    "check_task_slice_schema.py",
    "check_task_dependency_graph.py",
    "check_parallel_safety.py",
)


@dataclass
class ExecutionSystemSummary:
    hard_fail_status: str
    first_failing_command: str | None
    advisory_commands: list[str]
    advisory_commands_run: int = 0
    repo_smoke_tests_status: str = "not-run"
    repo_smoke_tests_total: int = 0
    repo_smoke_tests_root: str | None = None
    repo_smoke_tests_reason: str | None = None


def _merged_pythonpath(extra_entries: list[Path] | None = None) -> str:
    entries = [str(WORKSPACE), str(WORKSPACE / "scripts")]
    if extra_entries:
        entries.extend(str(path) for path in extra_entries)
    existing = os.environ.get("PYTHONPATH")
    if existing:
        entries.extend(part for part in existing.split(os.pathsep) if part)

    deduped: list[str] = []
    seen: set[str] = set()
    for entry in entries:
        if entry in seen:
            continue
        deduped.append(entry)
        seen.add(entry)
    return os.pathsep.join(deduped)


def repo_test_env() -> dict[str, str]:
    env = os.environ.copy()
    env["PYTHONPATH"] = _merged_pythonpath()
    return env


def discover_repo_tests_root() -> tuple[Path | None, str | None]:
    candidates: list[Path] = []
    override = os.environ.get("SIX_LAYER_SOURCE_REPO_ROOT")
    if override:
        candidates.append(Path(override).expanduser())

    try:
        candidates.append(Path(__file__).resolve().parents[3])
    except IndexError:
        pass

    plugin_root = WORKSPACE.resolve()
    seen: set[Path] = set()
    for candidate in candidates:
        resolved_candidate = candidate.resolve()
        if resolved_candidate in seen:
            continue
        seen.add(resolved_candidate)

        plugin_candidate = resolved_candidate / "plugins" / plugin_root.name
        try:
            if plugin_candidate.resolve() != plugin_root:
                continue
        except FileNotFoundError:
            continue

        tests_root = resolved_candidate / "tests"
        if tests_root.exists():
            return tests_root, None
        return None, f"repo checkout detected at {resolved_candidate}, but {tests_root} is missing"

    return None, "repo checkout not detected from plugin layout"


def repo_test_commands(tests_root: Path) -> list[list[str]]:
    return [repo_test_command(tests_root, test_name) for test_name in REPO_SMOKE_TESTS]


def repo_smoke_status_for_reason(reason: str | None) -> str:
    if reason and reason.startswith("repo checkout detected at "):
        return "unavailable"
    return "skipped"


def generated_task_docs() -> list[Path]:
    try:
        ledger = parse_ledger(WORKSPACE / "ACTIVE.md")
    except Exception:
        return []

    docs: list[Path] = []
    seen: set[Path] = set()
    for activity in ledger.list_activities():
        if activity.scalar("type") != "roadmap":
            continue
        source_doc = (activity.scalar("source_doc") or "").strip()
        tasks_doc = (activity.scalar("tasks_doc") or activity.scalar("tasks_dir") or "").strip()
        if not (source_doc.startswith("demands/") or source_doc.startswith("activities/")) or not tasks_doc:
            continue
        if not (activity.activity_id or "").startswith("auto-"):
            continue

        resolved = resolve_workspace_path(tasks_doc)
        if resolved is None or resolved in seen:
            continue
        seen.add(resolved)
        docs.append(resolved)
    return docs


def generated_task_doc_commands() -> list[list[str]]:
    commands: list[list[str]] = []
    for task_doc in generated_task_docs():
        for script_name in GENERATED_TASK_DOC_CHECK_SCRIPT_NAMES:
            commands.append(workspace_python_command(script_name) + [str(task_doc)])
    return commands


def all_check_commands() -> list[list[str]]:
    commands: list[list[str]] = []
    for command in BASE_CHECKS:
        commands.append(command)
        if Path(command[-1]).name == "check_generated_decomposition_consistency.py":
            commands.extend(generated_task_doc_commands())
    return commands


def script_name_from_command(command: str | list[str]) -> str:
    tokens = command.split() if isinstance(command, str) else command
    for token in tokens:
        name = Path(token).name
        if name.endswith(".py"):
            return name
    return Path(tokens[-1]).name if tokens else ""


def advisory_warning_detected(output: str) -> bool:
    first_line = output.strip().splitlines()[0] if output.strip() else ""
    return first_line.endswith("_ADVISORY")


def recovery_hint_for_command(command: str | list[str]) -> str:
    script = script_name_from_command(command)
    if script == "check_active_consistency.py":
        return "repair ACTIVE.md or repo drift first"
    if script == "check_demand_card_schema.py":
        return "repair malformed demand intake fields before continuing"
    if script == "check_generated_decomposition_consistency.py":
        return "repair generated demand, roadmap, tasks, and ACTIVE drift before continuing"
    if script == "check_task_slice_schema.py":
        return "repair migrated task slice structure first"
    if script == "check_task_dependency_graph.py":
        return "repair slice dependency references or cycles before continuing"
    if script == "check_parallel_safety.py":
        return "repair unsafe parallel_safe declarations or missing shared_write_targets before continuing"
    if script == "check_active_wave_state.py":
        return "repair invalid ACTIVE wave-state fields or revert the pilot activity to lean non-wave execution before continuing"
    if script == "check_execution_system_governance_consistency.py":
        return "inspect spec/skill alignment and repair the drifted recovery rule"
    if script == "check_execution_system_status_freshness.py":
        return "remove baked-in full-suite health claims from durable docs and let live checks speak for current status"
    if script == "check_oversized_migration_slices.py":
        return "inspect warned slices and decide whether to split them or tighten wording"
    if script.startswith("test_"):
        return "inspect the failing repo smoke test and repair the drifted contract"
    return "inspect the command output and repair the surfaced domain"


def build_summary(
    first_failure: str | None,
    advisory_hits: list[str],
    *,
    advisory_commands_run: int = 0,
    repo_smoke_tests_status: str = "not-run",
    repo_smoke_tests_total: int = 0,
    repo_smoke_tests_root: str | None = None,
    repo_smoke_tests_reason: str | None = None,
) -> ExecutionSystemSummary:
    return ExecutionSystemSummary(
        hard_fail_status="passed" if first_failure is None else "failed",
        first_failing_command=first_failure,
        advisory_commands=advisory_hits,
        advisory_commands_run=advisory_commands_run,
        repo_smoke_tests_status=repo_smoke_tests_status,
        repo_smoke_tests_total=repo_smoke_tests_total,
        repo_smoke_tests_root=repo_smoke_tests_root,
        repo_smoke_tests_reason=repo_smoke_tests_reason,
    )


def summary_footer(summary: ExecutionSystemSummary) -> list[str]:
    lines = ["EXECUTION_SYSTEM_SUMMARY"]
    lines.append(f"- hard_fail_status: {summary.hard_fail_status}")
    lines.append(
        f"- first_failing_command: {summary.first_failing_command or 'none'}"
    )
    lines.append(f"- advisory_commands_run: {summary.advisory_commands_run}")

    if summary.advisory_commands:
        lines.append(f"- advisory_hits: {len(summary.advisory_commands)}")
        for advisory in summary.advisory_commands:
            lines.append(f"- advisory_hit_command: {advisory}")
            lines.append(f"- recovery_hint: {recovery_hint_for_command(advisory.split())}")
    else:
        lines.append("- advisory_hits: 0")

    lines.append(f"- repo_smoke_tests: {summary.repo_smoke_tests_status}")
    if summary.repo_smoke_tests_total:
        lines.append(f"- repo_smoke_tests_total: {summary.repo_smoke_tests_total}")
    if summary.repo_smoke_tests_root:
        lines.append(f"- repo_smoke_tests_root: {summary.repo_smoke_tests_root}")
    if summary.repo_smoke_tests_reason:
        lines.append(f"- repo_smoke_tests_reason: {summary.repo_smoke_tests_reason}")

    if summary.first_failing_command is not None:
        lines.append(
            f"- recovery_hint: {recovery_hint_for_command(summary.first_failing_command.split())}"
        )
    return lines


def build_telemetry_payload(result: tuple[int, ExecutionSystemSummary]) -> dict:
    code, summary = result
    return {
        "status": "passed" if code == 0 else "failed",
        "first_failing_command": summary.first_failing_command,
        "hard_fail_status": summary.hard_fail_status,
        "advisory_hits": len(summary.advisory_commands),
        "advisory_commands_run": summary.advisory_commands_run,
        "repo_smoke_tests_status": summary.repo_smoke_tests_status,
    }


@telemetry.with_telemetry("execution_system_check", payload_builder=build_telemetry_payload)
def collect_summary(print_output: bool = True) -> tuple[int, ExecutionSystemSummary]:
    first_failure: str | None = None
    advisory_hits: list[str] = []
    advisory_commands_run = 0

    for command in all_check_commands():
        pretty = " ".join(command)
        if print_output:
            print(f"==> {pretty}")
        completed = subprocess.run(command, cwd=WORKSPACE, check=False)
        if completed.returncode != 0:
            first_failure = pretty
            summary = build_summary(
                first_failure,
                advisory_hits,
                advisory_commands_run=advisory_commands_run,
            )
            if print_output:
                print(f"EXECUTION_SYSTEM_CHECKS_FAILED: {pretty}")
                for line in summary_footer(summary):
                    print(line)
            return completed.returncode, summary

    for command in ADVISORIES:
        pretty = " ".join(command)
        if print_output:
            print(f"==> advisory: {pretty}")
        completed = subprocess.run(command, cwd=WORKSPACE, text=True, capture_output=True, check=False)
        output = (completed.stdout + completed.stderr).strip()
        if print_output and output:
            print(output)
        advisory_commands_run += 1
        if completed.returncode == 0 and advisory_warning_detected(output):
            advisory_hits.append(pretty)

    tests_root, tests_reason = discover_repo_tests_root()
    if os.environ.get("SIX_LAYER_EXECUTION_MODE") == "agile":
        tests_reason = "agile mode enabled"
        tests_root = None

    if tests_root is None:
        repo_smoke_status = repo_smoke_status_for_reason(tests_reason)
        summary = build_summary(
            first_failure,
            advisory_hits,
            advisory_commands_run=advisory_commands_run,
            repo_smoke_tests_status=repo_smoke_status,
            repo_smoke_tests_reason=tests_reason,
        )
        if print_output:
            print(
                "EXECUTION_SYSTEM_REPO_SMOKE_TESTS_"
                f"{repo_smoke_status.upper()}: {tests_reason or 'unknown'}"
            )
            print("EXECUTION_SYSTEM_CHECKS_OK")
            for line in summary_footer(summary):
                print(line)
        return 0, summary

    for command in repo_test_commands(tests_root):
        pretty = " ".join(command)
        if print_output:
            print(f"==> repo-test: {pretty}")
        completed = subprocess.run(
            command,
            cwd=tests_root.parent,
            env=repo_test_env(),
            check=False,
        )
        if completed.returncode != 0:
            first_failure = pretty
            summary = build_summary(
                first_failure,
                advisory_hits,
                advisory_commands_run=advisory_commands_run,
                repo_smoke_tests_status="failed",
                repo_smoke_tests_total=len(REPO_SMOKE_TESTS),
                repo_smoke_tests_root=str(tests_root),
            )
            if print_output:
                print(f"EXECUTION_SYSTEM_CHECKS_FAILED: {pretty}")
                for line in summary_footer(summary):
                    print(line)
            return completed.returncode, summary

    summary = build_summary(
        first_failure,
        advisory_hits,
        advisory_commands_run=advisory_commands_run,
        repo_smoke_tests_status="passed",
        repo_smoke_tests_total=len(REPO_SMOKE_TESTS),
        repo_smoke_tests_root=str(tests_root),
    )
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
