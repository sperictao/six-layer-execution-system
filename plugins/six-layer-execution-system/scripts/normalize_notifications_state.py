#!/usr/bin/env python3
from __future__ import annotations

import json
from pathlib import Path

from execution_system_paths import WORKSPACE
STATE = WORKSPACE / "memory/notifications-state.json"


def infer_activity_id(item: dict) -> str | None:
    if item.get("activity_id"):
        return item["activity_id"]
    repo = item.get("repo")
    if repo and repo.startswith("notification-test"):
        return "notification-test"
    return None


def infer_activity_type(item: dict) -> str:
    if item.get("activity_type"):
        return item["activity_type"]
    if item.get("completed_slice_id") or item.get("commit"):
        return "roadmap"
    return "unknown"


def main() -> int:
    if not STATE.exists():
        data = {"version": 2, "pending": [], "inflight": [], "sent": []}
        STATE.write_text(json.dumps(data, ensure_ascii=True, indent=2) + "\n", encoding="utf-8")
        print("CREATED_V2")
        return 0

    data = json.loads(STATE.read_text(encoding="utf-8"))
    data["version"] = 2
    for bucket in ("pending", "inflight", "sent"):
        items = data.setdefault(bucket, [])
        for item in items:
            if not item.get("activity_id"):
                inferred = infer_activity_id(item)
                if inferred:
                    item["activity_id"] = inferred
            if not item.get("activity_type"):
                item["activity_type"] = infer_activity_type(item)
    STATE.write_text(json.dumps(data, ensure_ascii=True, indent=2) + "\n", encoding="utf-8")
    print("NORMALIZED_V2")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
