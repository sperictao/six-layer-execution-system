# AGENTS.md - Six-Layer Execution System Plugin

这个目录就是当前插件的唯一 subject root。

## 恢复顺序

1. 先读 `ACTIVE.md`，把它当作唯一 live runtime truth。
2. 再读 `skills/six-layer-execution-system/SKILL.md`，把它当作唯一详细规则源。
3. 如果需要 repo 事实，再运行：
   - `python3 scripts/inspect_execution_system.py --format markdown`
   - `python3 scripts/run_execution_checks.py checks --timeout 60`

## 边界

- `README.md` 负责安装和入口说明，不替代运行态真相。
- `references/` 只提供辅助参考，不替代运行态真相。
- `SKILL.md` 是插件根薄入口；如果和 `skills/six-layer-execution-system/SKILL.md` 漂移，以后者为准。
- repo 根的 `.agents/plugins/marketplace.json` 只是可选开发/演示元数据，不是插件运行前提。
- repo 根 `tests/` 属于 source checkout 的开发资产；独立复制插件目录时，`full-tests` 返回 `unavailable` 属于预期行为。
