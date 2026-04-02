# one-publish 重构拆分方案

## Source
- 来源：主人在主会话中明确给出的可直接开工方案
- 记录时间：2026-03-08 08:42 Asia/Shanghai
- 适用仓库：`/Users/erictao/source/repos/one-publish`

## 总目标
- 先降复杂度，不改产品行为。
- 不搞大爆炸重写。
- 不顺手改 UI。
- 不同时换状态管理。

## 总体结论
这次重构分成两条线并行：
- 前端：把 `src/App.tsx` 从“总控巨石”拆成 `feature + hook + section`
- 后端：把 `src-tauri/src/commands.rs` 按领域拆成 `commands` 子模块

## 阶段目标
- `App.tsx`: `5370` 行 → 先降到 `800` 行以内，最终 `300~500` 行
- `commands.rs`: `2741` 行 → 拆成 `6~8` 个模块

## 每一步的硬性验证
- `pnpm typecheck` 通过
- `pnpm test` 通过
- `cargo check` 通过

---

## 一、前端拆分方案

### App.tsx 当前混合的职责
至少包含以下 6 类：
1. 应用壳与 bootstrap
   - 语言同步
   - provider schema 加载
   - 执行历史初始化
   - Tauri window drag 行为
   - resize / 面板宽度
2. 仓库管理
   - add/edit/remove repo
   - detect provider
   - scan project files
   - refresh branches
3. 发布执行流
   - 构造 spec
   - 环境检查
   - 执行 publish
   - cancel publish
   - 输出日志处理
4. 诊断 / 历史
   - history filter
   - failure group
   - rerun checklist
   - handoff snippet
   - issue draft
5. 导出能力
   - snapshot
   - failure bundle
   - history export
   - diagnostics index
6. UI 组装
   - 各种 Card / Dialog / toolbar / section 拼接

### 前端目标结构
目标是把 `App.tsx` 缩成壳层，只负责：
- 读取 persistent app state
- 组装几个 domain hook
- 拼三栏 layout
- 打开/关闭几个 dialog
- 把 action 往下传

### 当前阶段判断（2026-03-14）
当前这一波 frontend shell-collapse 已经先后完成：
- publish cards props assembly 收口
- `PublishContentSection` / `MainContentShell` / `SidebarPanelShell` 拆出
- history/diagnostics/dialogs/layout/repository/project execution/project shell 等本地组合状态拆成独立 hooks

当前 `src/App.tsx` 已降到约 `928` 行，说明“把纯 view wiring 和壳层状态剥离出去”这条路已经接近边际收益下降。
接下来应优先判断：
- 是否还存在一块不碰 publish runtime、且可以独立验证的薄切片
- 如果没有，就把这一波视为阶段性完成，不要为了追逐行数继续把 publish execution orchestration 生硬切碎
- 当前更推荐把剩余逻辑视为 publish runtime 邻接层，先做边界与进入条件判断，再决定是否进入下一阶段

### 当前停止边界（2026-03-14）
本轮 frontend shell-collapse 暂停在这里：
- 可以继续拆，但剩余大头已经不是纯 view wiring，而是多个 domain hook 之间的 orchestration glue
- 继续下刀最可能触碰：`usePublishExecution`、`useProfiles`、`useRepositoryActions`、`useDiagnosticsExports`、`useRerunFlow` 之间的高耦合边界
- 因此，除非出现新的低风险切片，否则不再把“继续缩短 App.tsx”本身当成目标

### 下一阶段进入条件（建议）
在进入 publish runtime 邻接层之前，先满足这 4 条：
1. 能明确指出候选切片的单一入口点（例如只从 `usePublishExecution` 邻接层进入）
2. 能明确列出本刀不碰的边界（例如先不动 `src-tauri/src/commands/mod.rs` / `publish.rs`）
3. 能定义单 commit 可回滚的 done_definition，而不是多处混合修补
4. 三条验证命令仍作为每刀硬门槛：`pnpm typecheck`、`pnpm test`、`cargo check`

### 当前推荐入口（2026-03-14）
如果进入下一阶段，首刀优先从 `usePublishExecution` 邻接层进入，而不是：
- 直接改 `publish.rs`
- 同时碰 `useProfiles` / `useRepositoryActions` / dialogs wiring

推荐原因：
- `App.tsx` 剩余大头最明显地贴近 publish orchestration
- 可以把“进入点”限制在一个高耦合面上，避免多域同时变更
- 仍能维持单 commit 回滚与三条验证门槛

### 第一刀 entry slice（建议）
把第一刀定义成：
- 只处理 `App.tsx -> usePublishExecution` 的参数装配 / 调用面边界
- 不改 `usePublishExecution` 内部执行语义
- 不改 `publish.rs` / `commands/mod.rs`
- 不同时碰 profile、repository、dialog 三个相邻高耦合域

