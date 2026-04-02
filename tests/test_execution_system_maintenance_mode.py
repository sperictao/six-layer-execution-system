#!/usr/bin/env python3
from __future__ import annotations

import subprocess
import sys
from pathlib import Path

from execution_system_paths import WORKSPACE
CHECK = WORKSPACE / "scripts" / "check_execution_system_maintenance_mode.py"
sys.path.insert(0, str(WORKSPACE / "scripts"))

from active_ledger import parse_ledger  # noqa: E402


def expect(text: str, needle: str) -> None:
    if needle not in text:
        raise AssertionError(f"missing expected text: {needle}\n{text}")


def main() -> int:
    ledger = parse_ledger()
    focus = ledger.get_current_focus_activity()
    if focus is None:
        raise AssertionError("missing focus activity")

    proc = subprocess.run(["python3", str(CHECK)], text=True, capture_output=True, check=False)
    output = proc.stdout + proc.stderr
    if proc.returncode != 0:
        raise AssertionError(output)

    expect(output, "EXECUTION_SYSTEM_MAINTENANCE_OK")
    expect(output, "- execution_activity_status: parked")
    expect(output, f"- focus_activity_id: {focus.activity_id}")
    expect(output, f"- focus_type: {focus.scalar('type')}")

    print("EXECUTION_SYSTEM_MAINTENANCE_SMOKE_OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
