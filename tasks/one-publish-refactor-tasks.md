# one-publish refactor tasks

## Current phase
- Phase 5 - High-risk core split and shell collapse (`PR-E / Slice P2 - first frontend shell-collapse cut`)

## PR queue

### PR-A - pure split without behavior change
- phase_id: `PH-1`
- goal:
  - 用最低风险方式先把最独立的纯逻辑拆出去
- scope:
  - 前端纯函数
  - 后端 export / render / open snapshot 逻辑
- files:
  - `src/lib/tauri/invokeErrors.ts`
  - `src/features/history/utils/historyFilters.ts`
  - `src/features/repository/utils/pathUtils.ts`
  - `src-tauri/src/commands/export.rs`
  - `src-tauri/src/commands/mod.rs`
- validation:
  - `pnpm typecheck`
  - `pnpm test`
  - `cargo check`
- done_definition:
  - 前端纯函数已抽出并接线完成
  - 后端 export 逻辑已迁移到子模块并 re-export
  - 行为不变
  - 三条验证命令通过
- rollback_strategy:
  - 若接线异常，按独立 helper / export module 粒度回滚，不把行为修复拖进后续 PR
- risk:
  - low

#### Task 1 - extract invoke error helpers
- objective:
  - 从 `src/App.tsx` 抽出 invoke error / failure analysis helpers
- files:
  - `src/App.tsx`
  - `src/lib/tauri/invokeErrors.ts`
- steps:
  - 新建 `src/lib/tauri/invokeErrors.ts`
  - 迁移 `analyzeBranchRefreshFailure`
  - 迁移 `analyzeProviderDetectFailure`
  - 迁移 `analyzeProjectScanFailure`
  - 迁移 `analyzePublishExecutionFailure`
  - 迁移 `extractInvokeErrorMessage`
  - 迁移 `extractInvokeErrorCode`
  - 更新 `App.tsx` import 与调用
- validation:
  - `pnpm typecheck`
- done_definition:
  - helpers 已迁移
  - `App.tsx` 引用正常
  - 类型检查通过

#### Task 2 - extract history filter utils
- objective:
  - 从 `src/App.tsx` 抽出 history filter 纯逻辑
- files:
  - `src/App.tsx`
  - `src/features/history/utils/historyFilters.ts`
- steps:
  - 新建 `src/features/history/utils/historyFilters.ts`
  - 迁移 `filterExecutionHistory`
  - 迁移 `normalizePathForMatch`
  - 迁移 `isRecordInRepository`
  - 更新 import 与调用
- validation:
  - `pnpm typecheck`
- done_definition:
  - history filter utils 已迁移
  - 类型检查通过

#### Task 3 - extract path utils
- objective:
  - 抽出路径前缀映射纯逻辑
- files:
  - `src/App.tsx`
  - `src/features/repository/utils/pathUtils.ts`
- steps:
  - 新建 `src/features/repository/utils/pathUtils.ts`
  - 迁移 `remapPathPrefix`
  - 更新 import 与调用
- validation:
  - `pnpm typecheck`
- done_definition:
  - path utils 已迁移
  - 类型检查通过

#### Task 4 - extract backend export module
- objective:
  - 把 export / render / open snapshot 相关逻辑迁移到后端子模块
- files:
  - `src-tauri/src/commands.rs`
  - `src-tauri/src/commands/export.rs`
  - `src-tauri/src/commands/mod.rs`
- steps:
  - 新建 `src-tauri/src/commands/export.rs`
  - 迁移 `export_preflight_report`
  - 迁移 `export_execution_snapshot`
  - 迁移 `export_failure_group_bundle`
  - 迁移 `export_execution_history`
  - 迁移 `export_diagnostics_index`
  - 迁移 `open_execution_snapshot`
  - 迁移 render helpers 与 csv/html/markdown 辅助函数
  - 在 `commands/mod.rs` 做 re-export
- validation:
  - `cargo check`
- done_definition:
  - export 模块迁移完成
  - re-export 正常
  - `cargo check` 通过

#### Task 5 - run full validation and behavior review
- phase_id: `PH-1`
- objective:
  - 对 PR-A 做最终验证，确认结构变更没有引入行为变化
