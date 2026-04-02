#!/usr/bin/env python3
from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path

from execution_system_paths import WORKSPACE
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


def main() -> int:
    state = read_json(STATE)
    pending = state.get("pending", [])
    if not pending:
        print("NO_PENDING_NOTIFICATIONS")
        return 0

    item = pending.pop(0)
    item["flushed_at"] = now_iso()
    state.setdefault("inflight", []).append(item)
    state["pending"] = pending
    write_json(STATE, state)

    print(json.dumps(item, ensure_ascii=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
