#!/usr/bin/env python3
from __future__ import annotations

import re
import sys
from pathlib import Path

from task_inputs import TaskTargetNotRequired, iter_task_slices, resolve_task_target

FIELD_RE = re.compile(r"^- ([^:]+):(?: `([^`]+)`| (.+))$")
LIST_KEY_RE = re.compile(r"^- ([^:]+):$")
LIST_ITEM_RE = re.compile(r"^  - (.+)$")


def add_problem(problems: list[str], scope: str, message: str) -> None:
    problems.append(f"{scope}: {message}")


def parse_slice_blocks(lines: list[str]) -> list[tuple[str, list[str]]]:
    blocks: list[tuple[str, list[str]]] = []
    current_heading: str | None = None
    current_block: list[str] = []

    for line in lines:
        if line.startswith("#### "):
            if current_heading is not None:
                blocks.append((current_heading, current_block))
            current_heading = line.strip()
            current_block = []
            continue
        if current_heading is not None:
            current_block.append(line.rstrip("\n"))

    if current_heading is not None:
        blocks.append((current_heading, current_block))
    return blocks


def extract_fields(block: list[str]) -> dict[str, str]:
    fields: dict[str, str] = {}
    current_list_key: str | None = None
    list_values: dict[str, list[str]] = {}

    for raw in block:
        stripped = raw.rstrip("\n")
        line = stripped.strip()

        match = FIELD_RE.match(line)
        if match:
            current_list_key = None
            key = match.group(1).strip()
            value = match.group(2) if match.group(2) is not None else match.group(3)
            fields[key] = value.strip() if value else ""
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
        if values:
            fields[key] = " | ".join(values)
        else:
            fields.setdefault(key, "")
    return fields


def parse_list_field(raw: str) -> list[str]:
    if not raw:
        return []
    return [part.strip() for part in raw.split(" | ") if part.strip() and part.strip() != "none"]


def validate_task_doc(task_doc: Path) -> list[str]:
    problems: list[str] = []

    try:
        task_slices = iter_task_slices(task_doc)
    except FileNotFoundError as exc:
        add_problem(problems, f"task_target:{task_doc}", str(exc))
        return problems

    for task_slice in task_slices:
        fields = extract_fields(task_slice.lines)
        if "parallel_safe" not in fields and "shared_write_targets" not in fields:
            continue

        scope = f"task_doc:{task_slice.source.name}:{task_slice.heading.lstrip('# ').strip()}"
        parallel_value = fields.get("parallel_safe", "").strip().lower()
        shared_targets = parse_list_field(fields.get("shared_write_targets", ""))

        if parallel_value not in {"true", "false"}:
            add_problem(problems, scope, "`parallel_safe` must be `true` or `false`")
            continue

        if not fields.get("shared_write_targets"):
            add_problem(problems, scope, "missing `shared_write_targets`")
            continue

        if parallel_value == "true" and shared_targets:
            add_problem(
                problems,
                scope,
                "`parallel_safe: true` conflicts with non-empty `shared_write_targets`",
            )

        if parallel_value == "false" and not shared_targets:
            add_problem(
                problems,
                scope,
                "`parallel_safe: false` should explain the write surface in `shared_write_targets`",
            )

    return problems


def main() -> int:
    path_arg = sys.argv[1] if len(sys.argv) > 1 else None
    try:
        task_target = resolve_task_target(path_arg)
    except TaskTargetNotRequired as exc:
        print("PARALLEL_SAFETY_CHECK_OK")
        print(f"- task_target: skipped ({exc})")
        return 0
    except Exception as exc:
        print("PARALLEL_SAFETY_CHECK_FAILED")
        print(f"- task_target: {exc}")
        return 1

    problems = validate_task_doc(task_target)
    if problems:
        print("PARALLEL_SAFETY_CHECK_FAILED")
        for problem in problems:
            print(f"- {problem}")
        return 1

    print("PARALLEL_SAFETY_CHECK_OK")
    print(f"- task_target: {task_target}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
