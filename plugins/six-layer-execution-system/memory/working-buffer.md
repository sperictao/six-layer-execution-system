# Working Buffer

**Status:** IDLE
**Started:** 2026-03-12 22:00 Asia/Shanghai

Use this file only when context enters the danger zone or when compaction recovery is needed.

## Protocol
- At high context usage, append both the human message and a short agent summary for every exchange.
- After recovery, extract durable facts into `ACTIVE.md`, `memory/YYYY-MM-DD.md`, or `MEMORY.md` as appropriate.
- Clear and restart this file when a new danger-zone window begins.
