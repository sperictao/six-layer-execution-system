#!/usr/bin/env python3
from __future__ import annotations

import json

from execution_system_paths import WORKSPACE

CLOSEOUT = WORKSPACE / "memory/last-slice-closeout.json"


def read_closeout() -> dict | None:
    if not CLOSEOUT.exists():
        return None
    raw = CLOSEOUT.read_text(encoding="utf-8").strip()
    if not raw or raw == "{}":
        return None
    return json.loads(raw)


def build_handoff_payload(closeout: dict | None = None) -> dict | None:
    artifact = closeout if closeout is not None else read_closeout()
    if artifact is None:
        return None
    return {
        "dedupe_key": artifact.get("dedupe_key"),
        "activity_id": artifact.get("activity_id"),
        "current_focus_activity_id": artifact.get("current_focus_activity_id"),
        "activity_type": artifact.get("activity_type"),
        "repo": artifact.get("repo"),
        "completed_slice_id": artifact.get("completed_slice_id"),
        "next_slice_id": artifact.get("next_slice_id"),
        "commit": artifact.get("commit"),
        "validations": artifact.get("validations", []),
        "message": artifact.get("message"),
    }


def main() -> int:
    payload = build_handoff_payload()
    if payload is None:
        print("NO_SLICE_CLOSEOUT")
        return 0
    print(json.dumps(payload, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
