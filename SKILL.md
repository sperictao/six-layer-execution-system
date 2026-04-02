---
name: six-layer-execution-system
description: Repo-root shim for the standalone Six-Layer Execution System plugin repository. Read the plugin skill as source of truth, then use the root convenience entrypoints when working from repo root.
---

# Six-Layer Execution System

这个根目录 skill 只是当前独立插件仓库的便捷入口。

权威说明收敛在插件 skill：

- `skills/six-layer-execution-system/SKILL.md`

如果根目录说明和插件说明有漂移，以插件 skill 为准。

## 使用顺序

1. 先读 `skills/six-layer-execution-system/SKILL.md`。
2. 如果你从仓库根目录操作，优先使用根目录便捷入口：
   - `python3 scripts/inspect_openclaw_execution_system.py --format markdown`
   - `python3 scripts/run_local_execution_checks.py checks --timeout 60`
3. 如果你希望走插件包装入口，使用：
   - `python3 scripts/inspect_execution_system.py --format markdown`
   - `python3 scripts/run_execution_checks.py checks --timeout 60`

## 仓库职责

- `.codex-plugin/`、`skills/`、`agents/` 提供插件发现与交互元数据。
- 插件根目录本身提供最小可运行的 execution-system 运行态。
- `references/` 提供本地参考文档与 source map。
- `scripts/` 同时提供根入口和插件安全包装脚本。

不要在根目录和插件 skill 各维护一份完整规则文档。