- files:
  - repo-wide
- steps:
  - 跑 `pnpm typecheck`
  - 跑 `pnpm test`
  - 跑 `cargo check`
  - 检查 diff 是否只涉及结构拆分与接线
- validation:
  - `pnpm typecheck`
  - `pnpm test`
  - `cargo check`
- done_definition:
  - 三条命令通过
  - 未引入额外范围变化
- rollback_strategy:
  - validation task itself无状态变更；若结论错误，回到对应 slice 重新校验

### PR-B - backend module split continuation
- phase_id: `PH-2`
- goal:
  - 继续拆后端独立模块
- validation:
  - `cargo check`
- done_definition:
  - commands 领域边界清晰
  - checks 通过
- rollback_strategy:
  - 优先按领域模块回滚，避免把 repository / config / environment 改动混成一团
- risk:
  - medium

#### Slice 1 - `provider.rs` + `updater.rs`
- phase_id: `PH-2`
- status:
  - committed
- commit:
  - `861a7e2`
- scope:
  - `provider.rs`
  - `updater.rs`
- rollback_strategy:
  - 若 provider 或 updater 子模块拆分引入回归，按该 committed slice 回滚

#### Slice 2A - `repository.rs` project-scan / provider-detect / path helpers
- phase_id: `PH-2`
- rollback_strategy:
  - 若 repository project-scan / provider-detect 拆分回归，按该 slice 直接回滚
- goal:
  - 先拆 repository 里最独立、最不容易牵动 git runtime 的一半
- scope:
  - `find_project_root`
  - `find_project_file`
  - `scan_publish_profiles`
  - `has_extension_file`
  - `has_file`
  - `detect_provider_from_path`
  - `detect_repository_provider`
  - `scan_project_files`
  - `scan_project`
- non_goals:
  - 不碰 `check_repository_branch_connectivity`
  - 不碰 `scan_repository_branches`
  - 不碰 publish runtime
- validation:
  - `cargo check`
- done_definition:
  - `src-tauri/src/commands/repository.rs` 已创建
  - 上述 project-scan / provider-detect / path helper 逻辑已迁移
  - `commands/mod.rs` 已正确声明与 re-export
  - `cargo check` 通过
- rollback_strategy:
  - 若 repository 拆分导致 path/provider 识别异常，回滚到拆分前的 repository 命令聚合实现
- risk:
  - low-to-medium

#### Slice 2B - `repository.rs` git branch / connectivity
- phase_id: `PH-2`
- rollback_strategy:
  - 若 git branch / connectivity 拆分回归，按该 slice 直接回滚
- goal:
  - 再拆 repository 中与 git 过程、分支扫描、连通性检查相关逻辑
- scope:
  - `check_repository_branch_connectivity`
  - `scan_repository_branches`
  - git/path error classify helpers（若仍未迁移）
- validation:
  - `cargo check`
- done_definition:
  - git branch / connectivity 相关 command 已迁移
  - `cargo check` 通过
- rollback_strategy:
  - 若 git 过程或错误分类出现回归，按 branch/connectivity slice commit 回滚
- risk:
  - medium

#### Slice 3 - `config.rs` + `environment.rs` + `artifact.rs`
- phase_id: `PH-2`
- rollback_strategy:
  - 若 Phase 2 剩余命令域拆分方向被证明过宽，回到子切片逐块推进
- goal:
  - 继续拆剩余独立命令域
- validation:
  - `cargo check`
- done_definition:
  - 对应命令按领域可定位
  - `cargo check` 通过
- rollback_strategy:
  - 按 config / environment / artifact 子域逐块回滚，避免一次性打回整个 Phase 2
- risk:
  - medium

#### Slice 3A - `config.rs`
- phase_id: `PH-2`
- goal:
  - 先拆最独立的 config import/export 相关命令
- scope:
  - `export_config`
  - `import_config`
  - `apply_imported_config`
- validation:
  - `cargo check`
- done_definition:
  - `src-tauri/src/commands/config.rs` 已创建
  - config 相关命令已迁移并正确 re-export
  - `cargo check` 通过
- rollback_strategy:
  - 若配置导入导出语义异常，按 config 子模块切片回滚
