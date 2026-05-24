#!/usr/bin/env python3
from __future__ import annotations

import json

from execution_system_paths import STATE_ROOT
CLOSEOUT = STATE_ROOT / "last-slice-closeout.json"


def main() -> int:
    raw = CLOSEOUT.read_text(encoding="utf-8").strip() if CLOSEOUT.exists() else "{}"
    if not raw or raw == "{}":
        print("SLICE_CLOSEOUT_MISSING:artifact")
        return 1
    artifact = json.loads(raw)
    dedupe_key = artifact.get("dedupe_key", "")
    activity_id = artifact.get("activity_id", "")
    current_focus_activity_id = artifact.get("current_focus_activity_id", "")
    activity_type = artifact.get("activity_type", "")
    validation_state = artifact.get("validation_state", "")
    slice_state = artifact.get("slice_state", "")
    if not dedupe_key:
        print("SLICE_CLOSEOUT_MISSING:dedupe_key")
        return 1
    if not activity_id:
        print("SLICE_CLOSEOUT_MISSING:activity_id")
        return 1
    if not current_focus_activity_id:
        print("SLICE_CLOSEOUT_MISSING:current_focus_activity_id")
        return 1
    if activity_type == "roadmap" and current_focus_activity_id != activity_id:
        print(
            "SLICE_CLOSEOUT_INVALID:current_focus_activity_id_mismatch:"
            f"{activity_id}:{current_focus_activity_id}"
        )
        return 1
    if validation_state != "validated":
        print(f"SLICE_CLOSEOUT_INVALID:validation_state:{validation_state or 'missing'}")
        return 1
    if slice_state != "closed_out":
        print(f"SLICE_CLOSEOUT_INVALID:slice_state:{slice_state or 'missing'}")
        return 1
    print(f"SLICE_CLOSEOUT_OK:{activity_id}:{dedupe_key}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
