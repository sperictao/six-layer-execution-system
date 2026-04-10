#!/usr/bin/env python3
from __future__ import annotations

import argparse
import importlib.util
import json
import subprocess
import sys
from typing import Any

from repo_paths import CLI_PATH, CONFIG_PATH, PACKAGE_ROOT, REPO_ROOT, STATE_ROOT, WORKSPACE
SECRET_KEYS = {
    "apiKey",
    "token",
    "accessToken",
    "refreshToken",
    "secret",
    "clientSecret",
    "password",
    "authorization",
    "bearerToken",
}


def run_text(command: list[str]) -> str | None:
    try:
        return subprocess.check_output(command, text=True, stderr=subprocess.STDOUT).strip()
    except Exception:
        return None


def redact(value: Any) -> Any:
    if isinstance(value, dict):
        result: dict[str, Any] = {}
        for key, item in value.items():
            lowered = key.lower()
            if key in SECRET_KEYS or lowered in {k.lower() for k in SECRET_KEYS}:
                result[key] = "<redacted>"
            elif "key" in lowered and "monkey" not in lowered:
                result[key] = "<redacted>"
            else:
                result[key] = redact(item)
        return result
    if isinstance(value, list):
        return [redact(item) for item in value]
    return value


def load_config_summary() -> dict[str, Any]:
    if not CONFIG_PATH.exists():
        return {"exists": False}
    data = json.loads(CONFIG_PATH.read_text())
    summary = {}
    for key in ("agents", "skills", "gateway", "channels", "models", "providers"):
        if key in data:
            summary[key] = data[key]
    return {"exists": True, "data": redact(summary)}


def load_ledger_summary() -> dict[str, Any]:
    script_path = WORKSPACE / "scripts" / "active_ledger.py"
    active_path = WORKSPACE / "ACTIVE.md"
    scripts_dir = script_path.parent
    if not script_path.exists() or not active_path.exists():
        return {"exists": False}

    spec = importlib.util.spec_from_file_location("active_ledger", script_path)
    if spec is None or spec.loader is None:
        return {"exists": False, "error": "cannot import active_ledger.py"}
    module = importlib.util.module_from_spec(spec)
    original_sys_path = list(sys.path)
    try:
        sys.path.insert(0, str(scripts_dir))
        sys.modules[spec.name] = module
        spec.loader.exec_module(module)
        ledger = module.parse_ledger()
    except Exception as exc:
        return {"exists": False, "error": f"ledger import failed: {exc}"}
    finally:
        sys.path[:] = original_sys_path
    activities: list[dict[str, Any]] = []
    for activity in ledger.list_activities():
        activities.append(
            {
                "activity_id": activity.activity_id,
                "title": activity.scalar("title"),
                "type": activity.scalar("type"),
                "status": activity.scalar("status"),
                "focus_rank": activity.scalar("focus_rank"),
                "autopilot": activity.scalar("autopilot"),
                "path": activity.scalar("path") or activity.scalar("repo"),
                "current_slice_id": activity.scalar("current_slice_id"),
                "next_slice_id": activity.scalar("next_slice_id"),
            }
        )
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
        for path in (WORKSPACE / "docs").glob("execution-system*.md")
    ) if (WORKSPACE / "docs").exists() else []
    workspace_scripts = sorted(
        path.name
        for path in (WORKSPACE / "scripts").glob("*")
        if path.is_file() and ("execution_system" in path.name or path.name.startswith(("check_", "test_", "accept_", "complete_", "active_ledger", "set_focus")))
    ) if (WORKSPACE / "scripts").exists() else []
    return {
        "repo": {
            "root": str(REPO_ROOT),
        },
        "cli": {
            "path": CLI_PATH,
            "version": run_text([CLI_PATH, "--version"]),
        },
        "package": {
            "root": str(PACKAGE_ROOT),
            "exists": PACKAGE_ROOT.exists(),
            "readme": str(PACKAGE_ROOT / "README.md"),
            "bundled_skills_dir": str(PACKAGE_ROOT / "skills"),
        },
        "state_root": str(STATE_ROOT),
        "workspace": {
            "root": str(WORKSPACE),
            "exists": WORKSPACE.exists(),
            "docs": workspace_docs,
            "scripts_sample": workspace_scripts,
        },
        "config": load_config_summary(),
        "ledger": load_ledger_summary(),
        "upstream_docs": {
            "readme": str(PACKAGE_ROOT / "README.md"),
            "agents_cli": str(PACKAGE_ROOT / "docs" / "cli" / "agents.md"),
            "sandbox_cli": str(PACKAGE_ROOT / "docs" / "cli" / "sandbox.md"),
            "multi_agent_sandbox_tools": str(PACKAGE_ROOT / "docs" / "tools" / "multi-agent-sandbox-tools.md"),
            "pi_architecture": str(PACKAGE_ROOT / "docs" / "zh-CN" / "pi.md"),
        },
    }


def to_markdown(snapshot: dict[str, Any]) -> str:
    lines: list[str] = []
    lines.append("# Six-Layer Execution System Snapshot")
    lines.append("")
    lines.append("## Repository")
    lines.append(f"- repo_root: `{snapshot['repo']['root']}`")
    lines.append("")
    lines.append("## Install")
    lines.append(f"- cli: `{snapshot['cli']['path']}`")
    lines.append(f"- version: `{snapshot['cli']['version'] or 'unknown'}`")
    lines.append(f"- package_root: `{snapshot['package']['root']}`")
    lines.append("")
    lines.append("## Workspace")
    lines.append(f"- state_root: `{snapshot['state_root']}`")
    lines.append(f"- workspace_root: `{snapshot['workspace']['root']}`")
    for doc in snapshot["workspace"]["docs"]:
        lines.append(f"- execution_doc: `{doc}`")
    lines.append("")
    lines.append("## Ledger")
    ledger = snapshot["ledger"]
    if not ledger.get("exists"):
        lines.append("- ledger: missing")
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
    lines.append("")
    lines.append("## Redacted Config")
    config = snapshot["config"]
    if not config.get("exists"):
        lines.append("- config: missing")
    else:
        lines.append("```json")
        lines.append(json.dumps(config["data"], indent=2, ensure_ascii=False))
        lines.append("```")
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(description="Inspect local OpenClaw execution-system state.")
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
