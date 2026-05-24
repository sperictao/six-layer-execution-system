#!/usr/bin/env python3
from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path

from active_ledger import parse_ledger
from execution_system_paths import ACTIVE_PATH, resolve_workspace_path

SLICE_HEADING_RE = re.compile(r"^#{1,6}\s+Slice\s+([A-Z][A-Z0-9]*(?:-[A-Z0-9]+)?)(?:\s+[-—].*)?$")


@dataclass(frozen=True)
class TaskSlice:
    source: Path
    heading: str
    lines: list[str]
    slice_id: str | None


class TaskTargetNotRequired(ValueError):
    pass


def parse_slice_id_from_heading(heading: str) -> str | None:
    match = SLICE_HEADING_RE.match(heading.strip())
    return match.group(1) if match else None


def resolve_live_task_target(active_path: Path = ACTIVE_PATH) -> Path:
    ledger = parse_ledger(active_path)
    focus = ledger.get_current_focus_activity()
    if focus is None:
        if ledger.current_focus_activity_id == "none":
            raise TaskTargetNotRequired("no current focus activity")
        raise ValueError("ACTIVE current focus activity is missing")

    for field in ("tasks_dir", "tasks_doc", "current_tasks_file"):
        raw_path = focus.scalar(field)
        resolved = resolve_workspace_path(raw_path)
        if resolved is not None:
            return resolved

    focus_id = ledger.current_focus_activity_id or "unknown"
    if focus.scalar("type") != "roadmap":
        raise TaskTargetNotRequired(f"focus activity `{focus_id}` is not roadmap and has no task target")
    raise ValueError(f"focus activity `{focus_id}` has no tasks_dir/tasks_doc/current_tasks_file")


def resolve_task_target(path_arg: str | None = None) -> Path:
    if path_arg:
        candidate = Path(path_arg)
        if candidate.name == "ACTIVE.md":
            return resolve_live_task_target(candidate)
        return candidate
    return resolve_live_task_target()


def iter_task_files(target: Path) -> list[Path]:
    if target.is_dir():
        return sorted(path for path in target.glob("*.md") if path.is_file())
    if target.is_file():
        return [target]
    raise FileNotFoundError(f"{target} is not a file or directory")


def _legacy_slice_blocks(path: Path, lines: list[str]) -> list[TaskSlice]:
    blocks: list[TaskSlice] = []
    current_heading: str | None = None
    current_block: list[str] = []

    for line in lines:
        if line.startswith("#### Slice "):
            if current_heading is not None:
                blocks.append(
                    TaskSlice(
                        source=path,
                        heading=current_heading,
                        lines=current_block,
                        slice_id=parse_slice_id_from_heading(current_heading),
                    )
                )
            current_heading = line.strip()
            current_block = []
            continue
        if current_heading is not None:
            current_block.append(line.rstrip("\n"))

    if current_heading is not None:
        blocks.append(
            TaskSlice(
                source=path,
                heading=current_heading,
                lines=current_block,
                slice_id=parse_slice_id_from_heading(current_heading),
            )
        )
    return blocks


def _file_slice(path: Path, lines: list[str]) -> TaskSlice:
    heading = next((line.strip() for line in lines if line.startswith("# ")), f"# Slice {path.stem}")
    return TaskSlice(
        source=path,
        heading=heading,
        lines=lines,
        slice_id=parse_slice_id_from_heading(heading) or path.stem,
    )


def iter_task_slices(target: Path) -> list[TaskSlice]:
    slices: list[TaskSlice] = []
    for path in iter_task_files(target):
        lines = path.read_text(encoding="utf-8").splitlines()
        legacy_blocks = _legacy_slice_blocks(path, lines)
        if legacy_blocks:
            slices.extend(legacy_blocks)
            continue
        slices.append(_file_slice(path, lines))
    return slices
