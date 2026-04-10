#!/usr/bin/env python3
from __future__ import annotations

import sys

from execution_system_paths import WORKSPACE
sys.path.insert(0, str(WORKSPACE))
sys.path.insert(0, str(WORKSPACE / "scripts"))

import scripts.accept_active_ledger_v2 as acceptance
import scripts.validate_focus_first as focus_first
from execution_system_paths import command_str
from active_ledger import parse_ledger  # noqa: E402


def expect(text: str, needle: str) -> None:
    if needle not in text:
        raise AssertionError(f"missing expected text: {needle}\n{text}")


def main() -> int:
    ledger = parse_ledger()
    focus = ledger.get_current_focus_activity()
    if focus is None:
        raise AssertionError("missing focus activity")

    original_run_check = acceptance.run_check

    def fake_run_check(name: str, cmd: list[str]) -> tuple[str, str]:
        if name == "execution-system-suite":
            return (
                "ok",
                "EXECUTION_SYSTEM_SUMMARY_STATUS:passed\n"
                "first_failing_command=none\n"
                "advisory_commands_run=1\n"
                "advisory_hits=0",
            )
        if name == "focus-first":
            return (
                "policy_gate",
                "FOCUS_VALIDATION_POLICY_GATE\n"
                f"- focus_activity_id: {focus.activity_id}\n"
                "- focus activity is not autopilot=true\n"
                "- focus activity is not in runnable activity set\n"
                "- note: focus-first remains intact; current focus is intentionally not auto-runnable",
            )
        return "ok", "stubbed-ok"

    acceptance.run_check = fake_run_check
    try:
        import contextlib
        import io

        focus_buffer = io.StringIO()
        with contextlib.redirect_stdout(focus_buffer):
            focus_code = int(focus_first.main())
        focus_output = focus_buffer.getvalue()

        if focus_code != 2:
            raise AssertionError(f"expected policy gate exit code 2\n{focus_output}")
        expect(focus_output, "FOCUS_VALIDATION_POLICY_GATE")
        expect(focus_output, f"- focus_activity_id: {focus.activity_id}")
        expect(focus_output, "- note: focus-first remains intact; current focus is intentionally not auto-runnable")

        acceptance_buffer = io.StringIO()
        with contextlib.redirect_stdout(acceptance_buffer):
            acceptance_code = int(acceptance.main())
        acceptance_output = acceptance_buffer.getvalue()

        if acceptance_code != 0:
            raise AssertionError(acceptance_output)
        expect(acceptance_output, "ACTIVE_LEDGER_V2_ACCEPTANCE_OK_WITH_POLICY_GATES")
        expect(acceptance_output, "- policy_gates: focus-first")
        expect(acceptance_output, "[OK] execution-system-suite")
        expect(acceptance_output, "[POLICY_GATE] focus-first")
    finally:
        acceptance.run_check = original_run_check

    print("EXECUTION_SYSTEM_FOCUS_ACCEPTANCE_DRIFT_SMOKE_OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
