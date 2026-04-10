#!/usr/bin/env python3
from __future__ import annotations

import json
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Optional

from execution_system_paths import WORKSPACE
ACTIVE = WORKSPACE / "ACTIVE.md"

LEDGER_META_KEYS = (
    "version",
    "mode",
    "current_focus_activity_id",
    "default_reply_activity_id",
    "selection_policy",
    "updated_at",
)

SCALAR_KEYS = (
    "activity_id",
    "title",
    "type",
    "owner",
    "status",
    "priority",
    "autopilot",
    "focus_rank",
    "repo",
    "path",
    "scope",
    "goal",
    "waiting_on",
    "unblock_condition",
    "source_doc",
    "roadmap_doc",
    "tasks_doc",
    "current_slice_id",
    "objective",
    "next_slice_id",
    "execution_mode",
    "current_wave_id",
    "last_commit",
    "done_definition",
)


@dataclass
class Activity:
    heading: str
    fields: Dict[str, str]
    list_fields: Dict[str, List[str]]
    _raw_lines: List[str] = __import__("dataclasses").field(default_factory=list)
    _ledger: Optional['Ledger'] = None

    @property
    def activity_id(self) -> Optional[str]:
        return self.fields.get("activity_id")

    @property
    def type(self) -> Optional[str]:
        return self.fields.get("type")

    @property
    def status(self) -> Optional[str]:
        return self.fields.get("status")

    @property
    def repo_path(self) -> Optional[str]:
        return self.fields.get("path")

    @property
    def repo_name(self) -> Optional[str]:
        return self.fields.get("repo")

    @property
    def current_slice_id(self) -> Optional[str]:
        return self.fields.get("current_slice_id")

    @property
    def next_slice_id(self) -> Optional[str]:
        return self.fields.get("next_slice_id")

    @property
    def last_commit(self) -> Optional[str]:
        return self.fields.get("last_commit")

    def scalar(self, key: str, default: Optional[str] = None) -> Optional[str]:
        return self.fields.get(key, default)

    def items(self, key: str) -> List[str]:
        return list(self.list_fields.get(key, []))

    def as_dict(self) -> dict:
        return {
            "heading": self.heading,
            "fields": self.fields,
            "list_fields": self.list_fields,
        }

    def update_fields(self, **updates: str) -> None:
        for key, value in updates.items():
            self.fields[key] = value
            updated = False
            for i, line in enumerate(self._raw_lines):
                if re.match(rf"^\s*- {re.escape(key)}: `[^`]+`\s*$", line):
                    m = re.match(rf"^(\s*- {re.escape(key)}: `)[^`]+(`\s*)$", line)
                    if m:
                        self._raw_lines[i] = f"{m.group(1)}{value}{m.group(2)}"
                        updated = True
                        break
                elif re.match(rf"^\s*- {re.escape(key)}: .+$", line):
                    m = re.match(rf"^(\s*- {re.escape(key)}: ).+$", line)
                    if m:
                        self._raw_lines[i] = f"{m.group(1)}{value}"
                        updated = True
                        break
            
            if not updated:
                insert_idx = len(self._raw_lines)
                for i, line in enumerate(self._raw_lines):
                    if re.match(r"^\s*- [^:]+:\s*$", line):
                        insert_idx = i
                        break
                self._raw_lines.insert(insert_idx, f"- {key}: `{value}`")

    def save(self) -> None:
        if self._ledger:
            self._ledger.save()
        else:
            raise RuntimeError("Activity is not attached to a Ledger; cannot save.")


