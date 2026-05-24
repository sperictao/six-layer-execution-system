#!/usr/bin/env python3
from __future__ import annotations

import argparse
import shutil
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

from active_ledger import Activity, parse_ledger
from execution_system_paths import WORKSPACE

ACTIVE = WORKSPACE / "ACTIVE.md"
RECYCLE_ROOT = WORKSPACE / "recycle"
RECYCLED_ACTIVITIES = RECYCLE_ROOT / "activities"
HISTORY = RECYCLE_ROOT / "history.md"


@dataclass(frozen=True)
class RecyclePlan:
    activity_id: str
    activity_type: str
    status: str
    priority: str
    original_path: Path
    recycled_path: Path
    last_commit: str


def now_iso() -> str:
    return datetime.now().astimezone().isoformat(timespec="seconds")


def md_cell(value: str) -> str:
    return value.replace("|", "\\|").replace("\n", " ").strip()


def workspace_relative(path: Path) -> str:
    try:
        return path.resolve().relative_to(WORKSPACE.resolve()).as_posix()
    except ValueError:
        return str(path)


def activity_dir(activity: Activity) -> Path:
    if activity._card_path is None:
        return WORKSPACE / "activities" / (activity.activity_id or "")
    return activity._card_path.parent


def build_plan(activity_id: str, *, force: bool = False) -> RecyclePlan:
    ledger = parse_ledger(ACTIVE)
    activity = ledger.get_activity(activity_id)
    if activity is None:
        raise ValueError(f"UNKNOWN_ACTIVITY:{activity_id}")

    if not force and ledger.current_focus_activity_id == activity_id:
        raise ValueError(f"RECYCLE_REFUSED_CURRENT_FOCUS:{activity_id}")
    if not force and ledger.meta.get("default_reply_activity_id") == activity_id:
        raise ValueError(f"RECYCLE_REFUSED_DEFAULT_REPLY:{activity_id}")
    if not force and activity.scalar("status") != "done":
        raise ValueError(f"RECYCLE_REFUSED_NOT_DONE:{activity_id}:{activity.scalar('status') or 'missing'}")

    original = activity_dir(activity)
    if not original.is_dir():
        raise ValueError(f"RECYCLE_REFUSED_MISSING_ACTIVITY_DIR:{workspace_relative(original)}")

    recycled = RECYCLED_ACTIVITIES / activity_id
    if recycled.exists():
        raise ValueError(f"RECYCLE_REFUSED_ALREADY_RECYCLED:{workspace_relative(recycled)}")

    return RecyclePlan(
        activity_id=activity_id,
        activity_type=activity.scalar("type") or "",
        status=activity.scalar("status") or "",
        priority=activity.scalar("priority") or "",
        original_path=original,
        recycled_path=recycled,
        last_commit=activity.scalar("last_commit") or "none",
    )


def ensure_history() -> None:
    if HISTORY.exists():
        return
    HISTORY.parent.mkdir(parents=True, exist_ok=True)
    HISTORY.write_text(
        "\n".join(
            [
                "# Recycled activities",
                "",
                "| recycled_at | activity_id | type | status | priority | original_path | recycled_path | last_commit |",
                "|---|---|---|---|---|---|---|---|",
            ]
        )
        + "\n",
        encoding="utf-8",
    )


def append_history(plan: RecyclePlan) -> None:
    ensure_history()
    row = " | ".join(
        [
            md_cell(now_iso()),
            md_cell(plan.activity_id),
            md_cell(plan.activity_type),
            md_cell(plan.status),
            md_cell(plan.priority),
            md_cell(workspace_relative(plan.original_path)),
            md_cell(workspace_relative(plan.recycled_path)),
            md_cell(plan.last_commit),
        ]
    )
    with HISTORY.open("a", encoding="utf-8") as fh:
        fh.write(f"| {row} |\n")


def print_plan(plan: RecyclePlan, *, confirmed: bool) -> None:
    print("RECYCLE_ACTIVITY_PLAN" if not confirmed else "RECYCLE_ACTIVITY_OK")
    print(f"- activity_id: {plan.activity_id}")
    print(f"- type: {plan.activity_type}")
    print(f"- status: {plan.status}")
    print(f"- original_path: {workspace_relative(plan.original_path)}")
    print(f"- recycled_path: {workspace_relative(plan.recycled_path)}")


def recycle_activity(activity_id: str, *, confirm: bool, force: bool = False) -> int:
    try:
        plan = build_plan(activity_id, force=force)
    except ValueError as error:
        print("RECYCLE_ACTIVITY_REFUSED")
        print(f"- reason: {error}")
        return 1

    if not confirm:
        print_plan(plan, confirmed=False)
        print("RECYCLE_CONFIRMATION_REQUIRED")
        force_flag = " --force" if force else ""
        print(f"- confirm_command: python3 scripts/recycle_activity.py {activity_id} --confirm{force_flag}")
        return 0

    ledger = parse_ledger(ACTIVE)
    if force and (
        ledger.current_focus_activity_id == activity_id
        or ledger.meta.get("default_reply_activity_id") == activity_id
    ):
        ledger.update_fields(
            current_focus_activity_id="none",
            default_reply_activity_id="none",
        )
    ledger.remove_activity(activity_id)
    ledger.save()

    plan.recycled_path.parent.mkdir(parents=True, exist_ok=True)
    shutil.move(str(plan.original_path), str(plan.recycled_path))
    append_history(plan)
    print_plan(plan, confirmed=True)
    return 0


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("activity_id")
    parser.add_argument("--confirm", action="store_true")
    parser.add_argument("--force", action="store_true")
    args = parser.parse_args()
    return recycle_activity(args.activity_id, confirm=args.confirm, force=args.force)


if __name__ == "__main__":
    raise SystemExit(main())
