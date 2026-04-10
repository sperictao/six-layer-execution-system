#!/usr/bin/env python3
from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path

from execution_system_paths import WORKSPACE
CLOSEOUT = WORKSPACE / "memory/last-slice-closeout.json"
STATE = WORKSPACE / "memory/notifications-state.json"


def now_iso() -> str:
    return datetime.now().astimezone().isoformat(timespec="seconds")


def read_json(path: Path) -> dict:
    if not path.exists():
        return {"version": 2, "pending": [], "inflight": [], "sent": []}
    data = json.loads(path.read_text(encoding="utf-8"))
    data.setdefault("version", 2)
    data.setdefault("pending", [])
    data.setdefault("inflight", [])
    data.setdefault("sent", [])
    return data


def write_json(path: Path, data: dict) -> None:
    path.write_text(json.dumps(data, ensure_ascii=True, indent=2) + "\n", encoding="utf-8")


def queue_notification() -> str:
    raw = CLOSEOUT.read_text(encoding="utf-8").strip() if CLOSEOUT.exists() else "{}"
    if not raw or raw == "{}":
        raise ValueError("NO_SLICE_CLOSEOUT")
    artifact = json.loads(raw)
    dedupe_key = artifact.get("dedupe_key", "")
    if not dedupe_key:
        raise ValueError("INVALID_SLICE_CLOSEOUT")

    state = read_json(STATE)
    for bucket in ("pending", "inflight", "sent"):
        for item in state.get(bucket, []):
            if item.get("dedupe_key") == dedupe_key:
                return dedupe_key

    item = {
        "dedupe_key": dedupe_key,
        "activity_id": artifact.get("activity_id"),
        "current_focus_activity_id": artifact.get("current_focus_activity_id"),
        "activity_type": artifact.get("activity_type"),
        "repo": artifact.get("repo"),
        "completed_slice_id": artifact.get("completed_slice_id"),
        "next_slice_id": artifact.get("next_slice_id"),
        "commit": artifact.get("commit"),
        "validations": artifact.get("validations", []),
        "message": artifact.get("message", ""),
        "queued_at": now_iso(),
    }
    state.setdefault("pending", []).append(item)
    write_json(STATE, state)
    return dedupe_key


def main() -> int:
    try:
        dedupe_key = queue_notification()
        print(dedupe_key)
        return 0
    except ValueError as e:
        print(str(e))
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