@dataclass
class Ledger:
    meta: Dict[str, str]
    activities: Dict[str, Activity]
    activity_index: List[str]
    _path: Optional[Path] = None
    _all_lines: Optional[List[str]] = None
    _activities_section_range: Optional[tuple[int, int]] = None
    _pre_activities_lines: Optional[List[str]] = None

    @property
    def current_focus_activity_id(self) -> Optional[str]:
        return self.meta.get("current_focus_activity_id")

    def get_activity(self, activity_id: str) -> Optional[Activity]:
        return self.activities.get(activity_id)

    def get_current_focus_activity(self) -> Optional[Activity]:
        focus = self.current_focus_activity_id
        if not focus:
            return None
        return self.activities.get(focus)

    def list_activities(self) -> List[Activity]:
        ordered: List[Activity] = []
        seen = set()
        for activity_id in self.activity_index:
            activity = self.activities.get(activity_id)
            if activity is not None:
                ordered.append(activity)
                seen.add(activity_id)
        for activity_id, activity in self.activities.items():
            if activity_id not in seen:
                ordered.append(activity)
        return ordered

    def list_runnable_activities(self) -> List[Activity]:
        out: List[Activity] = []
        for activity in self.list_activities():
            if activity.scalar("autopilot") != "true":
                continue
            if activity.status not in {"ready", "in_progress"}:
                continue
            if activity.type == "waiting":
                continue
            blocked = activity.items("blocked_by")
            if blocked and blocked != ["none"]:
                continue
            out.append(activity)
        return out

    def as_dict(self) -> dict:
        return {
            "meta": self.meta,
            "activity_index": self.activity_index,
            "activities": {k: v.as_dict() for k, v in self.activities.items()},
        }

    def update_fields(self, **updates: str) -> None:
        if self._all_lines is None:
            raise RuntimeError("Ledger was not fully parsed with file content; cannot update.")
        
        for key, value in updates.items():
            self.meta[key] = value
            updated = False
            # Find the Ledger meta section in _all_lines and update it
            in_meta = False
            for i, line in enumerate(self._all_lines):
                if line.strip() == "## Ledger meta":
                    in_meta = True
                    continue
                if in_meta and line.startswith("## "):
                    # Insert if not found before next section
                    self._all_lines.insert(i, f"- {key}: `{value}`")
                    # Adjust _activities_section_range because we inserted a line before it
                    if self._activities_section_range:
                        start, end = self._activities_section_range
                        if i < start:
                            self._activities_section_range = (start + 1, end + 1)
                    updated = True
                    break
                
                if in_meta:
                    if re.match(rf"^\s*- {re.escape(key)}: `[^`]+`\s*$", line):
                        m = re.match(rf"^(\s*- {re.escape(key)}: `)[^`]+(`\s*)$", line)
                        if m:
                            self._all_lines[i] = f"{m.group(1)}{value}{m.group(2)}"
                            updated = True
                            break
                    elif re.match(rf"^\s*- {re.escape(key)}: .+$", line):
                        m = re.match(rf"^(\s*- {re.escape(key)}: ).+$", line)
                        if m:
                            self._all_lines[i] = f"{m.group(1)}{value}"
                            updated = True
                            break
            
            if not updated and in_meta:
                # We hit EOF while in meta
                self._all_lines.append(f"- {key}: `{value}`")
                
    def save(self) -> None:
        if not self._path or self._all_lines is None or self._activities_section_range is None:
            raise RuntimeError("Ledger was not fully parsed with file content; cannot save.")
            
        start, end = self._activities_section_range
        new_activities_lines = list(self._pre_activities_lines) if self._pre_activities_lines else []
        
        for act in self.list_activities():
            new_activities_lines.extend(act._raw_lines)
            
        self._all_lines = self._all_lines[:start] + new_activities_lines + self._all_lines[end:]
        self._activities_section_range = (start, start + len(new_activities_lines))
        
        self._path.write_text("\n".join(self._all_lines) + "\n", encoding="utf-8")


def _parse_backtick_value(line: str, key: str) -> Optional[str]:
    match = re.match(rf"^- {re.escape(key)}: `([^`]+)`$", line.strip())
    return match.group(1) if match else None


