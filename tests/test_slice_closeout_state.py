#!/usr/bin/env python3
from __future__ import annotations

import json
import subprocess

from test_workspace_clone import cloned_workspace, workspace_env


def main() -> int:
    with cloned_workspace() as workspace:
        env = workspace_env(workspace)
        create = workspace / "scripts" / "create_slice_closeout.py"
        check = workspace / "scripts" / "check_slice_closeout.py"
        payload_script = workspace / "scripts" / "build_slice_handoff.py"
        closeout = workspace / "local-state" / "last-slice-closeout.json"
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
                "TEST.A1",
                "--next-slice-id",
                "TEST.A2",
                "--commit",
                "abc123",
                "--validation",
                "check passed",
            ],
            check=True,
            text=True,
            capture_output=True,
            env=env,
        )

        artifact = json.loads(closeout.read_text(encoding="utf-8"))
        if artifact.get("validation_state") != "validated":
            raise AssertionError(f"missing validated state: {artifact}")
        if artifact.get("slice_state") != "closed_out":
            raise AssertionError(f"missing closed_out state: {artifact}")
        if artifact.get("current_focus_activity_id") != "test-activity":
            raise AssertionError(f"missing current_focus_activity_id: {artifact}")

        payload_proc = subprocess.run(
            ["python3", str(payload_script)],
            text=True,
            capture_output=True,
            check=True,
            env=env,
        )
        payload = json.loads(payload_proc.stdout)
        if payload.get("current_focus_activity_id") != "test-activity":
            raise AssertionError(f"payload missing current_focus_activity_id: {payload}")

        proc = subprocess.run(["python3", str(check)], text=True, capture_output=True, check=False, env=env)
        output = proc.stdout + proc.stderr
        if "SLICE_CLOSEOUT_OK:test-activity:" not in output:
            raise AssertionError(output)

        bad_artifact = dict(artifact)
        bad_artifact["validation_state"] = "implemented"
        closeout.write_text(json.dumps(bad_artifact, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        proc = subprocess.run(["python3", str(check)], text=True, capture_output=True, check=False, env=env)
        output = proc.stdout + proc.stderr
        if "SLICE_CLOSEOUT_INVALID:validation_state:implemented" not in output:
            raise AssertionError(output)

        bad_artifact = dict(artifact)
        bad_artifact["slice_state"] = "validated"
        closeout.write_text(json.dumps(bad_artifact, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        proc = subprocess.run(["python3", str(check)], text=True, capture_output=True, check=False, env=env)
        output = proc.stdout + proc.stderr
        if "SLICE_CLOSEOUT_INVALID:slice_state:validated" not in output:
            raise AssertionError(output)

        bad_artifact = dict(artifact)
        bad_artifact.pop("current_focus_activity_id", None)
        closeout.write_text(json.dumps(bad_artifact, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        proc = subprocess.run(["python3", str(check)], text=True, capture_output=True, check=False, env=env)
        output = proc.stdout + proc.stderr
        if "SLICE_CLOSEOUT_MISSING:current_focus_activity_id" not in output:
            raise AssertionError(output)

        bad_artifact = dict(artifact)
        bad_artifact["current_focus_activity_id"] = "other-focus"
        closeout.write_text(json.dumps(bad_artifact, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        proc = subprocess.run(["python3", str(check)], text=True, capture_output=True, check=False, env=env)
        output = proc.stdout + proc.stderr
        if "SLICE_CLOSEOUT_INVALID:current_focus_activity_id_mismatch:test-activity:other-focus" not in output:
            raise AssertionError(output)

    print("SLICE_CLOSEOUT_STATE_SMOKE_OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
