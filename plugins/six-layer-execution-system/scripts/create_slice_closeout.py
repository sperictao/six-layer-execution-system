#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from datetime import datetime

from execution_system_paths import STATE_ROOT
CLOSEOUT = STATE_ROOT / "last-slice-closeout.json"


def now_iso() -> str:
    return datetime.now().astimezone().isoformat(timespec="seconds")


def create_closeout(
    activity_id: str,
    current_focus_activity_id: str,
    activity_type: str,
    repo: str,
    completed_slice_id: str,
    next_slice_id: str,
    commit: str,
    validations: list[str],
) -> dict:
    if activity_type == "roadmap" and current_focus_activity_id != activity_id:
        raise ValueError("--current-focus-activity-id must equal --activity-id for roadmap closeout")

    dedupe_key = f"{activity_id}:{completed_slice_id}:{commit}"

    artifact = {
        "dedupe_key": dedupe_key,
        "activity_id": activity_id,
        "current_focus_activity_id": current_focus_activity_id,
        "activity_type": activity_type,
        "repo": repo,
        "completed_slice_id": completed_slice_id,
        "next_slice_id": next_slice_id,
        "validation_state": "validated",
        "slice_state": "closed_out",
        "commit": commit,
        "validations": validations,
        "message": "\n".join(
            [
                f"{repo} 切片完成",
                f"- 活动：{activity_id}",
                f"- 当前切片：{completed_slice_id}",
                f"- 验证：{' / '.join(validations) if validations else '已完成验证'}",
                f"- 下一切片：{next_slice_id}",
                f"- commit：{commit}",
            ]
        ),
        "created_at": now_iso(),
    }
    CLOSEOUT.parent.mkdir(parents=True, exist_ok=True)
    CLOSEOUT.write_text(json.dumps(artifact, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return artifact

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

    try:
        artifact = create_closeout(
            activity_id=args.activity_id,
            current_focus_activity_id=args.current_focus_activity_id,
            activity_type=args.activity_type,
            repo=args.repo,
            completed_slice_id=args.completed_slice_id,
            next_slice_id=args.next_slice_id,
            commit=args.commit,
            validations=args.validation,
        )
        print(json.dumps(artifact, ensure_ascii=False))
        return 0
    except ValueError as e:
        parser.error(str(e))



if __name__ == "__main__":
    raise SystemExit(main())
