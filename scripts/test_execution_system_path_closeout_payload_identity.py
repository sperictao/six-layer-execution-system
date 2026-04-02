#!/usr/bin/env python3
from __future__ import annotations

import json
import subprocess

from test_workspace_clone import cloned_workspace, workspace_env


def main() -> int:
    with cloned_workspace() as workspace:
        env = workspace_env(workspace)
        create = workspace / "scripts" / "create_slice_closeout.py"
        queue = workspace / "scripts" / "queue_slice_notification.py"
        check = workspace / "scripts" / "check_slice_closeout.py"
        payload_script = workspace / "scripts" / "send_slice_notification_payload.py"
        closeout = workspace / "memory" / "last-slice-closeout.json"
        state_path = workspace / "memory" / "notifications-state.json"
        subprocess.run(
            [
                "python3",
                str(create),
                "--activity-id",
                "test-activity",
                "--current-focus-activity-id",
                "test-activity",
                "--activity-type",
                "roadmap",
                "--repo",
                "test-repo",
                "--completed-slice-id",
                "TEST.P1",
                "--next-slice-id",
                "TEST.P2",
                "--commit",
                "abc123",
                "--validation",
                "path check passed",
            ],
            check=True,
            text=True,
            capture_output=True,
            env=env,
        )

        subprocess.run(["python3", str(queue)], check=True, text=True, capture_output=True, env=env)
        subprocess.run(["python3", str(check)], check=True, text=True, capture_output=True, env=env)

        artifact = json.loads(closeout.read_text(encoding="utf-8"))
        state = json.loads(state_path.read_text(encoding="utf-8"))
        payload_proc = subprocess.run(
            ["python3", str(payload_script)],
            check=True,
            text=True,
            capture_output=True,
            env=env,
        )
        payload = json.loads(payload_proc.stdout)

        pending_item = state.get("pending", [{}])[0]
        expected = "test-activity"

        for surface_name, obj in (
            ("artifact", artifact),
            ("queue", pending_item),
            ("payload", payload),
        ):
            if obj.get("activity_id") != expected:
                raise AssertionError(f"{surface_name} missing activity_id: {obj}")
            if obj.get("current_focus_activity_id") != expected:
                raise AssertionError(f"{surface_name} missing current_focus_activity_id: {obj}")

    print("EXECUTION_SYSTEM_CLOSEOUT_PAYLOAD_IDENTITY_PATH_SMOKE_OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
