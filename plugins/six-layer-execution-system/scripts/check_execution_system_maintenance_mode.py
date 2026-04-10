#!/usr/bin/env python3
from __future__ import annotations

import subprocess
import sys

from execution_system_paths import WORKSPACE
sys.path.insert(0, str(WORKSPACE / "scripts"))

from active_ledger import parse_ledger  # noqa: E402


ALLOWED_NON_RUNNABLE_FOCUS_IDS = {
    "execution-system-decomposition-upgrade",
}
ALLOWED_NON_RUNNABLE_FOCUS_TYPES = {
    "waiting",
}


def main() -> int:
    ledger = parse_ledger()
    execution_activity = ledger.get_activity("execution-system-spec-v1")

    if execution_activity is None:
        print("EXECUTION_SYSTEM_MAINTENANCE_FAILED")
        print("- reason: missing execution-system-spec-v1 activity")
        return 1

    if execution_activity.scalar("status") != "parked":
        print("EXECUTION_SYSTEM_MAINTENANCE_FAILED")
        print(f"- reason: execution-system status is not parked ({execution_activity.scalar('status') or 'missing'})")
        return 1

    if execution_activity.scalar("autopilot") != "false":
        print("EXECUTION_SYSTEM_MAINTENANCE_FAILED")
        print(f"- reason: execution-system autopilot is not false ({execution_activity.scalar('autopilot') or 'missing'})")
        return 1

    focus = ledger.get_current_focus_activity()
    if focus is None:
        print("EXECUTION_SYSTEM_MAINTENANCE_FAILED")
        print("- reason: no focus activity")
        return 1

    if focus.activity_id == "execution-system-spec-v1":
        print("EXECUTION_SYSTEM_MAINTENANCE_FAILED")
        print("- reason: execution-system should not remain the current focus in maintenance mode")
        return 1

    runnable = [activity.activity_id for activity in ledger.list_runnable_activities()]
    focus_type = focus.scalar("type") or "missing"
    focus_is_allowed_non_runnable = (
        focus.activity_id in ALLOWED_NON_RUNNABLE_FOCUS_IDS or focus_type in ALLOWED_NON_RUNNABLE_FOCUS_TYPES
    )
    if focus.activity_id not in runnable and not focus_is_allowed_non_runnable:
        print("EXECUTION_SYSTEM_MAINTENANCE_FAILED")
        print("- reason: current focus is neither runnable work outside the execution-system line nor an approved non-runnable focus")
        return 1

    proc = subprocess.run(
        ["python3", str(WORKSPACE / "scripts" / "accept_active_ledger_v2.py")],
        text=True,
        capture_output=True,
        check=False,
    )
    output = proc.stdout + proc.stderr
    if proc.returncode != 0 or "ACTIVE_LEDGER_V2_ACCEPTANCE_OK" not in output:
        print("EXECUTION_SYSTEM_MAINTENANCE_FAILED")
        print("- reason: acceptance is not green under maintenance mode")
        return 1

    print("EXECUTION_SYSTEM_MAINTENANCE_OK")
    print(f"- execution_activity_status: {execution_activity.scalar('status')}")
    print(f"- focus_activity_id: {focus.activity_id}")
    print(f"- focus_type: {focus_type}")
    print(f"- runnable_activity_ids: {','.join(runnable)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
