#!/usr/bin/env python3
from __future__ import annotations

import re
import sys
from pathlib import Path

from execution_system_paths import DEFAULT_ONE_PUBLISH_TASK_DOC as DEFAULT_TASK_DOC

SLICE_HEADING_RE = re.compile(r"^#### Slice [^\n]+$")
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


def is_in_scope_slice(heading: str, fields: dict[str, str]) -> bool:
    if not SLICE_HEADING_RE.match(heading):
        return False
    return "phase_id" in fields or "rollback_strategy" in fields


def validate_task_doc(task_doc: Path) -> list[str]:
    problems: list[str] = []
    blocks = parse_slice_blocks(task_doc.read_text(encoding="utf-8").splitlines())

    for heading, block in blocks:
        fields = extract_fields(block)
        if not is_in_scope_slice(heading, fields):
            continue

        scope = f"task_doc:{task_doc.name}:{heading.replace('#### ', '')}"
        if not fields.get("phase_id"):
            add_problem(problems, scope, "missing `phase_id`")
        if not fields.get("rollback_strategy"):
            add_problem(problems, scope, "missing `rollback_strategy`")

    return problems


def main() -> int:
    task_doc = Path(sys.argv[1]) if len(sys.argv) > 1 else DEFAULT_TASK_DOC
    problems = validate_task_doc(task_doc)
    if problems:
        print("TASK_SLICE_SCHEMA_CHECK_FAILED")
        for problem in problems:
            print(f"- {problem}")
        return 1

    print("TASK_SLICE_SCHEMA_CHECK_OK")
    print(f"- task_doc: {task_doc}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
