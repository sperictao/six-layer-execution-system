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


def main() -> int:
    state = read_json(STATE)
    inflight = state.get("inflight", [])
    if not inflight:
        print("NO_INFLIGHT_NOTIFICATIONS")
        return 0
    print(json.dumps(inflight[0], ensure_ascii=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
