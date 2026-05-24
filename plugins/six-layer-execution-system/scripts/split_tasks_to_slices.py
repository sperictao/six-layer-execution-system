#!/usr/bin/env python3
"""Split legacy tasks file into per-slice files."""
from pathlib import Path
import re

old_path = Path(__file__).parent.parent / "tasks/one-publish-architecture-fix-tasks.md"
content = old_path.read_text(encoding="utf-8")
activity_id = "one-publish-architecture-fix"

slices = []
current_slice_id = None
current_lines = []

for line in content.splitlines():
    if line.startswith("#### Slice "):
        if current_slice_id and current_lines:
            slices.append((current_slice_id, "\n".join(current_lines)))
        rest = line[len("#### Slice "):]
        slice_id = rest.split(" ")[0].strip()
        current_slice_id = slice_id
        current_lines = []
    elif current_slice_id:
        current_lines.append(line)

if current_slice_id and current_lines:
    slices.append((current_slice_id, "\n".join(current_lines)))

out_dir = Path(__file__).parent.parent / f"tasks/{activity_id}"
out_dir.mkdir(exist_ok=True)

for sid, text in slices:
    new_content = f"# Slice {sid} — one-publish 架构修复\n\n- activity_id: `{activity_id}`\n{text}\n"
    filepath = out_dir / f"{sid}.md"
    filepath.write_text(new_content, encoding="utf-8")
    print(f"Wrote {filepath} ({len(new_content.splitlines())} lines)")

print(f"\nDone: {len(slices)} slice files in {out_dir}")
