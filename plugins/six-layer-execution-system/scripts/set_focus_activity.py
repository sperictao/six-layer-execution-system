#!/usr/bin/env python3
from __future__ import annotations

import re
import sys

from execution_system_paths import WORKSPACE
ACTIVE = WORKSPACE / "ACTIVE.md"


def main() -> int:
    if len(sys.argv) != 2:
        print("usage: set_focus_activity.py <activity_id>", file=sys.stderr)
        return 2

    target = sys.argv[1]
    text = ACTIVE.read_text(encoding="utf-8")
    if f"- activity_id: `{target}`" not in text:
        print(f"UNKNOWN_ACTIVITY:{target}", file=sys.stderr)
        return 1

    text2, count = re.subn(
        r"(^- current_focus_activity_id: `)([^`]+)(`$)",
        rf"\g<1>{target}\g<3>",
        text,
        count=1,
        flags=re.MULTILINE,
    )
    if count != 1:
        print("MISSING_CURRENT_FOCUS", file=sys.stderr)
        return 1

    text2, count2 = re.subn(
        r"(^- default_reply_activity_id: `)([^`]+)(`$)",
        rf"\g<1>{target}\g<3>",
        text2,
        count=1,
        flags=re.MULTILINE,
    )
    if count2 != 1:
        print("MISSING_DEFAULT_REPLY_ACTIVITY", file=sys.stderr)
        return 1

    ACTIVE.write_text(text2, encoding="utf-8")
    print(target)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