- risk:
  - low

#### Slice 3B - `environment.rs`
- phase_id: `PH-2`
- goal:
  - 再拆 environment check / fix 相关命令
- scope:
  - `run_environment_check`
  - `apply_fix`
  - `validate_and_parse_fix_command`
- validation:
  - `cargo check`
- done_definition:
  - `environment.rs` 已创建并接线
  - `cargo check` 通过
- rollback_strategy:
  - 若环境检测或修复命令行为异常，按 environment 子模块切片回滚
- risk:
  - low-to-medium

#### Slice 3C - `artifact.rs`
- phase_id: `PH-2`
- goal:
  - 最后拆 artifact package / sign 相关命令
- scope:
  - `package_artifact`
  - `sign_artifact`
- validation:
  - `cargo check`
- done_definition:
  - `artifact.rs` 已创建并接线
  - `cargo check` 通过
- rollback_strategy:
  - 若打包或签名流程回归，按 artifact 子模块切片回滚
- risk:
  - low-to-medium

### PR-C - frontend behavior hooks split
- phase_id: `PH-3`
- goal:
  - 抽离行为层 hooks
- scope:
  - `useRepositoryActions.ts`
  - `usePublishExecution.ts`
  - `useDiagnosticsExports.ts`
  - `useProfiles.ts`
- validation:
  - `pnpm typecheck`
  - `pnpm test`
- done_definition:
  - hooks 接线完成
  - 行为不变
- rollback_strategy:
  - 若某个 hook 抽离导致状态接线异常，按单 hook 粒度回滚，不跨行为域补丁式修修补补
- risk:
  - medium

#### Slice C1 - `useDiagnosticsExports.ts`
- phase_id: `PH-3`
- rollback_strategy:
  - 若 diagnostics exports hook 改动引起行为回归，按该 hook slice 直接回滚
- goal:
  - 先抽离导出类行为，减少 `App.tsx` 中与导出动作相关的副作用代码
- scope:
  - `exportExecutionSnapshot`
  - `exportFailureGroupBundle`
  - `exportExecutionHistory`
  - `exportDailyTriageReport`
  - `exportDiagnosticsIndex`
- target_files:
  - `src/hooks/useDiagnosticsExports.ts`
  - `src/App.tsx`
- validation:
  - `pnpm typecheck`
  - `pnpm test`
- done_definition:
  - 导出类行为集中到 hook
  - `App.tsx` 改为接线调用，不改 UI 结构
- rollback_strategy:
  - 若导出链路行为改变，按 diagnostics exports hook 单独回滚
- risk:
  - low-to-medium

#### Slice C2 - `useRepositoryActions.ts`
- phase_id: `PH-3`
- rollback_strategy:
  - 若 repository actions hook 改动引起行为回归，按该 hook slice 直接回滚
- goal:
  - 抽离仓库增删改与 provider/branch 刷新行为
- scope:
  - `handleAddRepo`
  - `handleRemoveRepo`
  - `handleEditRepo`
  - `handleDetectRepoProvider`
  - `handleScanProjectFiles`
  - `handleRefreshRepoBranches`
- target_files:
  - `src/hooks/useRepositoryActions.ts`
  - `src/App.tsx`
- validation:
  - `pnpm typecheck`
  - `pnpm test`
- done_definition:
  - 仓库行为集中到 hook
  - toast / invoke 行为保持一致
- rollback_strategy:
  - 若仓库增删改或 branch/provider 刷新异常，按 repository actions hook 回滚
- risk:
  - medium

#### Slice C3 - `useProfiles.ts`
- phase_id: `PH-3`
- rollback_strategy:
  - 若 profiles hook 改动引起行为回归，按该 hook slice 直接回滚
- goal:
  - 抽离 profile 选择、保存、删除与 quick-create 行为
- scope:
  - `handleSelectProjectProfile`
  - `handleSelectConfigProfile`
  - `handleCreateProfile`
  - `handleDeleteProfile`
  - `handleLoadProfile`
- target_files:
  - `src/hooks/useProfiles.ts`
  - `src/App.tsx`
- validation:
  - `pnpm typecheck`
  - `pnpm test`
