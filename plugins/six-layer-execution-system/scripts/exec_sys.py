#!/usr/bin/env python3
import argparse
import subprocess
import sys
import re
from pathlib import Path

WORKSPACE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(WORKSPACE / "scripts"))

from active_ledger import parse_ledger

ACTIVE = WORKSPACE / "ACTIVE.md"

def update_active_slice_id(new_slice_id: str) -> bool:
    ledger = parse_ledger(ACTIVE)
    focus_id = ledger.current_focus_activity_id
    if not focus_id:
        print("No current focus activity found in ACTIVE.md", file=sys.stderr)
        return False
    
    text = ACTIVE.read_text(encoding="utf-8")
    
    # We need to find the block for the current focus activity and replace current_slice_id
    # A simple string split for the first occurrence after the activity heading
    heading_pattern = f"### Activity: {focus_id}"
    
    parts = text.split(heading_pattern)
    if len(parts) < 2:
        print(f"Could not find heading '{heading_pattern}' in ACTIVE.md", file=sys.stderr)
        return False
        
    after_heading = parts[1]
    
    # Update status to in_progress
    after_heading, _ = re.subn(
        r"(^- status: `)([^`]+)(`$)",
        r"\g<1>in_progress\g<3>",
        after_heading,
        count=1,
        flags=re.MULTILINE
    )

    # Replace current_slice_id in the block
    new_after, count = re.subn(
        r"(^- current_slice_id: `)([^`]+)(`$)",
        rf"\g<1>{new_slice_id}\g<3>",
        after_heading,
        count=1,
        flags=re.MULTILINE
    )
    
    if count == 0:
        # Insert current_slice_id if not present, e.g., after tasks_doc or status
        new_after, count = re.subn(
            r"(^- status: `in_progress`\n)",
            rf"\g<1>- current_slice_id: `{new_slice_id}`\n",
            after_heading,
            count=1,
            flags=re.MULTILINE
        )
        if count == 0:
            print("Could not find a place to insert current_slice_id", file=sys.stderr)
            return False
        
    new_text = parts[0] + heading_pattern + new_after
    ACTIVE.write_text(new_text, encoding="utf-8")
    print(f"Updated current_slice_id to {new_slice_id} for activity {focus_id}")
    return True

def cmd_slice_start(args):
    if update_active_slice_id(args.id):
        sys.exit(0)
    else:
        sys.exit(1)

def cmd_slice_complete(args):
    print("Running execution system checks and closeout generation...")
    # call complete_slice.sh prepare
    script = WORKSPACE / "scripts" / "complete_slice.sh"
    result = subprocess.run(["zsh", str(script), "prepare"], cwd=WORKSPACE)
    sys.exit(result.returncode)

def cmd_status(args):
    ledger = parse_ledger(ACTIVE)
    focus = ledger.get_current_focus_activity()
    if not focus:
        print("No current focus activity.")
        sys.exit(0)
        
    print(f"Current Focus Activity: {focus.activity_id}")
    print(f"Type: {focus.type}")
    print(f"Status: {focus.status}")
    print(f"Current Slice ID: {focus.current_slice_id}")
    
    blocked_by = focus.items("blocked_by")
    if blocked_by:
        print("Blocked By:")
        for b in blocked_by:
            print(f"  - {b}")
    sys.exit(0)

def main():
    parser = argparse.ArgumentParser(description="Unified CLI Tooling for Execution System")
    subparsers = parser.add_subparsers(dest="command", required=True)
    
    # slice commands
    slice_parser = subparsers.add_parser("slice", help="Slice commands")
    slice_subparsers = slice_parser.add_subparsers(dest="subcommand", required=True)
    
    start_parser = slice_subparsers.add_parser("start", help="Start a slice")
    start_parser.add_argument("id", help="Slice ID to start")
    
    complete_parser = slice_subparsers.add_parser("complete", help="Complete the current slice")
    
    # status command
    status_parser = subparsers.add_parser("status", help="Show current status")
    
    args = parser.parse_args()
    
    if args.command == "slice":
        if args.subcommand == "start":
            cmd_slice_start(args)
        elif args.subcommand == "complete":
            cmd_slice_complete(args)
    elif args.command == "status":
        cmd_status(args)

if __name__ == "__main__":
    main()
