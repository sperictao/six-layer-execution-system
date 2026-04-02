#!/usr/bin/env python3
from __future__ import annotations

import json
from pathlib import Path

from execution_system_paths import WORKSPACE
STATE = WORKSPACE / "memory/notifications-state.json"


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
    inflight = state.get("inflight", [])
    if not inflight:
        print("NO_INFLIGHT_NOTIFICATIONS")
        return 0

    pending = state.get("pending", [])
    existing = {item.get("dedupe_key") for item in pending}
    moved = 0
    for item in inflight:
        if item.get("dedupe_key") not in existing:
            item.pop("flushed_at", None)
            pending.append(item)
            moved += 1
    state["pending"] = pending
    state["inflight"] = []
    write_json(STATE, state)
    print(f"REQUEUED:{moved}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