建议先把这组参数看成第一刀的 contract surface：
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

建议再把它们分两层看：
- 核心输入状态层：`selectedRepoId`、`selectedRepo`、`activeProviderId`、`activeProviderParameters`、`selectedPreset`、`isCustomMode`、`customConfig`、`defaultOutputDir`、`projectInfo`
- 可先收口的回调/副作用层：`pushRecentConfig`、`openEnvironmentDialog`、`setEnvironmentLastResult`、`buildExecutionRecord`、`persistExecutionRecord`

### 第一刀建议变更集（2026-03-14）
如果继续推进，第一刀建议只做这件事：
- 先把“可先收口的回调/副作用层”压成较稳定的 publish-execution call surface
- 暂不移动“核心输入状态层”的直接装配位置
- 这样可以让第一刀仍然满足：
  - 单点进入：`App.tsx -> usePublishExecution`
  - 单点回滚：只回滚 call-surface 变更
  - 行为不变：不改 publish spec / cancel / log streaming / environment gate

更具体地说，第一刀若落代码，推荐形式是：
- 新增一个更窄的 publish-execution call-surface helper / composition helper
- 让它只聚合 `pushRecentConfig`、`openEnvironmentDialog`、`setEnvironmentLastResult`、`buildExecutionRecord`、`persistExecutionRecord`
- 继续让 `App.tsx` 直接提供 repo/provider/preset/config/projectInfo 这组核心输入状态

### 第一刀实现入口（建议）
若进入实现，建议采用这条最窄路径：
1. 在前端 hooks/composition 层新增 helper（优先 `usePublishExecutionCallSurface` 命名）
2. 由该 helper 聚合 5 个回调/副作用面，输出一个较窄的 call-surface object
3. `App.tsx` 继续负责核心输入状态装配，只把 call-surface object 交给 `usePublishExecution`
4. `usePublishExecution` 第一刀仅接受更稳定的参数对象，不改内部行为分支

### 第一刀实现草案边界（建议）
为了避免越界，第一刀代码实现建议再加这 4 条硬约束：
- helper 文件优先落在 `src/hooks/usePublishExecutionCallSurface.ts`
- helper 不接收 repo/provider/preset/config/projectInfo 这组核心输入状态
- `usePublishExecution` 只允许做参数签名调整、解构位置调整、变量改名等接线型改动
- 任何会触碰 invoke 顺序、cancel 路径、日志流、environment gate、publish spec 构造的修改，都视为超出第一刀边界

### 第一刀实现 brief（建议）
如果进入真正实现，建议按这个最小变更集执行：
1. 新增 `src/hooks/usePublishExecutionCallSurface.ts`
2. 让它只接收 `pushRecentConfig`、`openEnvironmentDialog`、`setEnvironmentLastResult`、`buildExecutionRecord`、`persistExecutionRecord`
3. 让 `App.tsx` 把这 5 个回调聚合后传给 `usePublishExecution`
4. 让 `usePublishExecution` 改成接收更窄的 call-surface object，而不是分散接收这 5 个回调
5. 除此之外不做任何 runtime 行为改动

### 第一刀开工前 checklist（建议）
真正开工前，再逐项确认：
- helper 没有偷偷接入 repo/provider/preset/config/projectInfo 这组核心输入状态
- `usePublishExecution` diff 只涉及签名、解构、引用位置，不涉及执行时序和行为分支
- `App.tsx` 只减少 publish call-surface 噪声，不引入新的中间状态源
- 验证门槛不降级：`pnpm typecheck`、`pnpm test`、`cargo check`
- 人工核对三条主路径：publish success / failure / cancelled 体感一致

### 第一刀最终开工结论（建议）
把 `PR-E.P45` 定义成一个显式决策点：
- 如果 checklist 全部满足，则允许进入真正代码实现，落第一刀 `usePublishExecutionCallSurface`
- 如果 checklist 任一项无法满足，则继续停留在文档边界阶段，不进入 runtime-adjacent code slice
- 换句话说，`PR-E.P45` 不是默认“继续做代码”，而是默认先做 go/no-go 判断

### 当前阶段性收口结论（2026-03-14）
到这里为止：
- frontend shell-collapse wave 已完成阶段性收口
- runtime-adjacent 第一刀的入口、contract surface、参数分层、implementation brief、checklist、go/no-go 条件也已全部写清
- 因此，除非人类明确要求进入第一刀代码实现，否则不应再继续机械扩写 planning slices
- 当前最准确的状态表述应为：`ready for go/no-go decision`
- 进一步的执行规则是：没有明确 `go`，就不进入 `usePublishExecutionCallSurface` 代码实现；没有明确 `no-go`，就不销毁当前结论
- 2026-03-15 的后续 repo fact check 已把当前默认结论收敛为：`no-go for PR-E.P57`。原因不是 planning 不够，而是剩余候选已明显集中在 `runPublishWithSpec` / `executePublish` / `cancelPublish` orchestration；继续推进会开始越过“低风险纯接线/纯状态”边界，进入 runtime-adjacent relocation

