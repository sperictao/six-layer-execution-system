#!/usr/bin/env python3
from __future__ import annotations

import sys

from execution_system_paths import WORKSPACE
sys.path.insert(0, str(WORKSPACE))

from scripts.run_execution_system_checks import collect_summary
from scripts.active_ledger import parse_ledger


def main() -> int:
    code, summary = collect_summary(print_output=False)
    if code != 0:
        print("CLOSEOUT_READY_FAILED")
        print("- reason: hard-fail suite did not pass")
        print(f"- first_failing_command: {summary.first_failing_command or 'none'}")
        return 1

    ledger = parse_ledger(WORKSPACE / "ACTIVE.md")
    focus = ledger.get_current_focus_activity()
    if focus is None:
        print("CLOSEOUT_READY_FAILED")
        print("- reason: no focus activity")
        return 1

    if focus.scalar("type") != "roadmap":
        print("CLOSEOUT_READY_FAILED")
        print(f"- reason: focus activity is not roadmap ({focus.scalar('type') or 'missing'})")
        return 1

    current_slice_id = focus.scalar("current_slice_id")
    next_slice_id = focus.scalar("next_slice_id")
    last_commit = focus.scalar("last_commit")
    last_validation = focus.items("last_validation")

    if not current_slice_id:
        print("CLOSEOUT_READY_FAILED")
        print("- reason: missing current_slice_id")
        return 1
    if not next_slice_id:
        print("CLOSEOUT_READY_FAILED")
        print("- reason: missing next_slice_id")
        return 1
    if not last_commit:
        print("CLOSEOUT_READY_FAILED")
        print("- reason: missing last_commit")
        return 1
    if not last_validation:
        print("CLOSEOUT_READY_FAILED")
        print("- reason: missing last_validation entries")
        return 1

    print("CLOSEOUT_READY_OK")
    print(f"- focus_activity_id: {focus.activity_id}")
    print(f"- current_slice_id: {current_slice_id}")
    print(f"- next_slice_id: {next_slice_id}")
    print(f"- last_commit: {last_commit}")
    print(f"- advisory_hits: {len(summary.advisory_commands)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
