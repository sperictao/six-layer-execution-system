#!/usr/bin/env python3
from __future__ import annotations

import re
import sys
from pathlib import Path

from active_ledger import parse_ledger
from demand_card import parse_markdown_fields
from execution_system_paths import WORKSPACE

ACTIVE_PATH = WORKSPACE / "ACTIVE.md"
SLICE_HEADING_RE = re.compile(r"^#### Slice ([A-Z]\d+) - .+$")
FIELD_RE = re.compile(r"^- ([^:]+):(?: `([^`]+)`| (.+))$")
LIST_KEY_RE = re.compile(r"^- ([^:]+):$")
LIST_ITEM_RE = re.compile(r"^  - (.+)$")


def add_problem(problems: list[str], scope: str, message: str) -> None:
    problems.append(f"{scope}: {message}")


def normalize_ref(value: str) -> str:
    text = value.strip()
    if len(text) >= 2 and text[0] == text[-1] and text[0] in {"`", "'"}:
        text = text[1:-1].strip()
    return text


def extract_heading_section(text: str, heading: str) -> list[str]:
    lines = text.splitlines()
    start = None
    for index, line in enumerate(lines):
        if line.strip() == heading:
            start = index + 1
            break
    if start is None:
        return []

    end = len(lines)
    for index in range(start, len(lines)):
        if lines[index].startswith("## "):
            end = index
            break
    return lines[start:end]


def extract_first_simple_item(text: str, heading: str) -> str | None:
    for line in extract_heading_section(text, heading):
        stripped = line.strip()
        if stripped.startswith("- "):
            return normalize_ref(stripped[2:])
    return None


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
            fields[key] = normalize_ref(value or "")
            continue

        list_key_match = LIST_KEY_RE.match(line)
        if list_key_match:
            current_list_key = list_key_match.group(1).strip()
            list_values.setdefault(current_list_key, [])
            continue

        list_item_match = LIST_ITEM_RE.match(stripped)
        if current_list_key and list_item_match:
            list_values.setdefault(current_list_key, []).append(normalize_ref(list_item_match.group(1)))
            continue

        current_list_key = None

    for key, values in list_values.items():
        fields[key] = " | ".join(values) if values else ""
    return fields


def parse_pipe_list(raw: str) -> list[str]:
    if not raw:
        return []
    return [normalize_ref(part) for part in raw.split(" | ") if normalize_ref(part) and normalize_ref(part) != "none"]


def parse_demand_chain(raw_items: list[str]) -> list[str]:
    for item in raw_items:
        parts = [normalize_ref(part) for part in item.split("->")]
        cleaned = [part for part in parts if part]
        if len(cleaned) >= 2:
            return cleaned
    return []


def resolve_task_slices(tasks_text: str, project_prefix: str) -> dict[str, dict[str, str]]:
    slices: dict[str, dict[str, str]] = {}
    blocks = parse_slice_blocks(tasks_text.splitlines())
    for heading, block in blocks:
        match = SLICE_HEADING_RE.match(heading)
        if not match:
            continue
        short_id = match.group(1)
        full_id = f"{project_prefix}.{short_id}"
        slices[full_id] = extract_fields(block)
    return slices


