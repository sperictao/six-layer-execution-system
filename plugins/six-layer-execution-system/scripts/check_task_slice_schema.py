#!/usr/bin/env python3
"""Check per-slice tasks files under a tasks directory.

Each file under activities/<activity-id>/3-tasks/<slice-id>.md is a self-contained slice.
Required fields: phase_id, rollback_strategy.
Expected fields: actual_execution_plan (before execution), actual_outcome (after).
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

from task_inputs import (
    TaskTargetNotRequired,
    iter_task_slices,
    parse_slice_id_from_heading,
    resolve_task_target,
)

FIELD_RE = re.compile(r"^- ([^:]+):(?: `([^`]+)`| (.+))$")
LIST_KEY_RE = re.compile(r"^- ([^:]+):$")
LIST_ITEM_RE = re.compile(r"^  - (.+)$")


def add_problem(problems: list[str], scope: str, message: str) -> None:
    problems.append(f"{scope}: {message}")


def extract_fields(lines: list[str]) -> dict[str, str]:
    """Parse key-value fields and list-key values from a slice file."""
    fields: dict[str, str] = {}
    current_list_key: str | None = None
    list_values: dict[str, list[str]] = {}

    for raw in lines:
        stripped = raw.rstrip("\n")
        line = stripped.strip()

        # If inside a list, check list item first
        if current_list_key:
            list_item_match = LIST_ITEM_RE.match(stripped)
            if list_item_match:
                list_values.setdefault(current_list_key, []).append(list_item_match.group(1).strip())
                continue

        match = FIELD_RE.match(line)
        if match:
            current_list_key = None
            key = match.group(1).strip()
            value = match.group(2) if match.group(2) is not None else match.group(3).strip() if match.group(3) else ""
            fields[key] = value
            continue

        list_key_match = LIST_KEY_RE.match(line)
        if list_key_match:
            current_list_key = list_key_match.group(1).strip()
            list_values.setdefault(current_list_key, [])
            continue

        list_item_match = LIST_ITEM_RE.match(stripped)
        if current_list_key and list_item_match:
            list_values.setdefault(current_list_key, []).append(list_item_match.group(1).strip())
            continue

        current_list_key = None

    for key, values in list_values.items():
        fields[key] = " | ".join(values) if values else ""
    return fields


def is_in_scope_slice(heading: str, fields: dict[str, str]) -> bool:
    if parse_slice_id_from_heading(heading) is None:
        return False
    return "phase_id" in fields or "rollback_strategy" in fields


def validate_slice(scope: str, lines: list[str]) -> list[str]:
    """Validate one parsed slice block or per-slice file."""
    problems: list[str] = []
    fields = extract_fields(lines)

    if not fields.get("phase_id"):
        add_problem(problems, scope, "missing `phase_id`")
    if not fields.get("rollback_strategy"):
        add_problem(problems, scope, "missing `rollback_strategy`")

    status = fields.get("status", "")
    if status == "in_progress" and not fields.get("actual_execution_plan"):
        add_problem(problems, scope, "in_progress but missing `actual_execution_plan`")
    if status == "done" and not fields.get("actual_outcome"):
        add_problem(problems, scope, "done but missing `actual_outcome`")

    return problems


def validate_task_doc(task_doc: Path) -> list[str]:
    return validate_task_target(task_doc)


def validate_task_target(task_target: Path) -> list[str]:
    """Validate a task file or directory of per-slice task files."""
    problems: list[str] = []

    try:
        slices = iter_task_slices(task_target)
    except FileNotFoundError as exc:
        add_problem(problems, f"task_target:{task_target}", str(exc))
        return problems

    if not slices:
        add_problem(problems, f"task_target:{task_target}", "no task slice files found")
        return problems

    for task_slice in slices:
        fields = extract_fields(task_slice.lines)
        if not is_in_scope_slice(task_slice.heading, fields):
            continue
        scope = f"task_doc:{task_slice.source.name}:{task_slice.heading.lstrip('# ').strip()}"
        problems.extend(validate_slice(scope, task_slice.lines))

    return problems


def main() -> int:
    path_arg = sys.argv[1] if len(sys.argv) > 1 else None
    try:
        task_target = resolve_task_target(path_arg)
    except TaskTargetNotRequired as exc:
        print("TASK_SLICE_SCHEMA_CHECK_OK")
        print(f"- task_target: skipped ({exc})")
        return 0
    except Exception as exc:
        print("TASK_SLICE_SCHEMA_CHECK_FAILED")
        print(f"- task_target: {exc}")
        return 1

    problems = validate_task_target(task_target)

    if problems:
        print("TASK_SLICE_SCHEMA_CHECK_FAILED")
        for problem in problems:
            print(f"- {problem}")
        return 1

    print("TASK_SLICE_SCHEMA_CHECK_OK")
    print(f"- task_target: {task_target}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
