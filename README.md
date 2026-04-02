# Six-Layer Execution System Plugin

这个仓库现在是独立的 Codex 插件仓库；插件根目录本身就是 six-layer execution-system 的默认运行态与参考文档入口。

## 设计边界

- `.codex-plugin/`、`skills/`、`agents/` 负责插件发现、展示和交互入口。
- 根目录控制文件、`contracts/`、`docs/`、`roadmaps/`、`tasks/`、`memory/` 共同组成默认运行态真相。
- 根目录 `references/` 与 `scripts/` 是当前仓库自带的文档与入口，不再依赖外层宿主仓库。

## 主要入口

- manifest：`.codex-plugin/plugin.json`
- skill：`skills/six-layer-execution-system/SKILL.md`
- 根目录 skill：`SKILL.md`
- agent 元数据：`agents/openai.yaml`
- 根目录入口：
  - `scripts/inspect_openclaw_execution_system.py`
  - `scripts/run_local_execution_checks.py`
- 插件包装脚本：
  - `scripts/inspect_execution_system.py`
  - `scripts/run_execution_checks.py`

## 目录约定

- 仓库根目录直接承载 execution-system 运行态；不再额外嵌套 `workspace/`。
- `references/` 保存安装说明、source map、上游运行时与本地执行系统文档。
- `scripts/` 同时提供根目录便捷命令和插件安全包装命令。

## 本地运行

在仓库根目录执行：

```bash
python3 scripts/inspect_openclaw_execution_system.py --format markdown
python3 scripts/run_local_execution_checks.py checks --timeout 60
python3 scripts/run_local_execution_checks.py full-tests --timeout 60
```

如果你希望验证插件公开入口，也可以执行：

```bash
python3 scripts/inspect_execution_system.py --format markdown
python3 scripts/run_execution_checks.py checks --timeout 60
```
