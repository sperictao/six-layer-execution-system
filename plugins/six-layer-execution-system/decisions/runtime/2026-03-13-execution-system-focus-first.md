# Decision: execution system uses focus-first execution

- date: 2026-03-13
- project: runtime
- status: accepted

## Context
- 工作区已经从单活动执行升级到多 activity ledger。
- 一旦允许多个 activity 并存，就必须解决“系统默认推进哪一条”的问题。
- 如果不收紧默认执行边界，恢复型触发或自动推进很容易跨 activity 串线。

## Options considered
- A. 多 activity 并存时，任何 `autopilot=true` 的 activity 都可被自动推进
- B. 默认只允许 current focus activity 自动推进，其他 activity 只做恢复 / 跟踪 / 提醒
- C. 完全禁止自动推进，所有 activity 都必须人工触发

## Chosen
- 采用 B：focus-first execution。

## Why
- 它保留了自动推进的价值，但把执行范围锁在唯一 focus 上。
- 它避免多条业务线、规范线、等待线互相串扰。
- 它与 `ACTIVE.md` 作为唯一运行时真相源的设计一致。

## Rejected because
- A 风险太高，会导致“系统自己在多条线之间跳转”。
- C 太保守，会让恢复型触发与主动推进能力退化。

## Review trigger
- 如果未来引入更强的 activity scheduler，或允许显式的 fallback execution policy，则需要重审本决策。
