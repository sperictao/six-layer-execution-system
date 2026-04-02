#!/usr/bin/env python3
from __future__ import annotations

import json
import os
import sys
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
    if os.environ.get("COMPLETE_SLICE_ACK") != "1":
        print("DIRECT_ACK_FORBIDDEN: use complete_slice.sh ack <dedupe_key>", file=sys.stderr)
        return 3

    if len(sys.argv) != 2:
        print("usage: ack_slice_notification.py <dedupe_key>", file=sys.stderr)
        return 2

    dedupe_key = sys.argv[1]
    state = read_json(STATE)
    inflight = state.get("inflight", [])
    sent = state.get("sent", [])

    remaining = []
    matched = None
    for item in inflight:
        if item.get("dedupe_key") == dedupe_key and matched is None:
            matched = item
        else:
            remaining.append(item)

    if matched is None:
        print("NOT_FOUND")
        return 1

    matched["sent_at"] = now_iso()
    sent.append(matched)
    state["inflight"] = remaining
    state["sent"] = sent
    write_json(STATE, state)
    print(dedupe_key)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
