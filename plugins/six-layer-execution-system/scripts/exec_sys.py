#!/usr/bin/env python3
from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path

from execution_system_paths import WORKSPACE

sys.path.insert(0, str(WORKSPACE / "scripts"))

from active_ledger import parse_ledger
from decomposition_engine import decompose_request

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
    except Exception as error:
        print(f"Failed to update ACTIVE.md: {error}", file=sys.stderr)
        return False


def cmd_slice_start(args):
    if update_active_slice_id(args.id):
        sys.exit(0)
    sys.exit(1)


def cmd_slice_complete(args):
    if getattr(args, "agile", False):
        os.environ["SIX_LAYER_EXECUTION_MODE"] = "agile"

    print("Running execution system checks and closeout generation...")
    import complete_slice

    try:
        complete_slice.prepare_slice()
    except SystemExit as exit_signal:
        sys.exit(exit_signal.code)
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
        for blocker in blocked_by:
            print(f"  - {blocker}")
    sys.exit(0)


def cmd_demand_decompose(args):
    if bool(args.request) == bool(args.request_file):
        print("Provide exactly one of --request or --request-file", file=sys.stderr)
        sys.exit(2)

    request = args.request
    if args.request_file:
        request = Path(args.request_file).read_text(encoding="utf-8")

    try:
        result = decompose_request(
            request,
            title=args.title,
            slug=args.slug,
            activate=getattr(args, "activate", False),
            confirm=getattr(args, "confirm", False),
        )
    except ValueError as error:
        print("DEMAND_DECOMPOSE_CONFLICT", file=sys.stderr)
        print(f"- reason: {error}", file=sys.stderr)
        sys.exit(1)

    print("DEMAND_DECOMPOSE_OK")
    print(f"- title: {result.title}")
    print(f"- task_type: {result.task_type}")
    print(f"- risk_level: {result.risk_level}")
    print(f"- strategy: {result.strategy}")
    print(f"- demand_doc: {result.demand_doc}")
    print(f"- roadmap_doc: {result.roadmap_doc}")
    print(f"- tasks_doc: {result.tasks_doc}")
    print(f"- activity_id: {result.activity_id}")
    print(f"- current_slice_id: {result.current_slice_id}")
    print(f"- next_slice_id: {result.next_slice_id}")
    print(f"- status: {result.status}")
    print(f"- autopilot: {'true' if result.autopilot else 'false'}")
    print(f"- activated: {'true' if result.activated else 'false'}")
    print(
        "- confirmation_required_for_activation: "
        f"{'true' if result.confirmation_required_for_activation else 'false'}"
    )
    print(f"- activation_blocked_reason: {result.activation_blocked_reason or 'none'}")
    sys.exit(0)


def cmd_activity_recycle(args):
    import recycle_activity

    code = recycle_activity.recycle_activity(args.activity_id, confirm=args.confirm, force=args.force)
    sys.exit(code)


def main():
    parser = argparse.ArgumentParser(description="Unified CLI Tooling for Execution System")
    subparsers = parser.add_subparsers(dest="command", required=True)

    slice_parser = subparsers.add_parser("slice", help="Slice commands")
    slice_subparsers = slice_parser.add_subparsers(dest="subcommand", required=True)

    start_parser = slice_subparsers.add_parser("start", help="Start a slice")
    start_parser.add_argument("id", help="Slice ID to start")

    complete_parser = slice_subparsers.add_parser("complete", help="Complete the current slice")
    complete_parser.add_argument("--agile", action="store_true", help="Run in Agile Mode (skip repo smoke tests for faster execution)")
    subparsers.add_parser("status", help="Show current status")

    activity_parser = subparsers.add_parser("activity", help="Activity commands")
    activity_subparsers = activity_parser.add_subparsers(dest="subcommand", required=True)

    recycle_parser = activity_subparsers.add_parser("recycle", help="Recycle a completed activity")
    recycle_parser.add_argument("activity_id", help="Activity ID to recycle")
    recycle_parser.add_argument("--confirm", action="store_true", help="Confirm recycling and move the activity")
    recycle_parser.add_argument("--force", action="store_true", help="Recycle even when the activity is not done or is current focus")

    demand_parser = subparsers.add_parser("demand", help="Demand decomposition commands")
    demand_subparsers = demand_parser.add_subparsers(dest="subcommand", required=True)

    decompose_parser = demand_subparsers.add_parser("decompose", help="Decompose a natural-language demand into execution artifacts")
    decompose_parser.add_argument("--title", help="Optional short title for the generated demand")
    decompose_parser.add_argument("--slug", help="Optional readable slug override for generated file names and activity id suffix")
    decompose_parser.add_argument("--request", help="Natural-language request content")
    decompose_parser.add_argument("--request-file", help="Read natural-language request content from a file")
    decompose_parser.add_argument("--activate", action="store_true", help="Switch current focus to the generated activity")
    decompose_parser.add_argument(
        "--confirm",
        action="store_true",
        help="Explicitly confirm activation for review-gated generated activities",
    )

    args = parser.parse_args()

    if args.command == "slice":
        if args.subcommand == "start":
            cmd_slice_start(args)
        elif args.subcommand == "complete":
            cmd_slice_complete(args)
    elif args.command == "demand":
        if args.subcommand == "decompose":
            cmd_demand_decompose(args)
    elif args.command == "activity":
        if args.subcommand == "recycle":
            cmd_activity_recycle(args)
    elif args.command == "status":
        cmd_status(args)

if __name__ == "__main__":
    main()
