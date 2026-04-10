#!/usr/bin/env python3
from __future__ import annotations

import argparse
import importlib.util
import json
import sys
from typing import Any

from execution_system_paths import WORKSPACE

SCRIPTS_DIR = WORKSPACE / "scripts"
DOCS_DIR = WORKSPACE / "docs"
SKILLS_DIR = WORKSPACE / "skills"


def load_ledger_summary() -> dict[str, Any]:
    script_path = SCRIPTS_DIR / "active_ledger.py"
    active_path = WORKSPACE / "ACTIVE.md"
    if not script_path.exists() or not active_path.exists():
        return {"exists": False}
    spec = importlib.util.spec_from_file_location("active_ledger", script_path)
    if spec is None or spec.loader is None:
        return {"exists": False, "error": "cannot import active_ledger.py"}
    module = importlib.util.module_from_spec(spec)
    original_sys_path = list(sys.path)
    try:
        sys.path.insert(0, str(SCRIPTS_DIR))
        sys.modules[spec.name] = module
        spec.loader.exec_module(module)
        ledger = module.parse_ledger()
    except Exception as exc:
        return {"exists": False, "error": f"ledger import failed: {exc}"}
    finally:
        sys.path[:] = original_sys_path
    activities: list[dict[str, Any]] = []
    for activity in ledger.list_activities():
        activities.append({
            "activity_id": activity.activity_id,
            "title": activity.scalar("title"),
            "type": activity.scalar("type"),
            "status": activity.scalar("status"),
            "focus_rank": activity.scalar("focus_rank"),
            "autopilot": activity.scalar("autopilot"),
            "current_slice_id": activity.scalar("current_slice_id"),
            "next_slice_id": activity.scalar("next_slice_id"),
        })
    return {
        "exists": True,
        "meta": dict(ledger.meta),
        "current_focus_activity_id": ledger.current_focus_activity_id,
        "default_reply_activity_id": ledger.meta.get("default_reply_activity_id"),
        "activity_index": list(ledger.activity_index),
        "activities": activities,
    }


def build_snapshot() -> dict[str, Any]:
    workspace_docs = sorted(
        str(path.relative_to(WORKSPACE))
        for path in DOCS_DIR.glob("execution-system*.md")
    ) if DOCS_DIR.exists() else []
    workspace_scripts = sorted(
        path.name for path in SCRIPTS_DIR.glob("*.py")
        if path.is_file()
    ) if SCRIPTS_DIR.exists() else []
    skill_files = sorted(
        str(path.relative_to(WORKSPACE))
        for path in SKILLS_DIR.rglob("SKILL.md")
    ) if SKILLS_DIR.exists() else []
    return {
        "plugin": {
            "root": str(WORKSPACE),
            "exists": WORKSPACE.exists(),
        },
        "workspace": {
            "docs": workspace_docs,
            "scripts": workspace_scripts,
            "skills": skill_files,
        },
        "ledger": load_ledger_summary(),
    }


def to_markdown(snapshot: dict[str, Any]) -> str:
    lines: list[str] = ["# Six-Layer Execution System Snapshot", ""]
    lines += [
        "## Plugin",
        f"- plugin_root: `{snapshot['plugin']['root']}`",
        f"- exists: `{snapshot['plugin']['exists']}`",
        "",
        "## Workspace",
    ]
    for doc in snapshot["workspace"]["docs"]:
        lines.append(f"- execution_doc: `{doc}`")
    for skill in snapshot["workspace"]["skills"]:
        lines.append(f"- skill: `{skill}`")
    lines.append("")
    lines.append("## Ledger")
    ledger = snapshot["ledger"]
    if not ledger.get("exists"):
        lines.append(f"- ledger: missing — {ledger.get('error', 'unknown')}")
    else:
        lines.append(f"- current_focus_activity_id: `{ledger.get('current_focus_activity_id')}`")
        lines.append(f"- default_reply_activity_id: `{ledger.get('default_reply_activity_id')}`")
        for activity in ledger.get("activities", []):
            lines.append(
                "- activity: `{}` | type=`{}` | status=`{}` | current_slice=`{}` | next_slice=`{}`".format(
                    activity.get("activity_id"),
                    activity.get("type"),
                    activity.get("status"),
                    activity.get("current_slice_id"),
                    activity.get("next_slice_id"),
                )
            )
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(description="Inspect Six-Layer Execution System plugin state.")
    parser.add_argument("--format", choices=("json", "markdown"), default="markdown")
    args = parser.parse_args()
    snapshot = build_snapshot()
    if args.format == "json":
        print(json.dumps(snapshot, indent=2, ensure_ascii=False))
    else:
        print(to_markdown(snapshot))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
