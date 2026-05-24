#!/usr/bin/env python3
from __future__ import annotations

import argparse
import filecmp
import shutil
from dataclasses import dataclass, field
from datetime import date
from pathlib import Path

from execution_system_paths import PLUGIN_ROOT, WORKSPACE


COPY_DIRS = (
    ".codex-plugin",
    "assets",
    "agents",
    "docs",
    "references",
    "recycle",
    "scripts",
    "skills",
)
COPY_FILES = (
    "AGENTS.md",
    "README.md",
)
CREATE_DIRS = (
    "activities",
    "local-state",
)
SKIP_NAMES = {
    ".DS_Store",
    "__pycache__",
}


@dataclass
class InitResult:
    target: Path
    template_root: Path
    dry_run: bool = False
    created: list[str] = field(default_factory=list)
    skipped: list[str] = field(default_factory=list)
    overwritten: list[str] = field(default_factory=list)
    conflicts: list[str] = field(default_factory=list)


def fresh_active_text() -> str:
    today = date.today().isoformat()
    return f"""# ACTIVE.md — Execution Ledger v3

## Ledger meta
- version: `3`
- mode: `multi-activity`
- current_focus_activity_id: `none`
- default_reply_activity_id: `none`
- selection_policy: `focus-first`
- activity_root: `activities/`
- updated_at: `{today}`

## Status legend
- `ready` — agreed and ready to start
- `in_progress` — actively being worked on
- `blocked` — cannot proceed until something changes
- `done` — completed and verified
- `parked` — intentionally paused

## Activity index

| activity_id | type | status | priority | path |
|------------|------|--------|----------|------|

## Focus: none
- status: `none`

## Workspace rules
- execution_truth: `ACTIVE.md` (this file) + `activities/<focus>/card.md`
- complex_task_truth: `activities/<id>/card.md` → `2-roadmap.md` → `3-tasks/`
- focus_execution: `focus-first`
- recovery_chain: `ACTIVE.md` → `activities/<focus>/card.md` → `3-tasks/<slice>.md`
- spec_reference: `docs/execution-system-spec-v1.md`

## Cross-activity resources
- `docs/` —跨 activity 规范与设计文档
- `references/` — 跨 activity 模板、协议、源映射
- `scripts/` — 跨 activity checker、runner、工具
- `skills/` — 跨 activity skill 定义
- `recycle/` — 已确认回收的 activity 目录与 `history.md` 索引，不是运行态真相

## Recovery checklist
1. Read `Ledger meta` and `Activity index` above.
2. If `current_focus_activity_id` is `none`, there is no live activity; use `recycle/history.md` only as historical index.
3. Otherwise follow `Focus` pointer to `activities/<focus>/card.md`.
4. Read the card — follow `2-roadmap.md` and `3-tasks/<slice>.md`.
5. Run: `python3 scripts/run_execution_system_checks.py checks --timeout 60`
6. For progress questions, verify repo facts before answering.
"""


def rel(path: Path, root: Path) -> str:
    return path.relative_to(root).as_posix()


def should_skip(path: Path) -> bool:
    return any(part in SKIP_NAMES for part in path.parts)


def files_equal(left: Path, right: Path) -> bool:
    return filecmp.cmp(str(left), str(right), shallow=False)


def iter_source_files(root: Path) -> list[Path]:
    return sorted(path for path in root.rglob("*") if path.is_file() and not should_skip(path))


def parent_conflict(path: Path, target_root: Path) -> str | None:
    current = path.parent
    while current != target_root.parent:
        if current.exists() and not current.is_dir():
            return f"{current.relative_to(target_root).as_posix()} exists and is not a directory"
        if current == target_root:
            break
        current = current.parent
    return None


