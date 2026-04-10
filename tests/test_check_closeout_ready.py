#!/usr/bin/env python3
from __future__ import annotations

import subprocess
import sys

from execution_system_paths import WORKSPACE
CHECK = WORKSPACE / "scripts" / "check_closeout_ready.py"
sys.path.insert(0, str(WORKSPACE / "scripts"))

from active_ledger import parse_ledger  # noqa: E402


def expect_contains(output: str, needle: str) -> None:
    if needle not in output:
        raise AssertionError(f"missing expected text: {needle}\n{output}")


def main() -> int:
    ledger = parse_ledger()
    focus = ledger.get_current_focus_activity()
    if focus is None:
        raise AssertionError("missing focus activity")

    proc = subprocess.run(["python3", str(CHECK)], text=True, capture_output=True, check=False)
    output = proc.stdout + proc.stderr

    if focus.scalar("type") == "roadmap":
        if proc.returncode != 0:
            raise AssertionError(output)
        expect_contains(output, "CLOSEOUT_READY_OK")
        expect_contains(output, f"- focus_activity_id: {focus.activity_id}")
    else:
        if proc.returncode == 0:
            raise AssertionError("closeout-ready should fail for non-roadmap focus")
        expect_contains(output, "CLOSEOUT_READY_FAILED")
        expect_contains(output, f"- reason: focus activity is not roadmap ({focus.scalar('type')})")

    print("CLOSEOUT_READY_SMOKE_OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
