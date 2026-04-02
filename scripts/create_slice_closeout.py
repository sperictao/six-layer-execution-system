#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from datetime import datetime
from pathlib import Path

from execution_system_paths import WORKSPACE
CLOSEOUT = WORKSPACE / "memory/last-slice-closeout.json"


def now_iso() -> str:
    return datetime.now().astimezone().isoformat(timespec="seconds")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--activity-id", required=True)
    parser.add_argument("--current-focus-activity-id", required=True)
    parser.add_argument("--activity-type", required=True)
    parser.add_argument("--repo", required=True)
    parser.add_argument("--completed-slice-id", required=True)
    parser.add_argument("--next-slice-id", required=True)
    parser.add_argument("--commit", required=True)
    parser.add_argument("--validation", action="append", default=[])
    args = parser.parse_args()

    if args.activity_type == "roadmap" and args.current_focus_activity_id != args.activity_id:
        parser.error("--current-focus-activity-id must equal --activity-id for roadmap closeout")

    dedupe_key = f"{args.activity_id}:{args.completed_slice_id}:{args.commit}"
    validations = args.validation

    artifact = {
        "dedupe_key": dedupe_key,
        "activity_id": args.activity_id,
        "current_focus_activity_id": args.current_focus_activity_id,
        "activity_type": args.activity_type,
        "repo": args.repo,
        "completed_slice_id": args.completed_slice_id,
        "next_slice_id": args.next_slice_id,
        "validation_state": "validated",
        "slice_state": "closed_out",
        "commit": args.commit,
        "validations": validations,
        "message": "\n".join(
            [
                f"{args.repo} 切片完成",
                f"- 活动：{args.activity_id}",
                f"- 当前切片：{args.completed_slice_id}",
                f"- 验证：{' / '.join(validations) if validations else '已完成验证'}",
                f"- 下一切片：{args.next_slice_id}",
                f"- commit：{args.commit}",
            ]
        ),
        "created_at": now_iso(),
    }
    CLOSEOUT.write_text(json.dumps(artifact, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(artifact, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
