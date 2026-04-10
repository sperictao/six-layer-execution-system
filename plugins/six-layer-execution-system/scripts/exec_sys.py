#!/usr/bin/env python3
import argparse
import subprocess
import sys
from pathlib import Path

WORKSPACE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(WORKSPACE / "scripts"))

from active_ledger import parse_ledger

ACTIVE = WORKSPACE / "ACTIVE.md"

def update_active_slice_id(new_slice_id: str) -> bool:
    ledger = parse_ledger(ACTIVE)
    focus = ledger.get_current_focus_activity()
    if not focus:
        print("No current focus activity found in ACTIVE.md", file=sys.stderr)
        return False
    
    focus.update_fields(status="in_progress", current_slice_id=new_slice_id)
    try:
        ledger.save()
        print(f"Updated current_slice_id to {new_slice_id} for activity {focus.activity_id}")
        return True
    except Exception as e:
        print(f"Failed to update ACTIVE.md: {e}", file=sys.stderr)
        return False

def cmd_slice_start(args):
    if update_active_slice_id(args.id):
        sys.exit(0)
    else:
        sys.exit(1)

def cmd_slice_complete(args):
    print("Running execution system checks and closeout generation...")
    import complete_slice
    try:
        complete_slice.prepare_slice()
    except SystemExit as e:
        sys.exit(e.code)
    sys.exit(0)

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