如果这 4 条不能同时成立，就说明还没到可以安全进 runtime-adjacent phase 的时点。

### 第一刀：先抽纯函数
#### 1) invoke error / failure analysis helpers
从 `App.tsx` 先搬走：
- `analyzeBranchRefreshFailure`
- `analyzeProviderDetectFailure`
- `analyzeProjectScanFailure`
- `analyzePublishExecutionFailure`
- `extractInvokeErrorMessage`
- `extractInvokeErrorCode`

建议落点：
- `src/lib/tauri/invokeErrors.ts`

#### 2) history filter 相关纯逻辑
搬走：
- `filterExecutionHistory`
- `normalizePathForMatch`
- `isRecordInRepository`

建议落点：
- `src/features/history/utils/historyFilters.ts`

#### 3) path utils
搬走：
- `remapPathPrefix`

建议落点：
- `src/features/repository/utils/pathUtils.ts`

### 第二刀：抽操作 hook
#### `useRepositoryActions.ts`
搬入：
- `handleAddRepo`
- `handleRemoveRepo`
- `handleEditRepo`
- `handleDetectRepoProvider`
- `handleScanProjectFiles`
- `handleRefreshRepoBranches`

#### `usePublishExecution.ts`
搬入：
- `runPublishWithSpec`
- `executePublish`
- `cancelPublish`
- `buildExecutionRecord`
- `persistExecutionRecord`

#### `useDiagnosticsExports.ts`
搬入：
- `exportExecutionSnapshot`
- `exportFailureGroupBundle`
- `exportExecutionHistory`
- `exportDailyTriageReport`
- `exportDiagnosticsIndex`

#### `useProfiles.ts`
搬入：
- `loadProfiles`
- `handleSelectProfileFromPanel`
- `handleQuickCreateProfileSave`
- `handleDeleteProfileFromPanel`
- `handleLoadProfile`

### 第三刀：抽 UI section
建议拆分：
- `DotnetPublishCard.tsx`
  - dotnet preset/custom UI
  - publish preview command
  - execute/cancel 按钮
- `GenericProviderPublishCard.tsx`
  - 非 dotnet provider 参数编辑
  - `ParameterEditor`
  - 环境检查入口
  - execute/cancel
- `OutputLogCard.tsx`
  - publish result
  - output log
  - snapshot export
  - artifact actions
  - release checklist 按钮
- `FailureGroupsCard.tsx`
  - failure group 列表
  - copy signature
  - rerun representative
  - open snapshot
- `FailureGroupDetailCard.tsx`
  - selected failure group 详情
  - issue draft
  - export bundle
  - record-level actions
- `ExecutionHistoryCard.tsx`
  - history filter
  - presets
  - daily triage preset
  - export history
  - diagnostics index
  - rerun / open snapshot / copy handoff

---

## 二、后端拆分方案

### commands.rs 当前混合的职责
至少包含：
- repository/project 扫描
- git branch / connectivity
- publish execution / cancel / log stream
- updater
- provider schema / command import
- diagnostics/export markdown/html/csv
- config import/export
- environment check / apply fix
- artifact package / sign

### 后端目标结构
先走中等粒度拆分，不一开始拆太碎。

#### `repository.rs`
放入：
- `detect_repository_provider`
- `check_repository_branch_connectivity`
- `scan_repository_branches`
- `scan_project_files`
- `scan_project`

helpers：
- `find_project_root`
- `find_project_file`
- `scan_publish_profiles`
- `detect_provider_from_path`
- git/path error classify helpers

#### `publish.rs`
最核心、也最晚拆。

放入：
- `execute_publish`
- `execute_provider_publish`
- `cancel_provider_publish`

以及内部执行辅助：
- `RunningExecution`
- `RUNNING_EXECUTION`
- `build_dotnet_spec_from_config`
- `execute_publish_spec`
- `build_publish_session_id`
- `emit_publish_log`
- `collect_log_lines`
- `read_stream_lines`
- `clear_running_execution`
- `resolve_plan_command`
- `resolve_java_program`
- `resolve_working_dir`
- `infer_output_dir`
- `count_output_files`

#### `provider.rs`
放入：
- `list_providers`
- `get_provider_schema`
- `import_from_command`

#### `updater.rs`
放入：
- `get_updater_help_paths`
- `get_updater_config_health`
- `open_updater_help`
- `check_update`
- `install_update`
- `get_current_version`
- `get_shortcuts_help`

