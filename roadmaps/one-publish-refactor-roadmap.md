# one-publish refactor roadmap

## Goal
- 先降复杂度，不改产品行为。
- 不搞大爆炸重写。
- 不顺手改 UI。
- 不同时换状态管理。

## Contract reference
- `contracts/one-publish-contract.md`

## Constraints / non-goals
- 以 `contracts/one-publish-contract.md` 为长期约束真相。
- 本 roadmap 只承载 phase / dependency / exit criteria / risk，不承载当前运行态真相。

## Validation baseline
- `pnpm typecheck`
- `pnpm test`
- `cargo check`

## Phases

### Phase 1 - Low-risk extraction baseline
- objective:
  - 用最低风险方式先降低文件复杂度
  - 不改变现有行为
- outputs:
  - 前端纯函数拆出
  - 后端 `export.rs` 子模块拆出
  - `commands/mod.rs` 完成 re-export
- exit criteria:
  - `src/lib/tauri/invokeErrors.ts` 已创建并接线
  - `src/features/history/utils/historyFilters.ts` 已创建并接线
  - `src/features/repository/utils/pathUtils.ts` 已创建并接线
  - `src-tauri/src/commands/export.rs` 已创建并接线
  - 三条验证命令通过
- validation:
  - `pnpm typecheck`
  - `pnpm test`
  - `cargo check`
- risks:
  - 低风险，但要避免改动行为和 import 路径错误

### Phase 2 - Backend independent module split
- objective:
  - 继续拆独立性高、耦合较低的后端模块
- outputs:
  - `updater.rs`
  - `provider.rs`
  - `repository.rs`
  - `config.rs`
  - `environment.rs`
  - `artifact.rs`
- exit criteria:
  - 对应 command 与 helper 已按领域可定位
  - `commands.rs` 体积显著下降
  - 三条验证命令持续通过
- validation:
  - `cargo check`
  - 相关前端/集成验证保持通过
- risks:
  - repository 拆分时要留意 git/path 错误分类边界

### Phase 3 - Frontend behavior layer split
- objective:
  - 从 `App.tsx` 继续抽离行为层逻辑
- outputs:
  - `useRepositoryActions.ts`
  - `usePublishExecution.ts`
  - `useDiagnosticsExports.ts`
  - `useProfiles.ts`
- exit criteria:
  - `App.tsx` 不再承载大段业务行为逻辑
  - 业务动作集中到 hooks / api 层
- validation:
  - `pnpm typecheck`
  - `pnpm test`
- risks:
  - action 传递和状态依赖容易接线出错

### Phase 4 - Frontend UI section split
- objective:
  - 把右侧大块 UI 拆成稳定 section/card 组件
- outputs:
  - `DotnetPublishCard.tsx`
  - `GenericProviderPublishCard.tsx`
  - `OutputLogCard.tsx`
  - `FailureGroupsCard.tsx`
  - `FailureGroupDetailCard.tsx`
  - `ExecutionHistoryCard.tsx`
- exit criteria:
  - 右侧大块 section 独立组件化
  - `App.tsx` 更接近 layout shell
- validation:
  - `pnpm typecheck`
  - `pnpm test`
- risks:
  - props drilling / dialog wiring 可能变复杂

### Phase 5 - High-risk core split and shell collapse
- objective:
  - 最后处理高风险核心逻辑，把大文件压缩到目标规模
- outputs:
  - `publish.rs`
  - `App.tsx` 收缩为壳层
- exit criteria:
  - `commands.rs` 核心 publish runtime 已拆出
  - `App.tsx` 主要只负责状态装配、layout、dialog wiring
  - `App.tsx` 先降到 800 行以内，最终 300~500 行
  - `commands.rs` 拆成 6~8 个模块
- validation:
  - `pnpm typecheck`
  - `pnpm test`
  - `cargo check`
- risks:
  - publish runtime 有运行态单例、cancel、log streaming，风险最高

## Dependency notes
- Phase 1 是低风险入口，优先执行
- Backend 的 `publish.rs` 必须最后拆
- Frontend 的 UI section 拆分应晚于 behavior hooks 拆分
- `App.tsx` shell collapse 应放在 hooks 和 sections 都稳定之后

## Current recommended phase
- Phase 5 - High-risk core split and shell collapse (`PR-E / frontend shell-collapse continuation; current runtime slice lives in ACTIVE.md`)

