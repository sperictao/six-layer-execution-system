#!/usr/bin/env python3
from __future__ import annotations

import re
import sys
from pathlib import Path

from execution_system_paths import WORKSPACE as DEFAULT_WORKSPACE

STALE_PATTERNS = [
    re.compile(r"run_execution_system_full_tests\.py.*failed:\s*\d+", re.IGNORECASE),
    re.compile(r"run_execution_system_full_tests\.py.*total:\s*\d+", re.IGNORECASE),
    re.compile(r"passed with `total:\s*\d+`, `failed:\s*\d+`", re.IGNORECASE),
]


def find_problems(workspace: Path, path: Path) -> list[str]:
    problems: list[str] = []
    for line_no, line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
        for pattern in STALE_PATTERNS:
            if pattern.search(line):
                problems.append(f"{path.relative_to(workspace)}:{line_no}: stale suite-health claim should not live in durable docs")
                break
    return problems


def main() -> int:
    workspace = Path(sys.argv[1]) if len(sys.argv) > 1 else DEFAULT_WORKSPACE
    scopes = [
        workspace / "ACTIVE.md",
        workspace / "docs" / "execution-system-testing-inventory.md",
    ]

    problems: list[str] = []
    for path in scopes:
        if not path.exists():
            problems.append(f"{path.relative_to(workspace)}: missing required file")
            continue
        problems.extend(find_problems(workspace, path))

    if problems:
        print("EXECUTION_SYSTEM_STATUS_FRESHNESS_FAILED")
        for problem in problems:
            print(f"- {problem}")
        return 1

    print("EXECUTION_SYSTEM_STATUS_FRESHNESS_OK")
    print("- checked_files: ACTIVE.md,docs/execution-system-testing-inventory.md")
    print("- rule: durable docs must not quote exact full-suite pass/fail counts")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
