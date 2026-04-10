#!/usr/bin/env python3
from __future__ import annotations

import json

from execution_system_paths import WORKSPACE
CLOSEOUT = WORKSPACE / "memory/last-slice-closeout.json"


def get_notification_payload() -> dict | None:
    if not CLOSEOUT.exists():
        return None
    raw = CLOSEOUT.read_text(encoding="utf-8").strip()
    if not raw or raw == "{}":
        return None
    obj = json.loads(raw)
    return {
        "dedupe_key": obj.get("dedupe_key"),
        "activity_id": obj.get("activity_id"),
        "current_focus_activity_id": obj.get("current_focus_activity_id"),
        "activity_type": obj.get("activity_type"),
        "message": obj.get("message"),
    }


def main() -> int:
    payload = get_notification_payload()
    if payload is None:
        print("NO_SLICE_CLOSEOUT")
        return 0
    print(json.dumps(payload, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