- done_definition:
  - profile 行为集中到 hook
  - preset/profile 接线保持不变
- rollback_strategy:
  - 若 profile 载入/删除/quick-create 行为异常，按 profiles hook 回滚
- risk:
  - medium

#### Slice C4 - `usePublishExecution.ts`
- phase_id: `PH-3`
- rollback_strategy:
  - 若 publish execution hook 改动引起行为回归，按该 hook slice 直接回滚
- goal:
  - 最后抽离发布执行与取消逻辑
- scope:
  - `execute publish` 相关逻辑
  - `cancel publish` 相关逻辑
  - 发布结果 / 输出日志相关行为接线
- target_files:
  - `src/hooks/usePublishExecution.ts`
  - `src/App.tsx`
- validation:
  - `pnpm typecheck`
  - `pnpm test`
- done_definition:
  - 发布执行行为集中到 hook
  - 运行态行为、取消逻辑、日志流保持一致
- rollback_strategy:
  - 若执行、取消或日志流行为出现偏差，按 publish execution hook 回滚
- risk:
  - medium-to-high

### PR-D - frontend UI sections split
- phase_id: `PH-4`
- goal:
  - 右侧卡片组件化
- scope:
  - `DotnetPublishCard.tsx`
  - `GenericProviderPublishCard.tsx`
  - `OutputLogCard.tsx`
  - `FailureGroupsCard.tsx`
  - `FailureGroupDetailCard.tsx`
  - `ExecutionHistoryCard.tsx`
- validation:
  - `pnpm typecheck`
  - `pnpm test`
- done_definition:
  - section 独立组件化
  - 行为不变
- rollback_strategy:
  - 若 props drilling 或 dialog wiring 出现回归，按 card / section 粒度回滚
- risk:
  - medium

### PR-E - high-risk core split
- phase_id: `PH-5`
- goal:
  - 最后拆 publish runtime 并把 `App.tsx` 收口成壳层
- scope:
  - `publish.rs`
  - `App.tsx` shell collapse
- validation:
  - `pnpm typecheck`
  - `pnpm test`
  - `cargo check`
- done_definition:
  - 高风险核心已收口
  - 大文件达到阶段目标
- rollback_strategy:
  - 若某一刀引入行为风险，优先按 slice 粒度回滚，不做跨 slice 混合修补
- risk:
  - high

#### Slice P1 - define first minimal shell-collapse cut
- phase_id: `PH-5`
- rollback_strategy:
  - 若第一刀边界定义被证明不成立，回退到上一版 phase 说明并重新划界
- goal:
  - 在动高风险逻辑之前，先把 `App.tsx` 与 `commands/mod.rs` 的第一刀边界定清楚
- scope:
  - `src/App.tsx`
  - `src-tauri/src/commands/mod.rs`
  - `src/hooks/usePublishExecution.ts`
- steps:
  - 识别 `App.tsx` 里仍然属于壳层的状态装配、dialog wiring、layout wiring
  - 识别仍然耦合 publish runtime 的部分，明确暂不动的边界
  - 定义第一刀最小切片：优先前端 shell collapse，后动后端 `publish.rs`
  - 回写 `ACTIVE.md` / daily note，作为后续执行真相
- validation:
  - 文档切片定义清楚即可；不要求立即改代码
- done_definition:
  - 明确 `PR-E.P2` 的最小可执行变更集
  - 明确哪些逻辑继续留在 `App.tsx`，哪些延后到 `publish.rs`
- rollback_strategy:
  - 此 slice 以文档边界定义为主，若结论不成立则回退到前一版 phase 说明
- risk:
  - medium

#### Slice P2 - first frontend shell-collapse cut
- phase_id: `PH-5`
- rollback_strategy:
  - 若首刀 shell-collapse 出现 wiring 回归，按当前 slice 直接回滚
- goal:
  - 在不动 publish runtime 的前提下，先继续收缩 `App.tsx` 壳层复杂度
- scope:
  - `src/App.tsx`
  - 新的前端装配 helper / hook（待 P1 定义）
- validation:
  - `pnpm typecheck`
  - `pnpm test`
- done_definition:
  - `App.tsx` 再降一刀，且行为不变
