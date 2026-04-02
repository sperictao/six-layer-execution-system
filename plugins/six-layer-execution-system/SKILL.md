---
name: six-layer-execution-system
description: Plugin-root entry skill for a self-contained Six-Layer Execution System plugin whose root stores runtime truth.
---

# Six-Layer Execution System

这个插件根目录 skill 是当前 execution-system 插件的最短入口。

完整规则见：

- `skills/six-layer-execution-system/SKILL.md`

如果两处说明有漂移，以插件 skill 为准；但根目录 skill 也应保持 execution-system 本体优先，而不是只充当插件包装说明。

## 使用顺序

1. 先读 `ACTIVE.md`，确认 live runtime truth。
2. 再读 `skills/six-layer-execution-system/SKILL.md`。
3. 默认使用插件根目录公开入口：
   - `python3 scripts/inspect_execution_system.py --format markdown`
   - `python3 scripts/run_execution_checks.py checks --timeout 60`
   - repo-local 开发测试位于 source checkout 根 `tests/`；如需直接运行单测，使用仓库根视角命令并显式注入 `PYTHONPATH="plugins/six-layer-execution-system:plugins/six-layer-execution-system/scripts"`
4. 只有在需要排查底层包装或本机安装差异时，才直接运行：
   - `python3 scripts/inspect_openclaw_execution_system.py --format markdown`
   - `python3 scripts/run_local_execution_checks.py checks --timeout 60`
   - `full-tests` 只在带根 `tests/` 的 source checkout 中可用；standalone plugin 副本返回 `unavailable` 是预期行为

## 仓库职责

- 插件根目录直接承载 execution-system 本体与运行态真相。
- `.codex-plugin/`、`skills/`、`agents/` 提供插件发现与交互元数据。
- `references/` 提供辅助参考，不替代 live runtime truth。
- `scripts/` 提供根入口、包装入口与校验/closeout 工具。
- 仓库根 `tests/` 是 repo-local 开发资产，不属于 standalone plugin 分发面。

不要在根目录和插件 skill 各维护一份完整规则文档。
