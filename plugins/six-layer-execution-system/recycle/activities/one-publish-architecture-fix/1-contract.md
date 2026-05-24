# one-publish 架构修复 contract

## Goal
将 one-publish 从进化遗留的沙漏架构（Provider 抽象好，但上层状态管理和下层遗留执行路径未跟上）改造为前后一致、可扩展、可测试的结构，消除全部 10 个已识别的架构问题。

## Scope
- 后端: `src-tauri/src/` — Rust 命令层、Provider 注册、执行路径、持久化
- 前端: `src/` — 状态管理、组件拆分、hook 解耦、lib 目录重组
- 仓库根: `docs/`、配置文件、构建脚本（仅在必要时调整引用）

## Invariants
1. **行为不变**: 所有外部可观察行为（Tauri IPC 契约、UI 交互、持久化格式）不改变
2. **类型安全不减**: TypeScript strict mode + Rust 编译检查，不引入 `any` 或 `unsafe`
3. **每个 commit 独立可回滚**: 任意一个 slice 的 revert 不应破坏其他 slice
4. **Provider trait 接口不变**: 6 个方法的签名和语义保持稳定
5. **测试只增不减**: 不移除任何现有测试；不降低任何覆盖率阈值

## Non-goals
- 不添加新功能或新 UI
- 不修改 Provider trait 接口或语义
- 不迁移持久化格式（`~/.one-publish/config.json` schema 不变）
- 不引入新的构建工具或流程（保持 pnpm + Vite + Tauri 不变）
- 不调整 CSS/Tailwind 设计令牌
- 不改变 Tauri 插件配置或窗口行为

## Forbidden moves
1. **禁止大规模一次性重写**: 每次只改一个关注点，不混合多种重构
2. **禁止无测试的重构**: 每个 slice 必须有对应的 typecheck/lint/compile 验证
3. **禁止删除 deprecated 代码时有功能回归**: 必须先确保新路径完全覆盖旧路径的所有用例
4. **禁止在重构中引入新的依赖**: 除非需求分析阶段已明确论证（如 Zustand）
5. **禁止修改 `generated/tauri-contracts.ts`**（此文件由 Rust `ts-rs` 自动生成）
6. **禁止触碰** `.trellis/` 目录（Trellis 治理文件独立运作）

## Allowed tradeoffs
- 允许引入 1 个轻量状态管理库（Zustand 或 Jotai，< 2KB gzip）以替代手动 props drilling
- 允许将大的 hook 拆分为多个小 hook，增加文件数但降低单文件复杂度
- 允许在后端增加一个简单的 Tauri command wrapper 中间件层（无需引入框架）
- 允许在不改变语义的前提下重命名内部类型/函数以消除 dotnet 偏见

## Validation baseline
- **类型系统**: `pnpm typecheck`（前端）、`cargo check`（后端）
- **Lint**: `cargo clippy -- -D warnings`
- **测试**: `pnpm vitest run`（前端）、`cargo test`（后端）
- **冒烟**: 启动应用 → 扫描项目 → 执行发布 → 验证输出

## Completion philosophy
- **渐进交付**: 每个 Phase 完成后即可停止，后续 Phase 可独立决策是否继续
- **P0 是阻断性修复**: 移除双路径执行是后续所有重构的前提
- **每个 slice 都是「可以在这里停止」的 checkpoint**
- **完成 ≠ 完美**: 完成标准是问题已修复 + 验证通过，不是代码达到理想形态

## Decomposition Guardrails
- allowed_slice_shapes:
  - 单文件删除/重命名（如移除 deprecated module）
  - 单文件拆分（如拆大 hook 为多个小 hook）
  - 单模块抽取（如提取新的 lib/ 子目录）
  - 单层薄封装（如增加 command middleware wrapper）
- forbidden_slice_shapes:
  - 跨前后端的混合 slice（前端改动和后端改动必须分属不同 slice）
  - 同时修改接口和实现的 slice（必须先稳定接口，再迁移实现）
  - 引入新依赖 + 使用新依赖的混合 slice（先引入并验证，再迁移使用）
- preferred_dependency_shape:
  - P0 → P1 → P2 是硬序列依赖
  - P0 内部: P0-1 → P0-2 → P0-3 有强依赖（先清旧路再修类型再拆组件）
  - P1 内部: 4 个 slice 无相互依赖，可全并行
  - P2 内部: P2-1（中间件）先于 P2-2/P2-3（动态发现/事件总线）
- parallelism_policy:
  - 同一 Phase 内、无写冲突的 slice 默认并行执行
  - 跨 Phase 的 slice 不得并行（P1 依赖 P0 的变更结果）
- integration_constraints:
  - 每个 wave 完成后运行全量验证再进入下一 wave
  - 并行 wave 的集成步骤由父级执行路径显式承担

## Review triggers
- 任何 slice 导致 typecheck 失败 → 暂停，修复后再继续
- 任何 slice 导致测试失败 → 暂停，定位根因
- 发现新的未记录问题 → 记录到 decision log，不阻塞当前 slice
- P0 全量测试未通过 → 不得进入 P1
- P1 冒烟测试未通过 → 不得进入 P2
