#!/usr/bin/env python3
from __future__ import annotations

import sys
from pathlib import Path

from execution_system_paths import WORKSPACE
sys.path.insert(0, str(WORKSPACE / "scripts"))

from active_ledger import parse_ledger  # noqa: E402


def main() -> int:
    ledger = parse_ledger()
    focus = ledger.get_current_focus_activity()
    if focus is None:
        print("FOCUS_VALIDATION_FAILED:no_focus")
        return 1

    problems: list[str] = []
    policy_gates: list[str] = []

    focus_autopilot = focus.scalar("autopilot") == "true"
    runnable = [activity.activity_id for activity in ledger.list_runnable_activities()]
    focus_is_runnable = focus.activity_id in runnable

    if not focus_autopilot:
        policy_gates.append("focus activity is not autopilot=true")
    if not focus_is_runnable:
        policy_gates.append("focus activity is not in runnable activity set")

    non_focus_runnable = [aid for aid in runnable if aid != focus.activity_id]

    if problems:
        print("FOCUS_VALIDATION_FAILED")
        for problem in problems:
            print(f"- {problem}")
        return 1

    if policy_gates:
        print("FOCUS_VALIDATION_POLICY_GATE")
        print(f"- focus_activity_id: {focus.activity_id}")
        for gate in policy_gates:
            print(f"- {gate}")
        print("- note: focus-first remains intact; current focus is intentionally not auto-runnable")
        return 2

    print("FOCUS_VALIDATION_OK")
    print(f"- focus_activity_id: {focus.activity_id}")
    print(f"- runnable_activity_ids: {','.join(runnable)}")
    print(f"- non_focus_runnable_count: {len(non_focus_runnable)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
