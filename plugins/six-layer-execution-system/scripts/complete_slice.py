import json
import sys
from pathlib import Path

from active_ledger import parse_ledger
from execution_system_paths import STATE_ROOT, WORKSPACE
from run_execution_system_checks import collect_summary

from build_slice_handoff import build_handoff_payload
from create_slice_closeout import create_closeout

LAST_CLOSEOUT = STATE_ROOT / "last-slice-closeout.json"
ACTIVE = WORKSPACE / "ACTIVE.md"

def check_closeout_ready() -> bool:
    code, summary = collect_summary(print_output=False)
    if code != 0:
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
    
    if not check_closeout_ready():
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

    artifact = json.loads(LAST_CLOSEOUT.read_text(encoding="utf-8"))
    payload = build_handoff_payload(artifact)
    if payload is None:
        print("NO_SLICE_CLOSEOUT")
        sys.exit(1)
    print(json.dumps(payload, ensure_ascii=False))

def payload_slice():
    payload = build_handoff_payload()
    if payload is None:
        print("NO_SLICE_CLOSEOUT")
    else:
        print(json.dumps(payload, ensure_ascii=False))

def main():
    if len(sys.argv) < 2:
        print("usage: complete_slice.py prepare | payload", file=sys.stderr)
        sys.exit(2)
        
    mode = sys.argv[1]
    if mode == "prepare":
        prepare_slice()
    elif mode == "payload":
        payload_slice()
    else:
        print("usage: complete_slice.py prepare | payload", file=sys.stderr)
        sys.exit(2)

if __name__ == "__main__":
    main()
