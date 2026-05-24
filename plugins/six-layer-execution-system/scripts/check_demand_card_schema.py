#!/usr/bin/env python3
from __future__ import annotations

import sys
from pathlib import Path

from demand_card import validate_demand_card_text
from execution_system_paths import ACTIVITIES_DIR, DEMANDS_DIR


def demand_files_from_args(args: list[str]) -> list[Path]:
    if not args:
        files: list[Path] = []
        if ACTIVITIES_DIR.exists():
            files.extend(sorted(path for path in ACTIVITIES_DIR.glob("*/0-demand.md") if path.is_file()))
        if DEMANDS_DIR.exists():
            files.extend(sorted(path for path in DEMANDS_DIR.glob("*.md") if path.is_file()))
        return files

    files: list[Path] = []
    for raw in args:
        path = Path(raw)
        if path.is_dir():
            files.extend(sorted(candidate for candidate in path.glob("*.md") if candidate.is_file()))
        else:
            files.append(path)
    return files


def main() -> int:
    files = demand_files_from_args(sys.argv[1:])
    problems: list[str] = []

    for path in files:
        if not path.exists():
            problems.append(f"{path}: missing file")
            continue
        text = path.read_text(encoding="utf-8")
        problems.extend(validate_demand_card_text(text, str(path)))

    if problems:
        print("DEMAND_CARD_SCHEMA_CHECK_FAILED")
        for problem in problems:
            print(f"- {problem}")
        return 1

    print("DEMAND_CARD_SCHEMA_CHECK_OK")
    print(f"- scanned_files: {len(files)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
