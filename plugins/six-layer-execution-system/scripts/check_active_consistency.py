#!/usr/bin/env python3
from __future__ import annotations

import subprocess
import sys
from pathlib import Path

from execution_system_paths import WORKSPACE, resolve_workspace_path
ACTIVE_PATH = WORKSPACE / "ACTIVE.md"
sys.path.insert(0, str(WORKSPACE / "scripts"))

from active_ledger import Activity, parse_ledger  # noqa: E402


def git_head(repo_path: str) -> str | None:
    try:
        out = subprocess.check_output(
            ["git", "-C", repo_path, "rev-parse", "--short", "HEAD"],
            text=True,
            stderr=subprocess.STDOUT,
        )
    except (subprocess.CalledProcessError, FileNotFoundError):
        return None
    return out.strip()


def git_has_commit(repo_path: str, commit: str) -> bool:
    try:
        subprocess.check_output(
            ["git", "-C", repo_path, "rev-parse", "--verify", f"{commit}^{{commit}}"],
            text=True,
            stderr=subprocess.STDOUT,
        )
    except (subprocess.CalledProcessError, FileNotFoundError):
        return False
    return True


def git_repo_available(repo_path: str) -> bool:
    try:
        out = subprocess.check_output(
            ["git", "-C", repo_path, "rev-parse", "--is-inside-work-tree"],
            text=True,
            stderr=subprocess.STDOUT,
        )
    except (subprocess.CalledProcessError, FileNotFoundError):
        return False
    return out.strip() == "true"


def add_problem(problems: list[str], scope: str, message: str) -> None:
    problems.append(f"{scope}: {message}")


def require_scalar(problems: list[str], scope: str, activity: Activity, field: str) -> None:
    if field not in activity.fields or not activity.scalar(field):
        add_problem(problems, scope, f"missing `{field}`")


def require_list(problems: list[str], scope: str, activity: Activity, field: str) -> None:
    if field in activity.list_fields and activity.items(field):
        return
    scalar = activity.scalar(field)
    if scalar:
        return
    add_problem(problems, scope, f"missing list `{field}`")


def git_changed_files(repo_path: str) -> list[str]:
    try:
        out = subprocess.check_output(
            ["git", "-C", repo_path, "status", "--short", "--untracked-files=no"],
            text=True,
            stderr=subprocess.STDOUT,
        )
    except (subprocess.CalledProcessError, FileNotFoundError):
        return []

    changed: list[str] = []
    for line in out.splitlines():
        if not line.strip():
            continue
        changed.append(line[3:])
    return changed


def is_active_self_drift(repo_path: str, changed_files: list[str]) -> bool:
    if Path(repo_path).resolve() != WORKSPACE.resolve():
        return False
    normalized = {Path(path).as_posix() for path in changed_files}
    return normalized == {ACTIVE_PATH.relative_to(WORKSPACE).as_posix()}


def validate_ledger_level(problems: list[str], ledger) -> None:
    required_meta = (
        "version",
        "mode",
        "current_focus_activity_id",
        "default_reply_activity_id",
        "selection_policy",
        "updated_at",
    )
    for key in required_meta:
        if key not in ledger.meta:
            add_problem(problems, "ledger", f"missing `{key}` in Ledger meta")

    if ledger.meta.get("mode") != "multi-activity":
        add_problem(problems, "ledger", "mode must be `multi-activity`")

    if ledger.meta.get("selection_policy") not in {"focus-first", "focus-then-fallback"}:
        add_problem(problems, "ledger", "selection_policy must be `focus-first` or `focus-then-fallback`")

    if not ledger.activity_index:
        add_problem(problems, "ledger", "Activity index is empty")

    if len(set(ledger.activity_index)) != len(ledger.activity_index):
        add_problem(problems, "ledger", "Activity index contains duplicate activity ids")

    for activity_id in ledger.activity_index:
        if activity_id not in ledger.activities:
            add_problem(problems, "ledger", f"Activity index references missing activity `{activity_id}`")

    focus_id = ledger.current_focus_activity_id
    if not focus_id:
        add_problem(problems, "ledger", "missing current focus activity")
    elif focus_id not in ledger.activities:
        add_problem(problems, "ledger", f"current focus activity `{focus_id}` does not exist")

    reply_id = ledger.meta.get("default_reply_activity_id")
    if reply_id and reply_id not in ledger.activities:
        add_problem(problems, "ledger", f"default reply activity `{reply_id}` does not exist")


