# MEMORY.md

## User preferences
- 主人明确要求：交代过的事情要记住，不要轻易忘记；涉及之前说过的项目与任务，先查记忆和历史再答。
- 默认中文回复，称呼用户为“主人”。
- 使用 🦞 emoji。
- 以 GMT+8 为默认时区。
- 风格偏好：像秘书一样主动提醒，并主动记录重要信息。
- 任务结构偏好：简单任务直接生成计划；复杂任务不生成单独计划，改为生成 `roadmap + tasks`，`ACTIVE.md` 只保留当前执行切片。

## Working preferences
- 对进行中的项目，优先维护一份可恢复的活动任务账本（见 `ACTIVE.md`）。
- 回答“结果怎么样了 / 进展如何”这类问题前，先检查：`ACTIVE.md`、`memory/YYYY-MM-DD.md`、`MEMORY.md`、最近会话转录。

## Current project context
- `one-publish` 仓库路径：`/Users/erictao/source/repos/one-publish`
- 当前约定要做的第一刀重构：低风险纯拆分，不改行为
  - 前端先抽纯函数
  - 后端先拆 export 子模块
