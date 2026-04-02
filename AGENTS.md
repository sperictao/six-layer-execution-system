# AGENTS.md - Plugin Packaging Repo

这个仓库根目录不再承载 execution-system 的运行态真相。

真正可复制、可安装、可运行的插件位于：

- `plugins/six-layer-execution-system/`

## 工作边界

- 如果任务涉及 `ACTIVE.md`、`HEARTBEAT.md`、`MEMORY.md`、`docs/`、`roadmaps/`、`tasks/`、`scripts/`、`skills/` 或 `.codex-plugin/plugin.json`，把 `plugins/six-layer-execution-system/` 当作唯一 subject root。
- 根目录只负责 git 历史、分发说明和 repo-local marketplace 元数据。
- 不要把 execution-system 的 runtime truth 再搬回仓库根目录。

## 恢复顺序

1. 先进入 `plugins/six-layer-execution-system/`。
2. 读 `plugins/six-layer-execution-system/ACTIVE.md`。
3. 再按插件目录内 `AGENTS.md` 的恢复顺序继续。

## 分发约定

- 目标形态是复制 `plugins/six-layer-execution-system/` 整个目录到其它机器的 Codex 插件目录后即可使用。
- `.agents/plugins/marketplace.json` 只是本仓库里的可选开发/演示元数据，不应成为插件运行前提。
