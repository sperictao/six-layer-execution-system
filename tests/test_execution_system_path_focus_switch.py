#!/usr/bin/env python3
from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

from execution_system_paths import WORKSPACE
TESTS_DIR = Path(__file__).resolve().parent
REPO_ROOT = TESTS_DIR.parent
ACTIVE_SMOKE = TESTS_DIR / "test_check_active_consistency.py"
FOCUS_FIRST = WORKSPACE / "scripts" / "validate_focus_first.py"
ACCEPT = WORKSPACE / "scripts" / "accept_active_ledger_v2.py"
sys.path.insert(0, str(WORKSPACE / "scripts"))

from active_ledger import parse_ledger  # noqa: E402


def run_env() -> dict[str, str]:
    env = os.environ.copy()
    env["PYTHONPATH"] = os.pathsep.join(
        [str(WORKSPACE), str(WORKSPACE / "scripts"), env.get("PYTHONPATH", "")]
    ).strip(os.pathsep)
    return env


def run(script: Path) -> tuple[int, str]:
    proc = subprocess.run(
        ["python3", str(script)],
        text=True,
        capture_output=True,
        check=False,
        cwd=REPO_ROOT,
        env=run_env(),
    )
    return proc.returncode, proc.stdout + proc.stderr


def expect(output: str, needle: str) -> None:
    if needle not in output:
        raise AssertionError(f"missing expected text: {needle}\n{output}")


def main() -> int:
    ledger = parse_ledger()
    focus = ledger.get_current_focus_activity()
    if focus is None:
        raise AssertionError("missing focus activity")

    code, output = run(ACTIVE_SMOKE)
    if code != 0:
        raise AssertionError(output)
    expect(output, "ACTIVE_CHECKER_SMOKE_OK")

    code, output = run(FOCUS_FIRST)
    if code == 0:
        raise AssertionError("focus validation should currently report a policy gate")
    expect(output, "FOCUS_VALIDATION_POLICY_GATE")
    expect(output, f"- focus_activity_id: {focus.activity_id}")

    code, output = run(ACCEPT)
    if code != 0:
        raise AssertionError(output)
    expect(output, "ACTIVE_LEDGER_V2_ACCEPTANCE_OK_WITH_POLICY_GATES")
    expect(output, "[POLICY_GATE] focus-first")

    print("EXECUTION_WORKFLOW_FOCUS_SWITCH_SMOKE_OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