以及：
- `UpdateInfo`
- `UpdaterHelpPaths`
- `UpdaterConfigHealth`
- `map_updater_error`
- `resolve_updater_help_paths`

#### `export.rs`
最适合优先拆的低风险大块。

放入：
- `export_preflight_report`
- `export_execution_snapshot`
- `export_failure_group_bundle`
- `export_execution_history`
- `export_diagnostics_index`
- `open_execution_snapshot`

以及 render helpers：
- `render_preflight_markdown`
- `render_execution_snapshot_markdown`
- `render_failure_group_bundle_markdown`
- `render_execution_history_csv`
- `render_diagnostics_index_markdown`
- `render_diagnostics_index_html`
- `find_latest_snapshot_in_output_dir`
- `markdown_link`
- `html_escape`
- `csv_escape`

#### `config.rs`
放入：
- `export_config`
- `import_config`
- `apply_imported_config`

#### `environment.rs`
放入：
- `run_environment_check`
- `apply_fix`
- `validate_and_parse_fix_command`

#### `artifact.rs`
放入：
- `package_artifact`
- `sign_artifact`

### `commands/mod.rs` 原则
只做两件事：
- 声明子模块
- `pub use` 导出 Tauri command

这样 `lib.rs` 里的 `generate_handler![]` 基本不用大改风格。

---

## 三、推荐拆分顺序

### 后端拆分顺序（低风险 → 高风险）
1. `PR1`：拆 `export.rs`
   - 原因：大量纯字符串/render 逻辑，跨状态最少，回归成本低
2. `PR2`：拆 `updater.rs` + `provider.rs`
   - 原因：逻辑相对独立，与 publish runtime 耦合低
3. `PR3`：拆 `repository.rs`
   - 原因：有 git/path 错误分类，但边界清晰
4. `PR4`：拆 `config.rs` + `environment.rs` + `artifact.rs`
   - 原因：命令独立性强
5. `PR5`：最后拆 `publish.rs`
   - 原因：有运行态单例、cancel/log streaming，风险最高

### 前端拆分顺序
1. `PR1`：抽纯函数
   - invoke error helpers
   - history filter utils
   - path utils
2. `PR2`：抽 storage / profile / preset 逻辑
   - `useRecentConfigs`
   - `useProfiles`
3. `PR3`：抽发布执行 hook
   - `usePublishExecution`
4. `PR4`：抽 diagnostics/history hook
   - `useFailureGroups`
   - `useDiagnosticsExports`
   - `useExecutionHistory`
5. `PR5`：抽 UI 卡片
   - `OutputLogCard`
   - `FailureGroupsCard`
   - `ExecutionHistoryCard`
6. `PR6`：最后把 `App.tsx` 缩成壳层
   - layout + hooks compose + dialog wiring

---

## 四、这次重构里不建议做的事
- 不要顺手上 Zustand / Redux
- 不要顺手改 UI 结构
- 不要顺手改 command 协议名
- 不要顺手重写 store
- 不要把 dotnet / 非 dotnet 流程一起统一重做
- 不要一边拆一边补大型新功能

否则会从“结构重构”变成“全线变更”。

---

## 五、验收标准

### 前端验收
- `App.tsx` 不再包含大量纯业务逻辑
- Tauri `invoke()` 不再散落在多个 section 里，尽量收口到 `api/hook`
- 右侧 5 大块 section 已独立组件化
- 发布、导出、rerun、history 筛选行为不变

### 后端验收
- `commands.rs` 不再是单文件巨石
- 各 command 按领域可定位
- render/export helper 与运行态 publish 逻辑分离
- 单元测试仍在对应模块旁边

---

## 六、建议的第一刀（可合并 PR）

### PR-A：纯拆分，不改行为
#### 前端
- `src/lib/tauri/invokeErrors.ts`
- `src/features/history/utils/historyFilters.ts`
- `src/features/repository/utils/pathUtils.ts`

#### 后端
- 新建 `src-tauri/src/commands/export.rs`
- 把所有 export/render/open snapshot 相关逻辑搬进去
- `commands/mod.rs` 做 re-export

### 这个 PR 的特点
- 风险最低
- 对 UI 几乎零影响
- reviewer 最容易过
- 合完之后，结构马上会清爽很多

---

## 七、主张 / 优先级判断
如果只问“先拆哪儿最值”：

### 第一优先级
- 拆 backend 的 export 块
- 拆 frontend 的纯函数和 export/history 逻辑
- 再拆 publish runtime

原因：
- 最快减少文件体积
- 最不容易把主流程拆坏

## 当前建议的下一步
- 先做第 1 个 PR：按低风险路线开刀
- 如有需要，再继续细化：
  - 更具体的 PR 列表（每个 PR 改哪些文件）
  - 目录级别的最终文件树
  - 第一版重构补丁
