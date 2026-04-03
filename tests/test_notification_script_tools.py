#!/usr/bin/env python3
from __future__ import annotations

import json
import subprocess
from pathlib import Path

import scripts.normalize_notifications_state as normalize_notifications_state
from test_workspace_clone import cloned_workspace, workspace_env


def expect(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def run_script(
    script: Path,
    *args: str,
    env: dict[str, str],
    extra_env: dict[str, str] | None = None,
) -> subprocess.CompletedProcess[str]:
    merged_env = dict(env)
    if extra_env:
        merged_env.update(extra_env)
    return subprocess.run(
        ["python3", str(script), *args],
        text=True,
        capture_output=True,
        check=False,
        env=merged_env,
    )


def read_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def main() -> int:
    expect(
        normalize_notifications_state.infer_activity_id({"activity_id": "existing"}) == "existing",
        "infer_activity_id should keep explicit activity_id",
    )
    expect(
        normalize_notifications_state.infer_activity_id({"repo": "notification-test-repo"}) == "notification-test",
        "infer_activity_id should infer notification-test repo",
    )
    expect(
        normalize_notifications_state.infer_activity_id({"repo": "other"}) is None,
        "infer_activity_id should return None when no inference is possible",
    )
    expect(
        normalize_notifications_state.infer_activity_type({"activity_type": "waiting"}) == "waiting",
        "infer_activity_type should keep explicit activity_type",
    )
    expect(
        normalize_notifications_state.infer_activity_type({"completed_slice_id": "A1"}) == "roadmap",
        "infer_activity_type should infer roadmap when closeout fields exist",
    )
    expect(
        normalize_notifications_state.infer_activity_type({}) == "unknown",
        "infer_activity_type should return unknown when no hint exists",
    )

    with cloned_workspace() as workspace:
        env = workspace_env(workspace)
        state_path = workspace / "memory" / "notifications-state.json"
        closeout_path = workspace / "memory" / "last-slice-closeout.json"

        normalize_script = workspace / "scripts" / "normalize_notifications_state.py"
        create_script = workspace / "scripts" / "create_slice_closeout.py"
        queue_script = workspace / "scripts" / "queue_slice_notification.py"
        flush_script = workspace / "scripts" / "flush_slice_notifications.py"
        inflight_script = workspace / "scripts" / "get_inflight_notification.py"
        ack_script = workspace / "scripts" / "ack_slice_notification.py"
        requeue_script = workspace / "scripts" / "requeue_inflight_notifications.py"
        payload_script = workspace / "scripts" / "send_slice_notification_payload.py"

        proc = run_script(inflight_script, env=env)
        expect(proc.returncode == 0, proc.stdout + proc.stderr)
        expect(proc.stdout.strip() == "NO_INFLIGHT_NOTIFICATIONS", proc.stdout + proc.stderr)

        if state_path.exists():
            state_path.unlink()
        proc = run_script(normalize_script, env=env)
        expect(proc.returncode == 0, proc.stdout + proc.stderr)
        expect(proc.stdout.strip() == "CREATED_V2", proc.stdout + proc.stderr)
        normalized = read_json(state_path)
        expect(normalized == {"version": 2, "pending": [], "inflight": [], "sent": []}, str(normalized))

        legacy_state = {
            "pending": [
                {
                    "repo": "notification-test-repo",
                    "completed_slice_id": "NT-X1",
                    "commit": "abc123",
                }
            ],
            "inflight": [
                {
                    "activity_id": "existing-activity",
                }
            ],
            "sent": [
                {
                    "activity_type": "waiting",
                }
            ],
        }
        state_path.write_text(json.dumps(legacy_state, ensure_ascii=True, indent=2) + "\n", encoding="utf-8")
        proc = run_script(normalize_script, env=env)
        expect(proc.returncode == 0, proc.stdout + proc.stderr)
        expect(proc.stdout.strip() == "NORMALIZED_V2", proc.stdout + proc.stderr)
        normalized = read_json(state_path)
        expect(normalized["version"] == 2, str(normalized))
        expect(normalized["pending"][0]["activity_id"] == "notification-test", str(normalized))
        expect(normalized["pending"][0]["activity_type"] == "roadmap", str(normalized))
        expect(normalized["inflight"][0]["activity_id"] == "existing-activity", str(normalized))
        expect(normalized["inflight"][0]["activity_type"] == "unknown", str(normalized))
        expect(normalized["sent"][0]["activity_type"] == "waiting", str(normalized))

        if closeout_path.exists():
            closeout_path.unlink()
        proc = run_script(payload_script, env=env)
        expect(proc.returncode == 0, proc.stdout + proc.stderr)
        expect(proc.stdout.strip() == "NO_SLICE_CLOSEOUT", proc.stdout + proc.stderr)

        closeout_path.write_text("{}\n", encoding="utf-8")
        proc = run_script(queue_script, env=env)
        expect(proc.returncode == 1, proc.stdout + proc.stderr)
        expect(proc.stdout.strip() == "NO_SLICE_CLOSEOUT", proc.stdout + proc.stderr)

        closeout_path.write_text(json.dumps({"activity_id": "missing-dedupe"}) + "\n", encoding="utf-8")
        proc = run_script(queue_script, env=env)
        expect(proc.returncode == 1, proc.stdout + proc.stderr)
        expect(proc.stdout.strip() == "INVALID_SLICE_CLOSEOUT", proc.stdout + proc.stderr)

        proc = run_script(
            create_script,
            "--activity-id",
            "roadmap-line",
            "--current-focus-activity-id",
            "other-line",
            "--activity-type",
            "roadmap",
            "--repo",
            "notification-repo",
            "--completed-slice-id",
            "NT-X1",
            "--next-slice-id",
            "NT-X2",
            "--commit",
            "abc123",
            env=env,
        )
        expect(proc.returncode != 0, proc.stdout + proc.stderr)
        expect(
            "--current-focus-activity-id must equal --activity-id for roadmap closeout" in proc.stderr,
            proc.stdout + proc.stderr,
        )

        proc = run_script(
            create_script,
            "--activity-id",
            "notification-test",
            "--current-focus-activity-id",
            "notification-test",
            "--activity-type",
            "roadmap",
            "--repo",
            "notification-repo",
            "--completed-slice-id",
            "NT-X1",
            "--next-slice-id",
            "NT-X2",
            "--commit",
            "abc123",
            "--validation",
            "python3 tests/test_notification_script_tools.py",
            env=env,
        )
        expect(proc.returncode == 0, proc.stdout + proc.stderr)
        artifact = json.loads(proc.stdout)
        dedupe_key = artifact["dedupe_key"]
        expect(artifact["current_focus_activity_id"] == "notification-test", str(artifact))
        expect("验证：" in artifact["message"], str(artifact))

        proc = run_script(payload_script, env=env)
        expect(proc.returncode == 0, proc.stdout + proc.stderr)
        payload = json.loads(proc.stdout)
        expect(payload["dedupe_key"] == dedupe_key, str(payload))
        expect(payload["current_focus_activity_id"] == "notification-test", str(payload))

        proc = run_script(queue_script, env=env)
        expect(proc.returncode == 0, proc.stdout + proc.stderr)
        expect(proc.stdout.strip() == dedupe_key, proc.stdout + proc.stderr)
        queued_state = read_json(state_path)
        expect(len(queued_state["pending"]) == 2, str(queued_state))
        expect(
            any(item.get("dedupe_key") == dedupe_key for item in queued_state["pending"]),
            str(queued_state),
        )

        state_path.write_text(
            json.dumps({"version": 2, "pending": [], "inflight": [], "sent": []}, ensure_ascii=True, indent=2) + "\n",
            encoding="utf-8",
        )
        proc = run_script(queue_script, env=env)
        expect(proc.returncode == 0, proc.stdout + proc.stderr)
        expect(proc.stdout.strip() == dedupe_key, proc.stdout + proc.stderr)
        proc = run_script(queue_script, env=env)
        expect(proc.returncode == 0, proc.stdout + proc.stderr)
        expect(proc.stdout.strip() == dedupe_key, proc.stdout + proc.stderr)
        queued_state = read_json(state_path)
        expect(len(queued_state["pending"]) == 1, str(queued_state))

        proc = run_script(flush_script, env=env)
        expect(proc.returncode == 0, proc.stdout + proc.stderr)
        flushed_item = json.loads(proc.stdout)
        expect(flushed_item["dedupe_key"] == dedupe_key, str(flushed_item))
        expect("flushed_at" in flushed_item, str(flushed_item))

        proc = run_script(inflight_script, env=env)
        expect(proc.returncode == 0, proc.stdout + proc.stderr)
        inflight_item = json.loads(proc.stdout)
        expect(inflight_item["dedupe_key"] == dedupe_key, str(inflight_item))

        proc = run_script(ack_script, dedupe_key, env=env)
        expect(proc.returncode == 3, proc.stdout + proc.stderr)
        expect("DIRECT_ACK_FORBIDDEN" in proc.stderr, proc.stdout + proc.stderr)

        proc = run_script(ack_script, env=env, extra_env={"COMPLETE_SLICE_ACK": "1"})
        expect(proc.returncode == 2, proc.stdout + proc.stderr)
        expect("usage: ack_slice_notification.py <dedupe_key>" in proc.stderr, proc.stdout + proc.stderr)

        proc = run_script(
            ack_script,
            "missing-key",
            env=env,
            extra_env={"COMPLETE_SLICE_ACK": "1"},
        )
        expect(proc.returncode == 1, proc.stdout + proc.stderr)
        expect(proc.stdout.strip() == "NOT_FOUND", proc.stdout + proc.stderr)

        proc = run_script(
            ack_script,
            dedupe_key,
            env=env,
            extra_env={"COMPLETE_SLICE_ACK": "1"},
        )
        expect(proc.returncode == 0, proc.stdout + proc.stderr)
        expect(proc.stdout.strip() == dedupe_key, proc.stdout + proc.stderr)
        acked_state = read_json(state_path)
        expect(acked_state["inflight"] == [], str(acked_state))
        expect(acked_state["sent"][0]["dedupe_key"] == dedupe_key, str(acked_state))
        expect("sent_at" in acked_state["sent"][0], str(acked_state))

        proc = run_script(requeue_script, env=env)
        expect(proc.returncode == 0, proc.stdout + proc.stderr)
        expect(proc.stdout.strip() == "NO_INFLIGHT_NOTIFICATIONS", proc.stdout + proc.stderr)

        state_path.write_text(
            json.dumps(
                {
                    "version": 2,
                    "pending": [{"dedupe_key": "dup"}],
                    "inflight": [
                        {"dedupe_key": "dup", "flushed_at": "old"},
                        {"dedupe_key": "new", "flushed_at": "old", "repo": "notification-test-other"},
                    ],
                    "sent": [],
                },
                ensure_ascii=True,
                indent=2,
            )
            + "\n",
            encoding="utf-8",
        )
        proc = run_script(requeue_script, env=env)
        expect(proc.returncode == 0, proc.stdout + proc.stderr)
        expect(proc.stdout.strip() == "REQUEUED:1", proc.stdout + proc.stderr)
        requeued_state = read_json(state_path)
        expect(requeued_state["inflight"] == [], str(requeued_state))
        expect(len(requeued_state["pending"]) == 2, str(requeued_state))
        moved = next(item for item in requeued_state["pending"] if item["dedupe_key"] == "new")
        expect("flushed_at" not in moved, str(requeued_state))

        proc = run_script(flush_script, env=env)
        expect(proc.returncode == 0, proc.stdout + proc.stderr)
        proc = run_script(inflight_script, env=env)
        expect(proc.returncode == 0, proc.stdout + proc.stderr)
        expect(json.loads(proc.stdout)["dedupe_key"] in {"dup", "new"}, proc.stdout + proc.stderr)

    print("NOTIFICATION_SCRIPT_TOOLS_SMOKE_OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
