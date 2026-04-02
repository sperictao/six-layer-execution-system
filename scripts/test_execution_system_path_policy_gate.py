#!/usr/bin/env python3
from __future__ import annotations

from execution_system_paths import command_str
import scripts.accept_active_ledger_v2 as acceptance


def expect(text: str, needle: str) -> None:
    if needle not in text:
        raise AssertionError(f"missing expected text: {needle}\n{text}")


def main() -> int:
    original_run_check = acceptance.run_check

    def fake_run_check(name: str, cmd: list[str]) -> tuple[str, str]:
        if name == "execution-system-suite":
            return "ok", f"EXECUTION_SYSTEM_SUMMARY_STATUS:passed\nfirst_failing_command=none\nadvisory_hits=1\nadvisory_command={command_str('check_oversized_migration_slices.py')}"
        if name == "focus-first":
            return "policy_gate", "FOCUS_VALIDATION_POLICY_GATE\n- focus_activity_id: execution-system-spec-v1\n- focus activity is not autopilot=true\n- note: focus-first remains intact; current focus is intentionally not auto-runnable"
        return "ok", "stubbed-ok"

    acceptance.run_check = fake_run_check
    try:
        import io
        import contextlib

        buffer = io.StringIO()
        with contextlib.redirect_stdout(buffer):
            code = int(acceptance.main())
        output = buffer.getvalue()
    finally:
        acceptance.run_check = original_run_check

    if code != 0:
        raise AssertionError(output)

    expect(output, "[POLICY_GATE] focus-first")
    expect(output, "ACTIVE_LEDGER_V2_ACCEPTANCE_OK_WITH_POLICY_GATES")
    expect(output, "- policy_gates: focus-first")
    expect(output, "[OK] execution-system-suite")

    print("EXECUTION_WORKFLOW_POLICY_GATE_SMOKE_OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