## Phase 5 note
- `PR-E.P21` 到 `PR-E.P31` 已形成一段连续的 frontend shell-collapse wave：publish card props assembly、publish content section、三栏 layout shells、history/diagnostics state、dialogs composition、repository/project execution/project shell state、provider presentation state 已先后从 `src/App.tsx` 收口
- 当前 `src/App.tsx` 约 `928` 行，说明这一波已经显著降低组合层噪声，但尚未达到 phase exit criterion 中的 `< 800` 目标
- 风险判断：剩余块越来越贴近 publish execution orchestration / runtime boundary；若继续拆，收益与回归风险的比值会明显变差
- 结论：把这轮 frontend shell-collapse wave 作为阶段性完成收口。除非后续发现最后一块明确独立、且不触碰 publish runtime 的切片，否则不再继续为追逐行数拆 `App.tsx`
- 下一阶段推荐：先做 publish runtime 邻接层 / orchestration boundary 的进入条件判断，再决定是否进入 `publish.rs` 或 `usePublishExecution` 相关拆分
- 建议进入条件：
  - 明确哪些逻辑仍属于 `App.tsx` 组合层，哪些已经是 publish runtime 邻接层
  - 明确第一刀只允许触碰一个高耦合入口（优先 `usePublishExecution` 或其邻接调用面），不同时改 `publish.rs`
  - 继续维持 `pnpm typecheck` / `pnpm test` / `cargo check` 三条验证为每刀门槛
  - 若无法把候选切片描述成“单点进入、单点回滚、行为不变”，则暂不进入 runtime phase
- 当前首选候选入口：
  - `usePublishExecution` 邻接层
- 首刀建议不碰边界：
  - `src-tauri/src/commands/mod.rs`
  - `publish.rs`
  - provider schema / repository management / dialogs wiring
- 首刀可接受目标：
  - 只梳理 `App.tsx` 与 `usePublishExecution` 之间的 orchestration call-surface
  - 不改变 publish spec 构造语义
  - 不改变 cancel / log streaming / environment check 行为
- 当前建议的第一刀 entry slice：
  - 先定义 `usePublishExecution` 邻接层里哪些输入仍属于组合层装配，哪些已经构成 runtime-adjacent contract
  - 第一刀若落代码，优先只收口调用面参数装配，不修改 hook 内执行语义
  - 若无法把这一刀描述成“只改 call-surface、不改 runtime semantics”，则继续停留在文档边界设计阶段
- 建议的第一刀候选参数面：
  - `selectedRepoId`
  - `selectedRepo`
  - `activeProviderId`
  - `activeProviderParameters`
  - `selectedPreset`
  - `isCustomMode`
  - `customConfig`
  - `defaultOutputDir`
  - `projectInfo`
  - `pushRecentConfig`
  - `openEnvironmentDialog`
  - `setEnvironmentLastResult`
  - `buildExecutionRecord`
  - `persistExecutionRecord`
- 第一刀验收口径：
  - 只允许减少 `App.tsx` 到 `usePublishExecution(...)` 这一调用点的参数装配噪声
  - 不允许改变 publish success / failure / cancelled 三条主路径的行为定义
  - 不允许修改 log streaming、cancel 语义、environment gate、spec 构造语义
- 第一刀参数分层（建议）：
  - 继续留在 `App.tsx` 组合层：`selectedRepoId`、`selectedRepo`、`activeProviderId`、`activeProviderParameters`、`selectedPreset`、`isCustomMode`、`customConfig`、`defaultOutputDir`、`projectInfo`
  - 可优先收口成较稳定调用面：`pushRecentConfig`、`openEnvironmentDialog`、`setEnvironmentLastResult`、`buildExecutionRecord`、`persistExecutionRecord`
- 设计意图：
  - 先把“副作用回调面”与“核心输入状态面”分层
  - 第一刀只尝试压缩回调/contract surface，不移动 publish spec 的核心输入来源
- 第一刀建议变更集：
  - 优先只收口：`pushRecentConfig`、`openEnvironmentDialog`、`setEnvironmentLastResult`、`buildExecutionRecord`、`persistExecutionRecord`
  - 暂时继续留在 `App.tsx`：`selectedRepoId`、`selectedRepo`、`activeProviderId`、`activeProviderParameters`、`selectedPreset`、`isCustomMode`、`customConfig`、`defaultOutputDir`、`projectInfo`
  - 目的不是减少参数个数本身，而是先把更容易漂移的副作用回调面稳定成一层较窄的 contract，再看是否值得进入下一刀
