import json
import sys
from pathlib import Path

from active_ledger import parse_ledger
from execution_system_paths import WORKSPACE
from run_execution_system_checks import collect_summary

from create_slice_closeout import create_closeout
from queue_slice_notification import queue_notification
from flush_slice_notifications import flush_notification
from send_slice_notification_payload import get_notification_payload
from ack_slice_notification import ack_notification
from requeue_inflight_notifications import requeue_notifications

LAST_CLOSEOUT = WORKSPACE / "memory/last-slice-closeout.json"
LAST_NOTIFICATION = WORKSPACE / "memory/last-slice-notification.json"
ACTIVE = WORKSPACE / "ACTIVE.md"

def clear_notification_cache():
    LAST_NOTIFICATION.write_text("{}\n", encoding="utf-8")

def clear_closeout_cache():
    LAST_CLOSEOUT.write_text("{}\n", encoding="utf-8")

def check_closeout_ready(summary=None) -> bool:
    if summary is None:
        code, summary = collect_summary(print_output=False)
        if code != 0:
            print("CLOSEOUT_READY_FAILED")
            print("- reason: hard-fail suite did not pass")
            print(f"- first_failing_command: {summary.first_failing_command or 'none'}")
            return False
    else:
        if summary.hard_fail_status == "failed":
            print("CLOSEOUT_READY_FAILED")
            print("- reason: hard-fail suite did not pass")
            print(f"- first_failing_command: {summary.first_failing_command or 'none'}")
            return False

    ledger = parse_ledger(ACTIVE)
    focus = ledger.get_current_focus_activity()
    if focus is None:
        print("CLOSEOUT_READY_FAILED")
        print("- reason: no focus activity")
        return False

    if focus.scalar("type") != "roadmap":
        print("CLOSEOUT_READY_FAILED")
        print(f"- reason: focus activity is not roadmap ({focus.scalar('type') or 'missing'})")
        return False

    current_slice_id = focus.scalar("current_slice_id")
    next_slice_id = focus.scalar("next_slice_id")
    last_commit = focus.scalar("last_commit")
    last_validation = focus.items("last_validation")

    if not current_slice_id:
        print("CLOSEOUT_READY_FAILED")
        print("- reason: missing current_slice_id")
        return False
    if not next_slice_id:
        print("CLOSEOUT_READY_FAILED")
        print("- reason: missing next_slice_id")
        return False
    if not last_commit:
        print("CLOSEOUT_READY_FAILED")
        print("- reason: missing last_commit")
        return False
    if not last_validation:
        print("CLOSEOUT_READY_FAILED")
        print("- reason: missing last_validation entries")
        return False

    print("CLOSEOUT_READY_OK")
    print(f"- focus_activity_id: {focus.activity_id}")
    print(f"- current_slice_id: {current_slice_id}")
    print(f"- next_slice_id: {next_slice_id}")
    print(f"- last_commit: {last_commit}")
    print(f"- advisory_hits: {len(summary.advisory_commands)}")
    return True

def prepare_slice():
    code, summary = collect_summary(print_output=True)
    if code != 0:
        sys.exit(code)
    
    if not check_closeout_ready(summary):
        sys.exit(1)

    ledger = parse_ledger(ACTIVE)
    focus = ledger.get_current_focus_activity()
    if focus is None:
        sys.exit(1)

    activity_id = focus.activity_id
    current_focus_activity_id = activity_id
    activity_type = focus.scalar("type")

    if activity_type != "roadmap":
        print(f"FOCUS_ACTIVITY_NOT_ROADMAP:{activity_id}:{activity_type}", file=sys.stderr)
        sys.exit(1)

    repo = focus.scalar("repo")
    if not repo:
        repo_path = focus.scalar("path")
        if not repo_path or repo_path == "." or repo_path == "<plugin-root>":
            repo = WORKSPACE.name
        else:
            repo = Path(repo_path).name

    completed_slice_id = focus.scalar("current_slice_id")
    next_slice_id = focus.scalar("next_slice_id")
    commit = focus.scalar("last_commit")
    validations = focus.items("last_validation")

    create_closeout(
        activity_id=activity_id,
        current_focus_activity_id=current_focus_activity_id,
        activity_type=activity_type,
        repo=repo,
        completed_slice_id=completed_slice_id,
        next_slice_id=next_slice_id,
        commit=commit,
        validations=validations
    )

    try:
        queue_notification()
    except ValueError:
        pass

    flushed = flush_notification()
    if flushed is None:
        clear_notification_cache()
        print("NO_PENDING_NOTIFICATIONS")
        sys.exit(0)

    flushed_json = json.dumps(flushed, ensure_ascii=True)
    LAST_NOTIFICATION.write_text(flushed_json + "\n", encoding="utf-8")
    print(flushed_json)

def payload_slice():
    payload = get_notification_payload()
    if payload is None:
        print("NO_SLICE_CLOSEOUT")
    else:
        print(json.dumps(payload, ensure_ascii=False))

def ack_slice(dedupe_key: str):
    if not ack_notification(dedupe_key):
        print("NOT_FOUND")
        sys.exit(1)
    
    clear_notification_cache()
    clear_closeout_cache()
    print(dedupe_key)

def fail_slice():
    requeue_notifications()
    clear_notification_cache()

def main():
    if len(sys.argv) < 2:
        print("usage: complete_slice.py prepare | payload | ack <dedupe_key> | fail", file=sys.stderr)
        sys.exit(2)
        
    mode = sys.argv[1]
    if mode == "prepare":
        prepare_slice()
    elif mode == "payload":
        payload_slice()
    elif mode == "ack":
        if len(sys.argv) != 3:
            print("usage: complete_slice.py ack <dedupe_key>", file=sys.stderr)
            sys.exit(2)
        ack_slice(sys.argv[2])
    elif mode == "fail":
        fail_slice()
    else:
        print("usage: complete_slice.py prepare | payload | ack <dedupe_key> | fail", file=sys.stderr)
        sys.exit(2)

if __name__ == "__main__":
    main()
