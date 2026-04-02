# one-publish contract

## Goal
- 在不改变产品行为的前提下，持续降低 `one-publish` 的实现复杂度。
- 通过小步、可验证、可回滚的重构，把前后端的大文件逐步收口到更稳定的边界。

## Scope
- 本 contract 约束的是 `one-publish` 第一轮重构主线。
- 适用于 roadmap、tasks、ACTIVE activity、slice closeout 与恢复问答。

## Invariants
- 行为保持不变。
- 命令协议名保持不变。
- publish runtime 的运行语义保持不变，直到专门进入对应高风险阶段。
- 每个 slice 都必须是独立、可 review、可验证、可回滚的一刀。
- 当前执行状态只能由 `ACTIVE.md` 表达，不能由 roadmap / tasks / memory 反推。

## Non-goals
- 不顺手重做 UI。
- 不切换到 Zustand / Redux 或其他新的状态管理方案。
- 不重写 store。
- 不在同一刀里同时重构前端壳层与后端高风险 publish runtime。
- 不边拆边加大型新功能。

## Forbidden moves
- 不做大爆炸重写。
- 不把低风险拆分与高风险语义改动混在同一个 slice。
- 不在没有通过 `pnpm typecheck` / `pnpm test` / `cargo check` 的情况下宣布切片完成。
- 不从 live `ACTIVE.md` 字段现拼 slice 完成通知；只允许从 frozen closeout artifact 发布。
- 不因为“顺手方便”修改 command protocol、状态管理或 UI 结构。

## Allowed tradeoffs
- 可以引入过渡 hook / helper / shell component，只要不引入行为漂移。
- 可以接受暂时增加 props / wiring 层级，只要复杂度总体下降且后续可继续收口。
- 可以先把前端壳层压薄，再进入后端 publish runtime 的高风险拆分。

## Validation baseline
- `pnpm typecheck`
- `pnpm test`
- `cargo check`

## Completion philosophy
- slice 完成不是“代码写完”，而是：实现完成、验证通过、commit 记录、ACTIVE 原子切换、closeout artifact 冻结、通知状态可追踪。
- 只有 `closed_out` 的 slice 才允许对外宣布为完成。
- phase 完成必须同时满足 roadmap 的 exit criteria 与 tasks 中所需 slice 的完成条件。

## Execution model
- 复杂任务执行真相采用：`contract + roadmap + tasks + ACTIVE`。
- `contract` 管长期约束。
- `roadmap` 管阶段结构与退出条件。
- `tasks` 管切片设计与验证。
- `ACTIVE` 管当前 focus activity 与运行态真相。

## Review triggers
- 如果需要开始拆 `publish.rs` 或调整 command protocol，必须重新审视本 contract。
- 如果发现某个 slice 无法保持“小步、可验证、可回滚”，必须先改 tasks 设计，再继续执行。
- 如果需要改变 completion protocol 或通知语义，必须同步更新执行系统总规范。  
