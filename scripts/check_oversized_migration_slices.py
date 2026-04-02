#!/usr/bin/env python3
from __future__ import annotations

import re
import sys
from pathlib import Path

from execution_system_paths import DEFAULT_ONE_PUBLISH_TASK_DOC as DEFAULT_TASK_DOC
SLICE_HEADING_RE = re.compile(r"^#### Slice [^\n]+$")
SUBSLICE_TOKEN_RE = re.compile(r"\b\d+[A-Z]\b")
FIELD_RE = re.compile(r"^- ([^:]+):(?: `([^`]+)`| (.+))$")
LIST_KEY_RE = re.compile(r"^- ([^:]+):$")
LIST_ITEM_RE = re.compile(r"^  - (.+)$")


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


def extract_fields(block: list[str]) -> tuple[dict[str, str], dict[str, list[str]]]:
    fields: dict[str, str] = {}
    list_fields: dict[str, list[str]] = {}
    current_list_key: str | None = None

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
            list_fields.setdefault(current_list_key, [])
            continue

        list_item_match = LIST_ITEM_RE.match(stripped)
        if current_list_key and list_item_match:
            list_fields.setdefault(current_list_key, []).append(list_item_match.group(1).strip())
            continue

        current_list_key = None

    for key, values in list_fields.items():
        if values:
            fields[key] = " | ".join(values)
        else:
            fields.setdefault(key, "")
    return fields, list_fields


def is_in_scope_slice(heading: str, fields: dict[str, str]) -> bool:
    if not SLICE_HEADING_RE.match(heading):
        return False
    if "phase_id" not in fields:
        return False
    if SUBSLICE_TOKEN_RE.search(heading):
        return False
    return True


def advisory_reasons(heading: str, list_fields: dict[str, list[str]]) -> list[str]:
    reasons: list[str] = []
    scope_items = list_fields.get("scope", [])
    done_items = list_fields.get("done_definition", [])
    target_files = list_fields.get("target_files", [])
    broad_phase_heading = heading.lower().startswith("#### slice p")

    if broad_phase_heading and len(scope_items) >= 2:
        reasons.append("heading uses a broad phase-level slice id")

    if len(scope_items) >= 5 and len(done_items) >= 2 and len(target_files) >= 3:
        reasons.append(f"scope has {len(scope_items)} entries")
        reasons.append(f"done_definition has {len(done_items)} entries")
        reasons.append(f"target_files has {len(target_files)} entries")

    return reasons


def check_task_doc(task_doc: Path) -> list[tuple[str, list[str]]]:
    warnings: list[tuple[str, list[str]]] = []
    blocks = parse_slice_blocks(task_doc.read_text(encoding="utf-8").splitlines())

    for heading, block in blocks:
        fields, list_fields = extract_fields(block)
        if not is_in_scope_slice(heading, fields):
            continue
        reasons = advisory_reasons(heading, list_fields)
        if not reasons:
            continue
        scope = f"task_doc:{task_doc.name}:{heading.replace('#### ', '')}"
        warnings.append((scope, reasons))
    return warnings


def main() -> int:
    task_doc = Path(sys.argv[1]) if len(sys.argv) > 1 else DEFAULT_TASK_DOC
    warnings = check_task_doc(task_doc)
    if warnings:
        print("OVERSIZED_MIGRATION_SLICE_ADVISORY")
        print(f"- warning_count: {len(warnings)}")
        for scope, reasons in warnings:
            print(f"- {scope}: {'; '.join(reasons)}")
        print("- recovery_hint: inspect the warned slice, decide whether visible progress is too heterogeneous for one slice id, then either split it into sub-slices or tighten the slice wording")
    else:
        print("OVERSIZED_MIGRATION_SLICE_OK")
    print(f"- task_doc: {task_doc}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
