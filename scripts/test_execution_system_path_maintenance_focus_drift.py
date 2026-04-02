#!/usr/bin/env python3
from __future__ import annotations

import sys
from pathlib import Path
from types import SimpleNamespace

from execution_system_paths import WORKSPACE
sys.path.insert(0, str(WORKSPACE / "scripts"))

import check_execution_system_maintenance_mode as maintenance  # noqa: E402


class FakeActivity:
    def __init__(self, activity_id: str, fields: dict[str, str]):
        self.activity_id = activity_id
        self.heading = activity_id
        self._fields = fields

    def scalar(self, key: str) -> str | None:
        return self._fields.get(key)


class FakeLedger:
    def __init__(self, focus: FakeActivity, runnable: list[FakeActivity], execution_activity: FakeActivity):
        self._focus = focus
        self._runnable = runnable
        self._execution = execution_activity

    def get_activity(self, activity_id: str):
        if activity_id == "execution-system-spec-v1":
            return self._execution
        return None

    def get_current_focus_activity(self):
        return self._focus

    def list_runnable_activities(self):
        return self._runnable


def expect(text: str, needle: str) -> None:
    if needle not in text:
        raise AssertionError(f"missing expected text: {needle}\n{text}")


def run_with(ledger: FakeLedger, acceptance_output: str, acceptance_code: int = 0) -> tuple[int, str]:
    original_parse = maintenance.parse_ledger
    original_run = maintenance.subprocess.run

    def fake_parse_ledger():
        return ledger

    def fake_run(*args, **kwargs):
        return SimpleNamespace(returncode=acceptance_code, stdout=acceptance_output, stderr="")

    maintenance.parse_ledger = fake_parse_ledger
    maintenance.subprocess.run = fake_run
    try:
        import contextlib
        import io

        buffer = io.StringIO()
        with contextlib.redirect_stdout(buffer):
            code = int(maintenance.main())
        return code, buffer.getvalue()
    finally:
        maintenance.parse_ledger = original_parse
        maintenance.subprocess.run = original_run


def main() -> int:
    execution = FakeActivity("execution-system-spec-v1", {"status": "parked", "autopilot": "false"})
    approved_focus = FakeActivity(
        "execution-system-decomposition-upgrade",
        {"type": "roadmap", "autopilot": "false", "status": "in_progress"},
    )
    disallowed_focus = FakeActivity(
        "docs-random-focus",
        {"type": "roadmap", "autopilot": "false", "status": "in_progress"},
    )
    runnable = [FakeActivity("one-publish-refactor", {"autopilot": "true", "status": "ready"})]

    approved_ledger = FakeLedger(approved_focus, runnable, execution)
    code, output = run_with(
        approved_ledger,
        "ACTIVE_LEDGER_V2_ACCEPTANCE_OK_WITH_POLICY_GATES\n- policy_gates: focus-first",
    )
    if code != 0:
        raise AssertionError(output)
    expect(output, "EXECUTION_SYSTEM_MAINTENANCE_OK")
    expect(output, "- focus_activity_id: execution-system-decomposition-upgrade")

    disallowed_ledger = FakeLedger(disallowed_focus, runnable, execution)
    code, output = run_with(
        disallowed_ledger,
        "ACTIVE_LEDGER_V2_ACCEPTANCE_OK_WITH_POLICY_GATES\n- policy_gates: focus-first",
    )
    if code == 0:
        raise AssertionError("disallowed non-business focus should fail")
    expect(output, "EXECUTION_SYSTEM_MAINTENANCE_FAILED")
    expect(output, "- reason: current focus is neither runnable business work nor an approved non-runnable maintenance focus")

    print("EXECUTION_SYSTEM_MAINTENANCE_FOCUS_DRIFT_SMOKE_OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
