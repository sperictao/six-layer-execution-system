#!/usr/bin/env python3
from __future__ import annotations

import subprocess
import tempfile
from pathlib import Path

from execution_system_paths import WORKSPACE
CHECKER = WORKSPACE / "scripts" / "check_oversized_migration_slices.py"


def run_checker(task_doc: Path) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["python3", str(CHECKER), str(task_doc)],
        text=True,
        capture_output=True,
        check=False,
    )


def expect_contains(name: str, proc: subprocess.CompletedProcess[str], needle: str) -> None:
    output = proc.stdout + proc.stderr
    if needle not in output:
        raise AssertionError(f"{name} missing expected text: {needle}\n{output}")


def expect_not_contains(name: str, proc: subprocess.CompletedProcess[str], needle: str) -> None:
    output = proc.stdout + proc.stderr
    if needle in output:
        raise AssertionError(f"{name} unexpectedly contained text: {needle}\n{output}")


def main() -> int:
    with tempfile.TemporaryDirectory(prefix="oversized-slice-") as tmpdir:
        tmp = Path(tmpdir)

        broad = tmp / "broad.md"
        broad.write_text(
            "# sample\n\n## PR queue\n\n#### Slice P1 - broad execution-system sample\n- phase_id: `PH-5`\n- scope:\n  - `ACTIVE.md`\n  - `docs/execution-system-spec-v1.md`\n  - `scripts/run_execution_system_checks.py`\n- done_definition:\n  - `first thing landed`\n  - `second thing landed`\n",
            encoding="utf-8",
        )
        broad_proc = run_checker(broad)
        expect_contains("broad-slice-advisory", broad_proc, "OVERSIZED_MIGRATION_SLICE_ADVISORY")
        expect_contains("broad-slice-advisory", broad_proc, "heading uses a broad phase-level slice id")

        heterogeneous = tmp / "heterogeneous.md"
        heterogeneous.write_text(
            "# sample\n\n## PR queue\n\n#### Slice C9 - heterogeneous execution-system sample\n- phase_id: `PH-3`\n- scope:\n  - `ledger schema`\n  - `checker summary`\n  - `notification payload`\n  - `maintenance rule`\n  - `path smoke`\n- target_files:\n  - `ACTIVE.md`\n  - `scripts/run_execution_system_checks.py`\n  - `scripts/check_execution_system_maintenance_mode.py`\n- done_definition:\n  - `first thing landed`\n  - `second thing landed`\n",
            encoding="utf-8",
        )
        heterogeneous_proc = run_checker(heterogeneous)
        expect_contains("heterogeneous-advisory", heterogeneous_proc, "OVERSIZED_MIGRATION_SLICE_ADVISORY")
        expect_contains("heterogeneous-advisory", heterogeneous_proc, "target_files has 3 entries")

        focused = tmp / "focused.md"
        focused.write_text(
            "# sample\n\n## PR queue\n\n#### Slice C1 - focused notification state slice\n- phase_id: `PH-3`\n- scope:\n  - `normalize pending notifications`\n  - `preserve inflight state`\n  - `keep sent dedupe`\n  - `retain payload identity`\n  - `document ack order`\n- target_files:\n  - `scripts/normalize_notifications_state.py`\n  - `scripts/check_slice_closeout.py`\n- done_definition:\n  - `notification state stays normalized`\n  - `closeout surface only rewired`\n",
            encoding="utf-8",
        )
        focused_proc = run_checker(focused)
        expect_contains("focused-slice-ok", focused_proc, "OVERSIZED_MIGRATION_SLICE_OK")
        expect_not_contains("focused-slice-ok", focused_proc, "OVERSIZED_MIGRATION_SLICE_ADVISORY")

        split = tmp / "split.md"
        split.write_text(
            "# sample\n\n## PR queue\n\n#### Slice 2A - split sample\n- phase_id: `PH-2`\n- scope:\n  - `a`\n  - `b`\n  - `c`\n- done_definition:\n  - `one`\n  - `two`\n",
            encoding="utf-8",
        )
        split_proc = run_checker(split)
        expect_contains("split-slice-ok", split_proc, "OVERSIZED_MIGRATION_SLICE_OK")
        expect_not_contains("split-slice-ok", split_proc, "OVERSIZED_MIGRATION_SLICE_ADVISORY")

        legacy = tmp / "legacy.md"
        legacy.write_text(
            "# sample\n\n## PR queue\n\n#### Task 1 - legacy\n- scope:\n  - `a`\n  - `b`\n  - `c`\n- done_definition:\n  - `one`\n  - `two`\n",
            encoding="utf-8",
        )
        legacy_proc = run_checker(legacy)
        expect_contains("legacy-task-ok", legacy_proc, "OVERSIZED_MIGRATION_SLICE_OK")

    print("OVERSIZED_MIGRATION_SLICE_SMOKE_OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
