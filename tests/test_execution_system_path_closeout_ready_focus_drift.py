#!/usr/bin/env python3
from __future__ import annotations

import sys
from types import SimpleNamespace

from execution_system_paths import WORKSPACE
sys.path.insert(0, str(WORKSPACE))

import scripts.check_closeout_ready as closeout_ready  # noqa: E402


class FakeSummary(SimpleNamespace):
    pass


class FakeActivity:
    def __init__(self, activity_id: str, fields: dict[str, object]):
        self.activity_id = activity_id
        self.heading = activity_id
        self._fields = fields

    def scalar(self, key: str):
        value = self._fields.get(key)
        return value if isinstance(value, str) else None

    def items(self, key: str):
        value = self._fields.get(key)
        return list(value) if isinstance(value, list) else []


class FakeLedger:
    def __init__(self, focus: FakeActivity):
        self._focus = focus

    def get_current_focus_activity(self):
        return self._focus


def expect(text: str, needle: str) -> None:
    if needle not in text:
        raise AssertionError(f"missing expected text: {needle}\n{text}")


def main() -> int:
    original_collect = closeout_ready.collect_summary
    original_parse = closeout_ready.parse_ledger

    synthetic_focus = FakeActivity(
        "synthetic-governance-line",
        {
            "type": "roadmap",
            "current_slice_id": "GD-X.X1",
            "next_slice_id": "GD-X.X2",
            "last_commit": "abc1234",
            "last_validation": ["python3 synthetic-check passed"],
        },
    )

    def fake_collect_summary(print_output: bool = False):
        return 0, FakeSummary(hard_fail_status="passed", first_failing_command=None, advisory_commands=[])

    def fake_parse_ledger(path):
        return FakeLedger(synthetic_focus)

    closeout_ready.collect_summary = fake_collect_summary
    closeout_ready.parse_ledger = fake_parse_ledger
    try:
        import contextlib
        import io

        buffer = io.StringIO()
        with contextlib.redirect_stdout(buffer):
            code = int(closeout_ready.main())
        output = buffer.getvalue()
    finally:
        closeout_ready.collect_summary = original_collect
        closeout_ready.parse_ledger = original_parse

    if code != 0:
        raise AssertionError(output)

    expect(output, "CLOSEOUT_READY_OK")
    expect(output, "- focus_activity_id: synthetic-governance-line")
    expect(output, "- current_slice_id: GD-X.X1")
    expect(output, "- next_slice_id: GD-X.X2")
    expect(output, "- advisory_hits: 0")

    print("EXECUTION_SYSTEM_CLOSEOUT_READY_FOCUS_DRIFT_SMOKE_OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