def validate_common_activity_fields(problems: list[str], activity: Activity) -> None:
    activity_id = activity.activity_id or activity.heading
    required = ("activity_id", "title", "type", "status", "priority", "autopilot")
    for field in required:
        if field not in activity.fields:
            add_problem(problems, f"activity:{activity_id}", f"missing `{field}`")

    if activity.scalar("status") not in {"ready", "in_progress", "blocked", "done", "parked"}:
        add_problem(problems, f"activity:{activity_id}", "status must be one of ready/in_progress/blocked/done/parked")

    if activity.scalar("autopilot") not in {"true", "false"}:
        add_problem(problems, f"activity:{activity_id}", "autopilot must be `true` or `false`")


def validate_roadmap_activity(problems: list[str], activity: Activity) -> None:
    activity_id = activity.activity_id or activity.heading

    if not activity.scalar("path") and not activity.scalar("repo"):
        add_problem(problems, f"activity:{activity_id}", "roadmap activity must include `path` or `repo`")

    doc_fields = ("roadmap_doc", "tasks_doc", "tasks_dir")
    for field in doc_fields:
        if field in activity.fields and not activity.scalar(field):
            add_problem(problems, f"activity:{activity_id}", f"roadmap activity has empty `{field}`")

    list_fields = ("next_step", "validation", "blocked_by")
    for field in list_fields:
        if field in activity.fields and not activity.items(field):
            add_problem(problems, f"activity:{activity_id}", f"roadmap activity has empty list `{field}`")


def validate_waiting_activity(problems: list[str], activity: Activity) -> None:
    activity_id = activity.activity_id or activity.heading
    scope = f"activity:{activity_id}"
    for field in ("waiting_on", "unblock_condition"):
        require_scalar(problems, scope, activity, field)
    if activity.scalar("autopilot") != "false":
        add_problem(problems, scope, "waiting activity autopilot must be `false`")


def validate_simple_activity(problems: list[str], activity: Activity) -> None:
    activity_id = activity.activity_id or activity.heading
    scope = f"activity:{activity_id}"
    for field in ("goal", "done_definition"):
        require_scalar(problems, scope, activity, field)
    for field in ("next_step", "validation"):
        require_list(problems, scope, activity, field)


def validate_activity_level(problems: list[str], ledger) -> None:
    for activity in ledger.list_activities():
        activity_id = activity.activity_id or activity.heading
        validate_common_activity_fields(problems, activity)

        activity_type = activity.scalar("type")
        if activity_type == "roadmap":
            validate_roadmap_activity(problems, activity)
        elif activity_type == "waiting":
            validate_waiting_activity(problems, activity)
        elif activity_type == "simple":
            validate_simple_activity(problems, activity)
        elif activity_type:
            add_problem(problems, f"activity:{activity_id}", f"unsupported activity type `{activity_type}`")

        if activity.scalar("focus_rank") is None:
            add_problem(problems, f"activity:{activity_id}", "missing `focus_rank`")


