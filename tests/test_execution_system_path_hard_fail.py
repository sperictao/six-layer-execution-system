#!/usr/bin/env python3
from __future__ import annotations

from execution_system_paths import command_str
from scripts.run_execution_system_checks import ExecutionSystemSummary, summary_footer
import scripts.check_closeout_ready as closeout_ready
import scripts.accept_active_ledger_v2 as acceptance


def expect(text: str, needle: str) -> None:
    if needle not in text:
        raise AssertionError(f"missing expected text: {needle}\n{text}")


def main() -> int:
    failing_command = command_str("check_active_consistency.py")
    failed_summary = ExecutionSystemSummary(
        hard_fail_status="failed",
        first_failing_command=failing_command,
        advisory_commands=[],
    )

    footer = "\n".join(summary_footer(failed_summary))
    expect(footer, "- hard_fail_status: failed")
    expect(footer, f"- first_failing_command: {failing_command}")
    expect(footer, "- recovery_hint: repair ACTIVE.md or repo drift first")

    original_collect_summary_closeout = closeout_ready.collect_summary
    closeout_ready.collect_summary = lambda print_output=False: (1, failed_summary)
    try:
        closeout_code = int(closeout_ready.main())
        if closeout_code == 0:
            raise AssertionError("closeout_ready should fail for hard-fail summary")
    finally:
        closeout_ready.collect_summary = original_collect_summary_closeout

    original_run_check = acceptance.run_check

    def fake_run_check(name: str, cmd: list[str]) -> tuple[str, str]:
        if name == "execution-system-suite":
            return "fail", f"EXECUTION_SYSTEM_SUMMARY_STATUS:failed\nfirst_failing_command={failing_command}\nadvisory_hits=0"
        return "ok", "stubbed-ok"

    acceptance.run_check = fake_run_check
    try:
        acceptance_code = int(acceptance.main())
        if acceptance_code == 0:
            raise AssertionError("acceptance should fail for hard-fail execution-system-suite")
    finally:
        acceptance.run_check = original_run_check

    print("EXECUTION_WORKFLOW_HARD_FAIL_SMOKE_OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