def _parse_simple_value(line: str, key: str) -> Optional[str]:
    match = re.match(rf"^- {re.escape(key)}: (.+)$", line.strip())
    return match.group(1).strip() if match else None


def _extract_section_with_range(lines: List[str], title: str) -> tuple[List[str], int, int]:
    start = None
    for idx, line in enumerate(lines):
        if line.strip() == f"## {title}":
            start = idx + 1
            break
    if start is None:
        return [], -1, -1
    end = len(lines)
    for idx in range(start, len(lines)):
        if lines[idx].startswith("## "):
            end = idx
            break
    return lines[start:end], start, end

def _extract_section(lines: List[str], title: str) -> List[str]:
    return _extract_section_with_range(lines, title)[0]


def parse_ledger(path: Path = ACTIVE) -> Ledger:
    lines = path.read_text(encoding="utf-8").splitlines()

    meta_lines = _extract_section(lines, "Ledger meta")
    meta: Dict[str, str] = {}
    for line in meta_lines:
        for key in LEDGER_META_KEYS:
            value = _parse_backtick_value(line, key)
            if value is not None:
                meta[key] = value

    index_lines = _extract_section(lines, "Activity index")
    activity_index: List[str] = []
    for line in index_lines:
        m = re.match(r"^- `([^`]+)`$", line.strip())
        if m:
            activity_index.append(m.group(1))

    activities_lines, sec_start, sec_end = _extract_section_with_range(lines, "Activities")
    activities: Dict[str, Activity] = {}

    current_heading: Optional[str] = None
    block: List[str] = []
    pre_activities_lines: List[str] = []

    def flush() -> None:
        nonlocal current_heading, block
        if not current_heading:
            return
        fields: Dict[str, str] = {}
        list_fields: Dict[str, List[str]] = {}
        current_list_key: Optional[str] = None
        for raw in block:
            stripped = raw.rstrip()
            if stripped.startswith("- "):
                current_list_key = None
                matched = False
                for key in SCALAR_KEYS:
                    value = _parse_backtick_value(stripped, key)
                    if value is not None:
                        fields[key] = value
                        matched = True
                        break
                    value2 = _parse_simple_value(stripped, key)
                    if value2 is not None:
                        fields[key] = value2
                        matched = True
                        break
                if not matched:
                    m = re.match(r"^- ([^:]+):$", stripped)
                    if m:
                        current_list_key = m.group(1).strip()
                        list_fields[current_list_key] = []
            elif stripped.startswith("  - ") and current_list_key:
                list_fields[current_list_key].append(stripped[4:].strip())
            else:
                current_list_key = None
        activity = Activity(current_heading, fields, list_fields)
        activity._raw_lines = block.copy()
        if activity.activity_id:
            activities[activity.activity_id] = activity
        current_heading = None
        block = []

    for line in activities_lines:
        if line.startswith("### Activity: "):
            flush()
            current_heading = line[len("### Activity: ") :].strip()
            block = [line]
        else:
            if current_heading is not None:
                block.append(line)
            else:
                pre_activities_lines.append(line)
    flush()

    ledger = Ledger(meta=meta, activities=activities, activity_index=activity_index)
    ledger._path = path
    ledger._all_lines = lines
    ledger._activities_section_range = (sec_start, sec_end)
    ledger._pre_activities_lines = pre_activities_lines

    for act in ledger.activities.values():
        act._ledger = ledger

    return ledger


def get_current_focus_activity(path: Path = ACTIVE) -> Optional[Activity]:
    return parse_ledger(path).get_current_focus_activity()


def dump_current_focus(path: Path = ACTIVE) -> dict:
    ledger = parse_ledger(path)
    focus = ledger.get_current_focus_activity()
    return {
        "focus_activity_id": ledger.current_focus_activity_id,
        "focus": focus.as_dict() if focus else None,
    }


if __name__ == "__main__":
    ledger = parse_ledger()
    print(json.dumps(ledger.as_dict(), ensure_ascii=False, indent=2))
