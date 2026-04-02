#!/usr/bin/env python3
from __future__ import annotations

import json
from pathlib import Path

from execution_system_paths import WORKSPACE
CLOSEOUT = WORKSPACE / "memory/last-slice-closeout.json"


def main() -> int:
    if not CLOSEOUT.exists():
        print("NO_SLICE_CLOSEOUT")
        return 0
    raw = CLOSEOUT.read_text(encoding="utf-8").strip()
    if not raw or raw == "{}":
        print("NO_SLICE_CLOSEOUT")
        return 0
    obj = json.loads(raw)
    print(
        json.dumps(
            {
                "dedupe_key": obj.get("dedupe_key"),
                "activity_id": obj.get("activity_id"),
                "current_focus_activity_id": obj.get("current_focus_activity_id"),
                "activity_type": obj.get("activity_type"),
                "message": obj.get("message"),
            },
            ensure_ascii=False,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
