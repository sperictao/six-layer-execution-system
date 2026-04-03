#!/usr/bin/env python3
from __future__ import annotations

import contextlib
import io
import json
import sys
import tempfile
from pathlib import Path

import scripts.ack_slice_notification as ack_notification
import scripts.active_ledger as active_ledger
import scripts.check_oversized_migration_slices as oversized_slices
import scripts.check_parallel_safety as parallel_safety
import scripts.check_slice_closeout as check_slice_closeout
import scripts.check_task_dependency_graph as dependency_graph
import scripts.flush_slice_notifications as flush_notifications
import scripts.get_inflight_notification as get_inflight
import scripts.queue_slice_notification as queue_notification
import scripts.requeue_inflight_notifications as requeue_notifications
import scripts.run_execution_system_checks as runner
import scripts.send_slice_notification_payload as send_payload


def expect(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def capture_main(fn) -> tuple[int, str]:
    buffer = io.StringIO()
    with contextlib.redirect_stdout(buffer):
        code = int(fn())
    return code, buffer.getvalue()


def main() -> int:
    with tempfile.TemporaryDirectory(prefix="six-layer-edge-state-") as tmpdir:
        missing = Path(tmpdir) / "missing.json"
        expect(ack_notification.read_json(missing)["version"] == 2, "ack read_json should default missing files")
        expect(flush_notifications.read_json(missing)["pending"] == [], "flush read_json should default missing files")
        expect(get_inflight.read_json(missing)["inflight"] == [], "get_inflight read_json should default missing files")
        expect(queue_notification.read_json(missing)["sent"] == [], "queue read_json should default missing files")
        expect(requeue_notifications.read_json(missing)["version"] == 2, "requeue read_json should default missing files")
        expect(check_slice_closeout.read_json(missing)["pending"] == [], "check_slice_closeout read_json should default missing files")

    sample_ledger = """# ACTIVE

## Ledger meta
- version: `2`
- current_focus_activity_id: `focus`

## Activity index
- `focus`

## Activities
### Activity: focus
- activity_id: `focus`
- title: `Focus`
- type: roadmap
- status: ready
- priority: P1
- autopilot: false
"""
    with tempfile.TemporaryDirectory(prefix="six-layer-active-edge-") as tmpdir:
        ledger_path = Path(tmpdir) / "ACTIVE.md"
        ledger_path.write_text(sample_ledger, encoding="utf-8")
        ledger = active_ledger.parse_ledger(ledger_path)
        focus = ledger.get_current_focus_activity()
        expect(focus is not None and focus.scalar("type") == "roadmap", ledger.as_dict().__repr__())
        expect(focus.scalar("status") == "ready", ledger.as_dict().__repr__())

    expect(not oversized_slices.is_in_scope_slice("#### Slice X - Demo", {}), "phase_id missing should be out of scope")
    with tempfile.TemporaryDirectory(prefix="six-layer-parallel-edge-") as tmpdir:
        task_doc = Path(tmpdir) / "edge.md"
        task_doc.write_text(
            "\n".join(
                [
                    "### Not a slice",
                    "- parallel_safe: `true`",
                    "",
                    "#### Slice E1 - No safety fields",
                    "- phase_id: `PH-1`",
                ]
            ),
            encoding="utf-8",
        )
        expect(parallel_safety.validate_task_doc(task_doc) == [], "non-slice and no-field blocks should be skipped")
        expect(dependency_graph.parse_dep_values("") == [], "empty dependency list should be empty")
        expect(dependency_graph.validate_task_doc(task_doc) == [], "non-matching dependency blocks should be skipped")

    original_closeout = check_slice_closeout.CLOSEOUT
    original_state = check_slice_closeout.STATE
    try:
        with tempfile.TemporaryDirectory(prefix="six-layer-closeout-edge-") as tmpdir:
            tmp = Path(tmpdir)
            closeout = tmp / "closeout.json"
            state = tmp / "state.json"
            check_slice_closeout.CLOSEOUT = closeout
            check_slice_closeout.STATE = state

            code, output = capture_main(check_slice_closeout.main)
            expect(code == 1, output)
            expect("SLICE_CLOSEOUT_MISSING:artifact" in output, output)

            closeout.write_text(json.dumps({"activity_id": "a"}) + "\n", encoding="utf-8")
            code, output = capture_main(check_slice_closeout.main)
            expect(code == 1 and "SLICE_CLOSEOUT_MISSING:dedupe_key" in output, output)

            closeout.write_text(json.dumps({"dedupe_key": "k"}) + "\n", encoding="utf-8")
            code, output = capture_main(check_slice_closeout.main)
            expect(code == 1 and "SLICE_CLOSEOUT_MISSING:activity_id" in output, output)

            closeout.write_text(
                json.dumps(
                    {
                        "dedupe_key": "k",
                        "activity_id": "a",
                        "current_focus_activity_id": "a",
                        "activity_type": "roadmap",
                        "validation_state": "validated",
                        "slice_state": "closed_out",
                    }
                )
                + "\n",
                encoding="utf-8",
            )
            code, output = capture_main(check_slice_closeout.main)
            expect(code == 1 and "SLICE_CLOSEOUT_MISSING:a:k" in output, output)
    finally:
        check_slice_closeout.CLOSEOUT = original_closeout
        check_slice_closeout.STATE = original_state

    original_state = flush_notifications.STATE
    try:
        with tempfile.TemporaryDirectory(prefix="six-layer-flush-edge-") as tmpdir:
            flush_notifications.STATE = Path(tmpdir) / "state.json"
            code, output = capture_main(flush_notifications.main)
            expect(code == 0 and "NO_PENDING_NOTIFICATIONS" in output, output)
    finally:
        flush_notifications.STATE = original_state

    original_closeout = send_payload.CLOSEOUT
    try:
        with tempfile.TemporaryDirectory(prefix="six-layer-payload-edge-") as tmpdir:
            send_payload.CLOSEOUT = Path(tmpdir) / "closeout.json"
            send_payload.CLOSEOUT.write_text("{}\n", encoding="utf-8")
            code, output = capture_main(send_payload.main)
            expect(code == 0 and "NO_SLICE_CLOSEOUT" in output, output)
    finally:
        send_payload.CLOSEOUT = original_closeout

    original_path = runner.Path
    try:
        class ResolvePath(Path):
            _flavour = type(Path())._flavour

            def resolve(self):
                if str(self).endswith(f"plugins/{runner.WORKSPACE.name}"):
                    raise FileNotFoundError("broken plugin link")
                return super().resolve()

        runner.Path = ResolvePath
        original_file = runner.__file__
        try:
            runner.__file__ = str(Path("/tmp/run_execution_system_checks.py"))
            tests_root, reason = runner.discover_repo_tests_root()
            expect(tests_root is None and reason == "repo checkout not detected from plugin layout", str((tests_root, reason)))
        finally:
            runner.__file__ = original_file
    finally:
        runner.Path = original_path

    print("EDGE_BRANCH_COVERAGE_SMOKE_OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