- rollback_strategy:
  - 若抽离后的 wiring 或派生逻辑出现行为漂移，按当前 slice commit 直接回滚，不把修复混入下一 slice
- risk:
  - medium-to-high
- progress_note:
  - `PR-E.P21` 到 `PR-E.P31` 已连续把 execution history props、publish content section、三栏 layout shell、history/diagnostics state、dialogs composition、layout shell state、repository/project execution/project shell state、provider presentation state 从 `App.tsx` 收口到独立 hooks / sections / shells
  - 当前 `src/App.tsx` 已降到约 `928` 行，仍高于 phase 目标的 `800` 行，但剩余块明显更贴近 publish execution orchestration，而不是纯 view wiring
  - `PR-E.P32` 的结论是：先把这轮 frontend shell-collapse wave 作为阶段性完成收口；只有在发现最后一块明确独立、且不触碰 publish runtime 的切片时才继续下刀
  - `PR-E.P36` 已把 `usePublishExecution` 邻接层定为下一阶段首选入口；`PR-E.P37` 的默认动作应是定义第一刀的 entry slice，而不是直接改代码
  - `PR-E.P37` 当前已进一步把 entry slice 收紧到 call-surface-only：只允许处理 `App.tsx -> usePublishExecution` 的参数装配与 contract 划界，不改 hook 内执行语义
  - `PR-E.P38` 的默认动作应是把 contract surface 再细化成“核心输入状态层”与“可先收口的回调/副作用层”，为真正落第一刀代码做准备
  - `PR-E.P39` 的默认动作应是把第一刀建议变更集写清楚：优先只收口 `pushRecentConfig`、`openEnvironmentDialog`、`setEnvironmentLastResult`、`buildExecutionRecord`、`persistExecutionRecord` 这组回调/副作用面，暂不移动 repo/provider/preset/config/projectInfo 这组核心输入状态面
  - `PR-E.P40` 的默认动作应是把这份建议变更集进一步落成代码切片说明：若进入代码实现，优先新增一个更窄的 publish-execution call-surface helper / composition helper，而不是直接改 `usePublishExecution` 内部流程
  - `PR-E.P41` 的默认动作应是把实现入口也写清楚：helper 放在前端 hooks/composition 层，只聚合 5 个回调/副作用面，`App.tsx` 仍直接装配核心输入状态，`usePublishExecution` 仅改参数接收面不改内部语义
  - `PR-E.P42` 的默认动作应是把实现草案边界写清楚：helper 优先落在 `src/hooks/usePublishExecutionCallSurface.ts`，且 `usePublishExecution` 第一刀只允许做签名/解构级接线改动，不允许动 invoke 顺序、cancel 路径、日志流、environment gate、publish spec 构造
  - `PR-E.P43` 的默认动作应是把真正的 implementation brief 写清：新增 helper、收口 5 个回调/副作用面、调整 `App.tsx` 调用面、让 `usePublishExecution` 接收较窄对象，但不做任何 runtime 行为改动
  - `PR-E.P44` 的默认动作应是把开工前 checklist / acceptance brief 写清：确认 helper 不吞入核心输入状态、`usePublishExecution` 只改签名/解构/引用、`App.tsx` 不引入第二状态源，并把 success/failure/cancelled 三条路径的人肉核对写成门槛
  - `PR-E.P45` 的默认动作应是把最终 go/no-go 决策点写清：只有当 checklist 全部满足时，才允许进入真正代码实现；否则继续停留在文档边界设计阶段
  - `PR-E.P46` 的默认动作应是做阶段收口：确认 planning 闭环已完成，并把状态明确标记为 `ready for go/no-go decision`
  - `PR-E.P47` 的默认动作应是停止继续扩写 planning，并把后续动作约束成真正的 go/no-go 分叉
  - 若继续推进，下一批工作应转向真正的 go/no-go 决策，而不是继续为 planning 本身增加层级
  - 2026-03-15 的 repo fact check 已给出当前默认结论：`no-go for PR-E.P57`；原因是剩余候选主要集中在 `runPublishWithSpec` / `executePublish` / `cancelPublish` orchestration，继续抽离将开始改写 runtime-adjacent contract，而不再是低风险纯接线/纯状态切片