def validate_generated_activity(activity, problems: list[str]) -> None:
    activity_id = activity.activity_id or activity.heading
    scope = f"generated:{activity_id}"
    source_doc = normalize_ref(activity.scalar("source_doc") or "")
    roadmap_doc = normalize_ref(activity.scalar("roadmap_doc") or "")
    tasks_doc = normalize_ref(activity.scalar("tasks_doc") or activity.scalar("tasks_dir") or "")
    current_slice_id = normalize_ref(activity.scalar("current_slice_id") or "")
    next_slice_id = normalize_ref(activity.scalar("next_slice_id") or "")
    if not source_doc.startswith("demands/") and not source_doc.startswith("activities/"):
        return
    demand_path = WORKSPACE / source_doc
    roadmap_path = WORKSPACE / roadmap_doc
    tasks_path = WORKSPACE / tasks_doc if tasks_doc else None
    for label, path in (("source_doc", demand_path), ("roadmap_doc", roadmap_path), ("tasks_doc", tasks_path)):
        if path is None:
            continue
        if not path.exists():
            add_problem(problems, scope, f"`{label}` points to missing file `{path.relative_to(WORKSPACE)}`")
            return

    demand_text = demand_path.read_text(encoding="utf-8")
    roadmap_text = roadmap_path.read_text(encoding="utf-8")
    tasks_text = tasks_path.read_text(encoding="utf-8") if tasks_path else ""
    demand_fields, demand_lists = parse_markdown_fields(demand_text)
    demand_expected_artifacts = [normalize_ref(item) for item in demand_lists.get("expected_artifacts", [])]

    for required_path in (source_doc, roadmap_doc, tasks_doc):
        if required_path not in demand_expected_artifacts:
            add_problem(problems, scope, f"demand expected_artifacts is missing `{required_path}`")

    if not any("ACTIVE activity" in item and activity_id in item for item in demand_expected_artifacts):
        add_problem(problems, scope, "demand expected_artifacts is missing the ACTIVE activity marker")

    roadmap_source = extract_first_simple_item(roadmap_text, "## Source demand")
    if roadmap_source != source_doc:
        add_problem(problems, scope, f"roadmap Source demand `{roadmap_source}` does not match `{source_doc}`")

    tasks_source = extract_first_simple_item(tasks_text, "## Source demand")
    if tasks_source != source_doc:
        add_problem(problems, scope, f"tasks Source demand `{tasks_source}` does not match `{source_doc}`")

    roadmap_phase = extract_first_simple_item(roadmap_text, "## Current recommended phase")
    if not roadmap_phase or current_slice_id not in roadmap_phase:
        add_problem(problems, scope, f"roadmap Current recommended phase does not mention `{current_slice_id}`")

    current_short_id = current_slice_id.split(".", 1)[1] if "." in current_slice_id else current_slice_id
    tasks_phase = extract_first_simple_item(tasks_text, "## Current phase")
    if not tasks_phase or f"Slice {current_short_id}" not in tasks_phase:
        add_problem(problems, scope, f"tasks Current phase does not mention `Slice {current_short_id}`")

    project_prefix = current_slice_id.split(".", 1)[0] if "." in current_slice_id else ""
    slices = resolve_task_slices(tasks_text, project_prefix)
    if current_slice_id not in slices:
        add_problem(problems, scope, f"tasks file is missing current slice `{current_slice_id}`")
    if next_slice_id not in slices:
        add_problem(problems, scope, f"tasks file is missing next slice `{next_slice_id}`")

    serial_units = [normalize_ref(item) for item in demand_lists.get("serial_units", []) if normalize_ref(item)]
    for slice_id in serial_units:
        if slice_id not in slices:
            add_problem(problems, scope, f"demand serial_units references missing task slice `{slice_id}`")

    chain = parse_demand_chain(demand_lists.get("dependency_graph", []))
    for previous, current in zip(chain, chain[1:]):
        depends_on = parse_pipe_list(slices.get(current, {}).get("depends_on", ""))
        if previous not in depends_on:
            add_problem(
                problems,
                scope,
                f"task slice `{current}` does not depend on the upstream demand edge `{previous}`",
            )

    if serial_units:
        if current_slice_id != serial_units[0]:
            add_problem(problems, scope, f"ACTIVE current_slice_id `{current_slice_id}` does not match first serial unit `{serial_units[0]}`")
        if len(serial_units) > 1 and next_slice_id != serial_units[1]:
            add_problem(problems, scope, f"ACTIVE next_slice_id `{next_slice_id}` does not match second serial unit `{serial_units[1]}`")

    risk_level = normalize_ref(demand_fields.get("risk_level", ""))
    external_confirmation = normalize_ref(demand_fields.get("external_confirmation_required", ""))
    autopilot = normalize_ref(activity.scalar("autopilot") or "")
    if (risk_level == "high" or external_confirmation == "true") and autopilot != "false":
        add_problem(
            problems,
            scope,
            "high-risk or confirmation-required generated activity must keep `autopilot: false`",
        )


def validate_generated_decomposition(active_path: Path) -> tuple[int, list[str]]:
    ledger = parse_ledger(active_path)
    problems: list[str] = []
    scanned = 0
    for activity in ledger.list_activities():
        if activity.scalar("type") != "roadmap":
            continue
        source_doc = normalize_ref(activity.scalar("source_doc") or "")
        if not source_doc.startswith("demands/") and not source_doc.startswith("activities/"):
            continue
        if not (activity.activity_id or "").startswith("auto-"):
            continue
        scanned += 1
        validate_generated_activity(activity, problems)
    return scanned, problems


def main() -> int:
    active_path = Path(sys.argv[1]) if len(sys.argv) > 1 else ACTIVE_PATH
    scanned, problems = validate_generated_decomposition(active_path)
    if problems:
        print("GENERATED_DECOMPOSITION_CONSISTENCY_CHECK_FAILED")
        for problem in problems:
            print(f"- {problem}")
        return 1

    print("GENERATED_DECOMPOSITION_CONSISTENCY_CHECK_OK")
    print(f"- scanned_activities: {scanned}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
