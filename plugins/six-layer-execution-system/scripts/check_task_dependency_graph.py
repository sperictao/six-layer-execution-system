#!/usr/bin/env python3
from __future__ import annotations

import re
import sys
from pathlib import Path

from task_inputs import TaskTargetNotRequired, iter_task_slices, resolve_task_target

FIELD_RE = re.compile(r"^- ([^:]+):(?: `([^`]+)`| (.+))$")
LIST_KEY_RE = re.compile(r"^- ([^:]+):$")
LIST_ITEM_RE = re.compile(r"^  - (.+)$")
SLICE_ID_REF_RE = re.compile(r"([A-Z]{2,}-[A-Z]\.([A-Z][A-Z0-9]*(?:-[A-Z0-9]+)?))")
SHORT_SLICE_ID_RE = re.compile(r"[A-Z][A-Z0-9]*(?:-[A-Z0-9]+)?")


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


def parse_dep_values(raw: str) -> list[str]:
    if not raw:
        return []
    values: list[str] = []
    for part in raw.split(" | "):
        part = part.strip().strip("`")
        if not part or part == "none":
            continue
        match = SLICE_ID_REF_RE.fullmatch(part)
        if match:
            values.append(match.group(2))
            continue
        if SHORT_SLICE_ID_RE.fullmatch(part):
            values.append(part)
            continue
        values.append(f"INVALID:{part}")
    return values


def validate_task_doc(task_doc: Path) -> list[str]:
    problems: list[str] = []
    graph: dict[str, list[str]] = {}

    try:
        task_slices = iter_task_slices(task_doc)
    except FileNotFoundError as exc:
        add_problem(problems, f"task_target:{task_doc}", str(exc))
        return problems

    for task_slice in task_slices:
        if not task_slice.slice_id:
            continue
        fields = extract_fields(task_slice.lines)
        if "parallel_safe" not in fields and "shared_write_targets" not in fields:
            continue

        scope = f"task_doc:{task_slice.source.name}:{task_slice.heading.lstrip('# ').strip()}"
        if not fields.get("depends_on"):
            add_problem(problems, scope, "missing `depends_on`")
            continue

        deps = parse_dep_values(fields.get("depends_on", ""))
        for dep in deps:
            if dep.startswith("INVALID:"):
                add_problem(problems, scope, f"invalid dependency reference `{dep.removeprefix('INVALID:')}`")
        clean_deps = [dep for dep in deps if not dep.startswith("INVALID:")]
        graph[task_slice.slice_id] = clean_deps

    for slice_id, deps in graph.items():
        scope = f"task_doc:{task_doc.name}:Slice {slice_id}"
        for dep in deps:
            if dep == slice_id:
                add_problem(problems, scope, "depends on itself")
            elif dep not in graph:
                add_problem(problems, scope, f"depends on unknown slice `{dep}`")

    temp_marks: set[str] = set()
    perm_marks: set[str] = set()

    def visit(node: str, stack: list[str]) -> None:
        if node in perm_marks:
            return
        if node in temp_marks:
            cycle = " -> ".join(stack + [node])
            add_problem(problems, f"task_doc:{task_doc.name}", f"dependency cycle `{cycle}`")
            return
        temp_marks.add(node)
        for dep in graph.get(node, []):
            if dep in graph:
                visit(dep, stack + [node])
        temp_marks.remove(node)
        perm_marks.add(node)

    for node in graph:
        visit(node, [])

    return problems


def main() -> int:
    path_arg = sys.argv[1] if len(sys.argv) > 1 else None
    try:
        task_target = resolve_task_target(path_arg)
    except TaskTargetNotRequired as exc:
        print("TASK_DEPENDENCY_GRAPH_CHECK_OK")
        print(f"- task_target: skipped ({exc})")
        return 0
    except Exception as exc:
        print("TASK_DEPENDENCY_GRAPH_CHECK_FAILED")
        print(f"- task_target: {exc}")
        return 1

    problems = validate_task_doc(task_target)
    if problems:
        print("TASK_DEPENDENCY_GRAPH_CHECK_FAILED")
        for problem in problems:
            print(f"- {problem}")
        return 1

    print("TASK_DEPENDENCY_GRAPH_CHECK_OK")
    print(f"- task_target: {task_target}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