def collect_conflicts(target: Path, template_root: Path, *, force: bool) -> list[str]:
    conflicts: list[str] = []
    if target.exists() and not target.is_dir():
        return [f"{target} exists and is not a directory"]
    nearest_parent = target.parent
    while not nearest_parent.exists() and nearest_parent != nearest_parent.parent:
        nearest_parent = nearest_parent.parent
    if nearest_parent.exists() and not nearest_parent.is_dir():
        return [f"{nearest_parent} exists and is not a directory"]

    active = target / "ACTIVE.md"
    if active.exists() and not active.is_file():
        conflicts.append("ACTIVE.md exists and is not a file")

    for dirname in CREATE_DIRS:
        target_dir = target / dirname
        if target_dir.exists() and not target_dir.is_dir():
            conflicts.append(f"{dirname} exists and is not a directory")

    for filename in COPY_FILES:
        source = template_root / filename
        destination = target / filename
        if not source.exists():
            conflicts.append(f"template is missing {filename}")
            continue
        if destination.exists() and destination.is_dir():
            conflicts.append(f"{filename} exists and is a directory")
        elif destination.exists() and not force and not files_equal(source, destination):
            conflicts.append(f"{filename} exists and differs")

    for dirname in COPY_DIRS:
        source_dir = template_root / dirname
        target_dir = target / dirname
        if not source_dir.exists():
            conflicts.append(f"template is missing {dirname}/")
            continue
        if target_dir.exists() and not target_dir.is_dir():
            conflicts.append(f"{dirname} exists and is not a directory")
            continue
        for source in iter_source_files(source_dir):
            destination = target / rel(source, template_root)
            parent_problem = parent_conflict(destination, target)
            if parent_problem:
                conflicts.append(parent_problem)
                continue
            if destination.exists() and destination.is_dir():
                conflicts.append(f"{rel(destination, target)} exists and is a directory")
            elif destination.exists() and not force and not files_equal(source, destination):
                conflicts.append(f"{rel(destination, target)} exists and differs")

    return sorted(set(conflicts))


def ensure_dir(path: Path, result: InitResult) -> None:
    relative = rel(path, result.target)
    if path.exists():
        result.skipped.append(relative)
        return
    if not result.dry_run:
        path.mkdir(parents=True, exist_ok=True)
    result.created.append(relative)


def write_active(result: InitResult) -> None:
    active = result.target / "ACTIVE.md"
    if active.exists():
        result.skipped.append("ACTIVE.md")
        return
    if not result.dry_run:
        active.parent.mkdir(parents=True, exist_ok=True)
        active.write_text(fresh_active_text(), encoding="utf-8")
    result.created.append("ACTIVE.md")


def copy_file(source: Path, destination: Path, result: InitResult, *, force: bool) -> None:
    relative = rel(destination, result.target)
    if destination.exists() and files_equal(source, destination):
        result.skipped.append(relative)
        return

    if destination.exists():
        if not result.dry_run:
            shutil.copy2(source, destination)
        result.overwritten.append(relative)
        return

    if not result.dry_run:
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source, destination)
    result.created.append(relative)


def copy_tree(dirname: str, result: InitResult, *, force: bool) -> None:
    source_dir = result.template_root / dirname
    target_dir = result.target / dirname
    ensure_dir(target_dir, result)
    for source in iter_source_files(source_dir):
        copy_file(source, result.target / rel(source, result.template_root), result, force=force)


def initialize(target: Path, *, force: bool = False, dry_run: bool = False) -> InitResult:
    result = InitResult(target=target.expanduser().resolve(), template_root=PLUGIN_ROOT.resolve(), dry_run=dry_run)
    result.conflicts = collect_conflicts(result.target, result.template_root, force=force)
    if result.conflicts:
        return result

    if not dry_run:
        result.target.mkdir(parents=True, exist_ok=True)

    write_active(result)
    for dirname in CREATE_DIRS:
        ensure_dir(result.target / dirname, result)
    for filename in COPY_FILES:
        copy_file(result.template_root / filename, result.target / filename, result, force=force)
    for dirname in COPY_DIRS:
        copy_tree(dirname, result, force=force)

    return result


def print_result(result: InitResult) -> int:
    if result.conflicts:
        print("EXECUTION_SYSTEM_INIT_CONFLICT")
        print(f"- target: {result.target}")
        for conflict in result.conflicts:
            print(f"- conflict: {conflict}")
        print("- hint: rerun with --force only if overwriting these files is intended")
        return 1

    print("EXECUTION_SYSTEM_INIT_OK")
    print(f"- target: {result.target}")
    print(f"- template_root: {result.template_root}")
    print(f"- dry_run: {'true' if result.dry_run else 'false'}")
    print(f"- created: {len(result.created)}")
    print(f"- overwritten: {len(result.overwritten)}")
    print(f"- skipped: {len(result.skipped)}")
    print("- next_step: run from the target root")
    print("- validation_command: python3 scripts/run_execution_checks.py active --timeout 60")
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Initialize a Six-Layer Execution System root.")
    parser.add_argument(
        "--target",
        default=str(WORKSPACE),
        help="Directory to initialize. Defaults to SIX_LAYER_WORKSPACE, then the plugin root.",
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Overwrite differing copied support files. Existing ACTIVE.md is still preserved.",
    )
    parser.add_argument("--dry-run", action="store_true", help="Report planned changes without writing files.")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    result = initialize(Path(args.target), force=args.force, dry_run=args.dry_run)
    return print_result(result)


if __name__ == "__main__":
    raise SystemExit(main())