def validate_focus_level(problems: list[str], ledger) -> None:
    focus = ledger.get_current_focus_activity()
    focus_id = ledger.current_focus_activity_id
    if focus is None or focus_id is None:
        return

    if focus.scalar("type") == "roadmap":
        repo_path = focus.repo_path
        resolved_repo_path = resolve_workspace_path(repo_path)
        last_commit = focus.last_commit
        current_slice_id = focus.current_slice_id
        next_slice_id = focus.next_slice_id
        status = focus.status

        scope = f"focus:{focus_id}"
        required_scalars = (
            "source_doc",
            "roadmap_doc",
            "current_slice_id",
            "next_slice_id",
            "last_commit",
        )
        for field in required_scalars:
            require_scalar(problems, scope, focus, field)
        if not (
            focus.scalar("tasks_doc")
            or focus.scalar("tasks_dir")
            or focus.scalar("current_tasks_file")
        ):
            add_problem(problems, scope, "missing `tasks_doc` or `tasks_dir`")

        for field in ("next_step", "validation", "blocked_by"):
            require_list(problems, scope, focus, field)

        doc_fields = ("source_doc", "roadmap_doc", "tasks_doc", "tasks_dir", "current_tasks_file")
        for field in doc_fields:
            if field in focus.fields:
                doc_path = focus.scalar(field)
                resolved_doc_path = resolve_workspace_path(doc_path)
                if doc_path and (resolved_doc_path is None or not resolved_doc_path.exists()):
                    add_problem(problems, scope, f"`{field}` points to missing file `{doc_path}`")

        if not repo_path:
            add_problem(problems, scope, "missing `path`")
        if not status:
            add_problem(problems, scope, "missing `status`")

        if current_slice_id and next_slice_id and current_slice_id == next_slice_id:
            add_problem(problems, scope, "current_slice_id and next_slice_id must differ")

        if repo_path and resolved_repo_path is None:
            add_problem(problems, scope, f"`path` is not resolvable: `{repo_path}`")

        if resolved_repo_path and last_commit:
            repo_path_text = str(resolved_repo_path)
            if not git_repo_available(repo_path_text):
                return
            if not git_has_commit(repo_path_text, last_commit):
                add_problem(problems, scope, f"last_commit `{last_commit}` does not exist in repo")
            head = git_head(repo_path_text)
            if head and head != last_commit:
                changed_files = git_changed_files(repo_path_text)
                if is_active_self_drift(repo_path_text, changed_files):
                    add_problem(
                        problems,
                        scope,
                        "repo HEAD `{}` does not match last_commit `{}`; likely self-drift from updating `ACTIVE.md`. Update `ACTIVE.md:last_commit` if this commit is now the intended truth, then rerun the checker".format(
                            head, last_commit
                        ),
                    )
                else:
                    add_problem(problems, scope, f"repo HEAD `{head}` does not match last_commit `{last_commit}`")
            head = git_head(repo_path_text)
            if head and head != last_commit:
                changed_files = git_changed_files(repo_path_text)
                if is_active_self_drift(repo_path_text, changed_files):
                    add_problem(
                        problems,
                        f"focus:{focus_id}",
                        "repo HEAD `{}` does not match last_commit `{}`; likely self-drift from updating `ACTIVE.md`. Update `ACTIVE.md:last_commit` if this commit is now the intended truth, then rerun the checker".format(
                            head, last_commit
                        ),
                    )
                else:
                    add_problem(problems, f"focus:{focus_id}", f"repo HEAD `{head}` does not match last_commit `{last_commit}`")


def main() -> int:
    problems: list[str] = []
    ledger_path = Path(sys.argv[1]) if len(sys.argv) > 1 else ACTIVE_PATH
    ledger = parse_ledger(ledger_path)

    validate_ledger_level(problems, ledger)
    validate_activity_level(problems, ledger)
    validate_focus_level(problems, ledger)

    if problems:
        print("CONSISTENCY_CHECK_FAILED")
        for problem in problems:
            print(f"- {problem}")
        return 1

    focus = ledger.get_current_focus_activity()
    print("CONSISTENCY_CHECK_OK")
    print(f"- focus_activity_id: {ledger.current_focus_activity_id}")
    print(f"- activity_count: {len(ledger.activities)}")
    print(f"- runnable_activity_count: {len(ledger.list_runnable_activities())}")
    if focus is not None:
        print(f"- focus_type: {focus.type}")
        print(f"- focus_status: {focus.status}")
        if focus.current_slice_id:
            print(f"- current_slice_id: {focus.current_slice_id}")
        if focus.next_slice_id:
            print(f"- next_slice_id: {focus.next_slice_id}")
        if focus.last_commit:
            print(f"- last_commit: {focus.last_commit}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