- 第一刀建议变更集说明（PR-E.P40 入口）：
  - 若后续从文档进入代码，实现应优先新增一个更窄的 publish-execution call-surface helper / composition helper，而不是立刻改 `usePublishExecution` 内部流程
  - helper 的职责只应是聚合上述 5 个回调/副作用面，不应接管 repo/provider/preset/config/projectInfo 这组核心输入状态
  - 这样可以把第一刀继续限制在“contract narrowing”而不是“runtime relocation”
- 第一刀实现入口说明（PR-E.P41 候选）：
  - 新 helper 应放在前端 hooks/composition 层，优先命名为 `usePublishExecutionCallSurface` 或同级 helper，而不是放到 `src-tauri/` 或 runtime command 层
  - `App.tsx` 只把那 5 个回调/副作用面交给该 helper，再由 helper 输出一个更稳定的 call-surface object 传给 `usePublishExecution`
  - `usePublishExecution` 本身在第一刀中最多只接受新的较窄参数对象，不改内部流程分支
  - 若需要修改超过调用签名与参数接线，说明已经越过第一刀边界，应停止并回到文档阶段
- 第一刀实现草案边界（PR-E.P42 候选）：
  - helper 文件建议落点：`src/hooks/usePublishExecutionCallSurface.ts`
  - helper 输入只包含 5 个回调/副作用面，不接收 repo/provider/preset/config/projectInfo
  - helper 输出建议是一个稳定 object，供 `usePublishExecution` 以单参数字段或子对象形式接收
  - `usePublishExecution` 第一刀允许的改动上限：参数签名调整 + 内部引用改名/解构；不允许新增/删除执行分支，不允许改 invoke 顺序，不允许改错误/取消/日志语义
- 第一刀实现 brief（PR-E.P43 候选）：
  - 目标文件：`src/hooks/usePublishExecutionCallSurface.ts`
  - 目标改动：新增 helper + 调整 `src/App.tsx` 调用面 + 让 `src/hooks/usePublishExecution.ts` 接收更窄的 call-surface object
  - 非目标：不改 tauri invoke payload，不改 publish session lifecycle，不改 cancel token 管理，不改日志缓冲/输出行为
  - 最小验收：类型通过、测试通过、`cargo check` 通过，且 UI 行为和 publish 行为体感不变
- 第一刀开工前 checklist（PR-E.P44 候选）：
  - 确认 helper 只接收 5 个回调/副作用面，不额外吞入核心输入状态
  - 确认 `usePublishExecution` diff 只涉及参数签名、解构、变量引用，不涉及行为分支
  - 确认 `App.tsx` 只减少调用面噪声，不新增第二处 publish orchestration source
  - 跑满 `pnpm typecheck` / `pnpm test` / `cargo check`，并人工核对 publish 成功、失败、取消三条路径的体感未变
- 第一刀最终开工结论（PR-E.P45 候选）：
  - 当且仅当上述 checklist 全部满足时，才允许把 `usePublishExecutionCallSurface` 作为 runtime-adjacent phase 的真正第一刀落地
  - 若任一项无法满足，则维持当前文档边界结论，不进入代码实现
  - 这意味着 `PR-E.P45` 的本质不是再扩 scope，而是把“可以开工”与“必须停住”两种结果都写成显式决策
- 当前阶段结论（PR-E.P46 / PR-E.P47）：
  - 到 `PR-E.P45` 为止，frontend shell-collapse wave 与 runtime-adjacent first-cut planning 都已经形成闭环
  - `PR-E.P46` 明确把状态标记为 `ready for go/no-go decision`
  - `PR-E.P47` 作为收口切片，不再新增 planning 细节，只保留两条后续路径：
    - `go`: 以 `usePublishExecutionCallSurface` 为第一刀进入代码实现
    - `no-go / defer`: 维持当前文档边界结论，转向其他仓库或其他 phase
  - 结论：在人类明确给出 go/no-go 之前，planning 到此停止，不再自动扩写
- 2026-03-15 repo fact-check addendum:
  - 基于对 `src/App.tsx` 与 `src/hooks/usePublishExecution.ts` 的再次实扫，当前默认结论已明确为 `no-go for PR-E.P57`
  - 原因不是缺少可改代码，而是剩余候选已明显集中在 `runPublishWithSpec` / `executePublish` / `cancelPublish` orchestration，继续下刀会更像 runtime-adjacent relocation，而不再是低风险纯接线/纯状态收口
  - 因此，Phase 5 现阶段应在 `PR-E.P56` 后正式视为阶段性暂停，直到出现新的 clean slice，或人类明确允许改 runtime-adjacent 边界
