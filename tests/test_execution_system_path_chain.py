#!/usr/bin/env python3
from __future__ import annotations

import subprocess
import sys
from pathlib import Path

from execution_system_paths import WORKSPACE
RUNNER = WORKSPACE / "scripts" / "run_execution_system_checks.py"
ACCEPT = WORKSPACE / "scripts" / "accept_active_ledger_v2.py"
CLOSEOUT_READY = WORKSPACE / "scripts" / "check_closeout_ready.py"
sys.path.insert(0, str(WORKSPACE / "scripts"))

from active_ledger import parse_ledger  # noqa: E402


def run(script: Path) -> tuple[int, str]:
    proc = subprocess.run(["python3", str(script)], text=True, capture_output=True, check=False)
    return proc.returncode, proc.stdout + proc.stderr


def expect(output: str, needle: str) -> None:
    if needle not in output:
        raise AssertionError(f"missing expected text: {needle}\n{output}")


def main() -> int:
    ledger = parse_ledger()
    focus = ledger.get_current_focus_activity()
    if focus is None:
        raise AssertionError("missing focus activity")

    code, runner_output = run(RUNNER)
    if code != 0:
        raise AssertionError(runner_output)
    expect(runner_output, "EXECUTION_SYSTEM_CHECKS_OK")
    expect(runner_output, "EXECUTION_SYSTEM_SUMMARY")
    expect(runner_output, "- hard_fail_status: passed")
    expect(runner_output, "- advisory_commands_run: 1")
    expect(runner_output, "- advisory_hits: 0")

    code, closeout_output = run(CLOSEOUT_READY)
    if focus.scalar("type") == "roadmap":
        if code != 0:
            raise AssertionError(closeout_output)
        expect(closeout_output, "CLOSEOUT_READY_OK")
        expect(closeout_output, f"- focus_activity_id: {focus.activity_id}")
    else:
        if code == 0:
            raise AssertionError("closeout-ready should fail for non-roadmap focus")
        expect(closeout_output, "CLOSEOUT_READY_FAILED")
        expect(closeout_output, f"- reason: focus activity is not roadmap ({focus.scalar('type')})")

    code, acceptance_output = run(ACCEPT)
    if code != 0:
        raise AssertionError(acceptance_output)
    expect(acceptance_output, "[OK] execution-system-suite")
    expect(acceptance_output, "EXECUTION_SYSTEM_SUMMARY_STATUS:passed")
    expect(acceptance_output, "ACTIVE_LEDGER_V2_ACCEPTANCE_OK_WITH_POLICY_GATES")

    print("EXECUTION_WORKFLOW_CHAIN_SMOKE_OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
