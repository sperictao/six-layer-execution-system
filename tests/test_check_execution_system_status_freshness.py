#!/usr/bin/env python3
from __future__ import annotations

import subprocess
import tempfile
from pathlib import Path

from execution_system_paths import WORKSPACE
CHECKER = WORKSPACE / "scripts" / "check_execution_system_status_freshness.py"


def run_checker(workspace: Path) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["python3", str(CHECKER), str(workspace)],
        text=True,
        capture_output=True,
        check=False,
    )


def expect_contains(name: str, proc: subprocess.CompletedProcess[str], needle: str) -> None:
    output = proc.stdout + proc.stderr
    if needle not in output:
        raise AssertionError(f"{name} missing expected text: {needle}\n{output}")


def main() -> int:
    proc = run_checker(WORKSPACE)
    if proc.returncode != 0:
        raise AssertionError(proc.stdout + proc.stderr)
    expect_contains("workspace-ok", proc, "EXECUTION_SYSTEM_STATUS_FRESHNESS_OK")
    expect_contains(
        "workspace-ok",
        proc,
        "- checked_files: ACTIVE.md,docs/execution-system-testing-inventory.md,tests/execution-system-testing-inventory.md",
    )

    with tempfile.TemporaryDirectory(prefix="status-freshness-") as tmpdir:
        tmp = Path(tmpdir)
        (tmp / "docs").mkdir(parents=True, exist_ok=True)
        (tmp / "ACTIVE.md").write_text(
            "- note: scripts/run_execution_system_full_tests.py passed with `total: 21`, `failed: 0`\n",
            encoding="utf-8",
        )
        (tmp / "docs" / "execution-system-testing-inventory.md").write_text(
            "- inventory placeholder\n",
            encoding="utf-8",
        )
        proc = run_checker(tmp)
        if proc.returncode == 0:
            raise AssertionError("stale status fixture should fail")
        expect_contains("stale-fixture", proc, "EXECUTION_SYSTEM_STATUS_FRESHNESS_FAILED")
        expect_contains("stale-fixture", proc, "ACTIVE.md:1: stale suite-health claim should not live in durable docs")

    print("EXECUTION_SYSTEM_STATUS_FRESHNESS_SMOKE_OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
