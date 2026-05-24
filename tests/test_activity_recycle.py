#!/usr/bin/env python3
from __future__ import annotations

import shutil
import subprocess

from test_workspace_clone import cloned_workspace, workspace_env


def seed_activity(workspace, *, activity_id: str, activity_type: str, status: str, priority: str) -> None:
    activity_dir = workspace / "activities" / activity_id
    activity_dir.mkdir(parents=True, exist_ok=True)
    (activity_dir / "card.md").write_text(
        "\n".join(
            [
                f"### Activity: {activity_id}",
                f"- activity_id: `{activity_id}`",
                "- title: `synthetic recyclable activity`",
                f"- type: `{activity_type}`",
                "- owner: `test`",
                f"- status: `{status}`",
                f"- priority: `{priority}`",
                "- autopilot: `false`",
                "- focus_rank: `99`",
                "- path: `.`",
                "- repo: `six-layer-execution-system`",
                f"- roadmap_doc: `activities/{activity_id}/2-roadmap.md`",
                f"- tasks_dir: `activities/{activity_id}/3-tasks/`",
                "- waiting_on: `test`",
                "- unblock_condition: `test`",
                "- last_commit: `test123`",
                "- blocked_by:",
                "  - none",
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    (activity_dir / "2-roadmap.md").write_text("# Synthetic recyclable roadmap\n", encoding="utf-8")
    (activity_dir / "3-tasks").mkdir()


def seed_recycle_fixture(workspace) -> tuple[str, str]:
    done_id = "recyclable-test-activity"
    current_id = "current-test-activity"

    activities_root = workspace / "activities"
    if activities_root.exists():
        for child in activities_root.iterdir():
            if child.is_dir():
                shutil.rmtree(child)

    seed_activity(workspace, activity_id=done_id, activity_type="roadmap", status="done", priority="P2")
    seed_activity(workspace, activity_id=current_id, activity_type="waiting", status="blocked", priority="P3")

    active = workspace / "ACTIVE.md"
    active.write_text(
        "\n".join(
            [
                "# ACTIVE.md — Execution Ledger v3",
                "",
                "## Ledger meta",
                "- version: `3`",
                "- mode: `multi-activity`",
                f"- current_focus_activity_id: `{current_id}`",
                f"- default_reply_activity_id: `{current_id}`",
                "- selection_policy: `focus-first`",
                "- activity_root: `activities/`",
                "- updated_at: `2026-05-24 CST`",
                "",
                "## Activity index",
                "",
                "| activity_id | type | status | priority | path |",
                "|------------|------|--------|----------|------|",
                f"| {done_id} | roadmap | done | P2 | activities/{done_id}/ |",
                f"| {current_id} | waiting | blocked | P3 | activities/{current_id}/ |",
                "",
                f"## Focus: {current_id}",
                f"- card: `activities/{current_id}/card.md`",
                "- status: `blocked`",
                "",
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    return done_id, current_id


def run_cmd(workspace, *args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["python3", str(workspace / "scripts" / "exec_sys.py"), *args],
        cwd=workspace,
        env=workspace_env(workspace),
        text=True,
        capture_output=True,
        check=False,
    )


def expect(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def main() -> int:
    with cloned_workspace() as workspace:
        activity_id, current_id = seed_recycle_fixture(workspace)
        active = workspace / "ACTIVE.md"
        activity_dir = workspace / "activities" / activity_id
        recycled_dir = workspace / "recycle" / "activities" / activity_id
        current_dir = workspace / "activities" / current_id
        recycled_current_dir = workspace / "recycle" / "activities" / current_id
        history = workspace / "recycle" / "history.md"

        dry_run = run_cmd(workspace, "activity", "recycle", activity_id)
        dry_output = dry_run.stdout + dry_run.stderr
        expect(dry_run.returncode == 0, dry_output)
        expect("RECYCLE_CONFIRMATION_REQUIRED" in dry_output, dry_output)
        expect(activity_dir.exists(), "dry-run must not move the activity")
        expect(not recycled_dir.exists(), "dry-run must not create recycled activity content")
        expect(f"| {activity_id} |" in active.read_text(encoding="utf-8"), "dry-run must keep ACTIVE index")

        refused = run_cmd(workspace, "activity", "recycle", current_id, "--confirm")
        refused_output = refused.stdout + refused.stderr
        expect(refused.returncode == 1, refused_output)
        expect(f"RECYCLE_REFUSED_CURRENT_FOCUS:{current_id}" in refused_output, refused_output)

        forced = run_cmd(workspace, "activity", "recycle", current_id, "--confirm", "--force")
        forced_output = forced.stdout + forced.stderr
        expect(forced.returncode == 0, forced_output)
        expect("RECYCLE_ACTIVITY_OK" in forced_output, forced_output)
        expect(not current_dir.exists(), "forced recycle must remove current focus activity directory")
        expect((recycled_current_dir / "card.md").exists(), "forced recycle must move current focus activity")

        confirmed = run_cmd(workspace, "activity", "recycle", activity_id, "--confirm")
        confirmed_output = confirmed.stdout + confirmed.stderr
        expect(confirmed.returncode == 0, confirmed_output)
        expect("RECYCLE_ACTIVITY_OK" in confirmed_output, confirmed_output)
        expect(not activity_dir.exists(), "confirmed recycle must remove live activity directory")
        expect((recycled_dir / "card.md").exists(), "confirmed recycle must move card into recycle")
        expect(f"| {activity_id} |" not in active.read_text(encoding="utf-8"), "confirmed recycle must remove ACTIVE index row")

        history_text = history.read_text(encoding="utf-8")
        expect(f"| {activity_id} | roadmap | done | P2 |" in history_text, history_text)
        expect(f"| {current_id} | waiting | blocked | P3 |" in history_text, history_text)
        expect(f"activities/{activity_id}" in history_text, history_text)
        expect(f"recycle/activities/{activity_id}" in history_text, history_text)

        check = subprocess.run(
            ["python3", str(workspace / "scripts" / "check_active_consistency.py")],
            cwd=workspace,
            env=workspace_env(workspace),
            text=True,
            capture_output=True,
            check=False,
        )
        check_output = check.stdout + check.stderr
        expect(check.returncode == 0, check_output)
        expect("CONSISTENCY_CHECK_OK" in check_output, check_output)
        expect("- focus_activity_id: none" in check_output, check_output)

    print("ACTIVITY_RECYCLE_SMOKE_OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
