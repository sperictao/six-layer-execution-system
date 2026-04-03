#!/usr/bin/env python3
from __future__ import annotations

import os
import re
import sys
from pathlib import Path

from execution_system_paths import WORKSPACE as DEFAULT_WORKSPACE

POINTER_DOC = Path("docs/execution-system-testing-inventory.md")
TESTS_INVENTORY = Path("tests/execution-system-testing-inventory.md")

STALE_PATTERNS = [
    re.compile(r"run_execution_system_full_tests\.py.*failed:\s*\d+", re.IGNORECASE),
    re.compile(r"run_execution_system_full_tests\.py.*total:\s*\d+", re.IGNORECASE),
    re.compile(r"passed with `total:\s*\d+`, `failed:\s*\d+`", re.IGNORECASE),
]


def find_problems_for_label(path: Path, label: str) -> list[str]:
    problems: list[str] = []
    for line_no, line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
        for pattern in STALE_PATTERNS:
            if pattern.search(line):
                problems.append(f"{label}:{line_no}: stale suite-health claim should not live in durable docs")
                break
    return problems


def find_problems(workspace: Path, path: Path) -> list[str]:
    return find_problems_for_label(path, path.relative_to(workspace).as_posix())


def discover_tests_inventory(workspace: Path) -> Path | None:
    candidates: list[Path] = []
    override = os.environ.get("SIX_LAYER_SOURCE_REPO_ROOT")
    if override:
        candidates.append(Path(override).expanduser())

    if workspace.parent.name == "plugins":
        candidates.append(workspace.parent.parent)

    seen: set[Path] = set()
    workspace_resolved = workspace.resolve()
    for candidate in candidates:
        try:
            resolved_candidate = candidate.resolve()
        except FileNotFoundError:
            continue
        if resolved_candidate in seen:
            continue
        seen.add(resolved_candidate)

        plugin_candidate = resolved_candidate / "plugins" / workspace.name
        try:
            if plugin_candidate.resolve() != workspace_resolved:
                continue
        except FileNotFoundError:
            continue

        inventory_path = resolved_candidate / TESTS_INVENTORY
        if inventory_path.exists():
            return inventory_path

    return None


def main() -> int:
    workspace = Path(sys.argv[1]) if len(sys.argv) > 1 else DEFAULT_WORKSPACE
    scopes: list[tuple[Path, str]] = [
        (workspace / "ACTIVE.md", "ACTIVE.md"),
        (workspace / POINTER_DOC, POINTER_DOC.as_posix()),
    ]
    tests_inventory = discover_tests_inventory(workspace)
    if tests_inventory is not None:
        scopes.append((tests_inventory, TESTS_INVENTORY.as_posix()))

    problems: list[str] = []
    for path, label in scopes:
        if not path.exists():
            problems.append(f"{label}: missing required file")
            continue
        problems.extend(find_problems_for_label(path, label))
    if problems:
        print("EXECUTION_SYSTEM_STATUS_FRESHNESS_FAILED")
        for problem in problems:
            print(f"- {problem}")
        return 1

    print("EXECUTION_SYSTEM_STATUS_FRESHNESS_OK")
    checked_files = ["ACTIVE.md", POINTER_DOC.as_posix()]
    if tests_inventory is not None:
        checked_files.append(TESTS_INVENTORY.as_posix())
    print(f"- checked_files: {','.join(checked_files)}")
    print("- rule: durable docs must not quote exact full-suite pass/fail counts")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
