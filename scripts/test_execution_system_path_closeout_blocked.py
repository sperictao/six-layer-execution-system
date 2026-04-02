#!/usr/bin/env python3
from __future__ import annotations

import scripts.check_closeout_ready as closeout_ready
from scripts.run_execution_system_checks import ExecutionSystemSummary
from execution_system_paths import command_str


class FakeFocus:
    activity_id = "one-publish-refactor"

    def scalar(self, field: str):
        values = {
            "type": "roadmap",
            "current_slice_id": "PR-E.P22",
            "next_slice_id": "PR-E.P23",
            "last_commit": "5e42765",
        }
        return values.get(field)

    def items(self, field: str):
        if field == "last_validation":
            return []
        return []


class FakeLedger:
    def get_current_focus_activity(self):
        return FakeFocus()


def expect(text: str, needle: str) -> None:
    if needle not in text:
        raise AssertionError(f"missing expected text: {needle}\n{text}")


def main() -> int:
    passed_summary = ExecutionSystemSummary(
        hard_fail_status="passed",
        first_failing_command=None,
        advisory_commands=[command_str("check_oversized_migration_slices.py")],
    )

    original_collect_summary = closeout_ready.collect_summary
    original_parse_ledger = closeout_ready.parse_ledger
    closeout_ready.collect_summary = lambda print_output=False: (0, passed_summary)
    closeout_ready.parse_ledger = lambda path=None: FakeLedger()

    try:
        import io
        import contextlib

        buffer = io.StringIO()
        with contextlib.redirect_stdout(buffer):
            code = int(closeout_ready.main())
        output = buffer.getvalue()
    finally:
        closeout_ready.collect_summary = original_collect_summary
        closeout_ready.parse_ledger = original_parse_ledger

    if code == 0:
        raise AssertionError(output)

    expect(output, "CLOSEOUT_READY_FAILED")
    expect(output, "- reason: missing last_validation entries")

    print("EXECUTION_WORKFLOW_CLOSEOUT_BLOCKED_SMOKE_OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
