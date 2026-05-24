# one-publish 架构修复 roadmap

## Goal
按 P0 → P1 → P2 顺序修复 one-publish 的全部 10 个架构问题，消除沙漏架构，建立前后一致的可扩展结构。

## Contract reference
- contracts/one-publish-architecture-fix-contract.md

## Validation baseline
- 每 slice: `pnpm typecheck` + `cargo check && cargo clippy`
- Phase 完成: 全量测试 + 冒烟验证

## Phases

### Phase 0 — 架构债务清理 (P0)
- objective:
  - 移除废弃的双路径执行系统，消除 dotnet 特化类型污染，提取前端状态编排层
  - 这是所有后续重构的前提——不清旧路，新路无法铺开
- dependencies:
  - 无外部依赖。P0 内部有强序列依赖: P0-1 → P0-2 → P0-3
- outputs:
  - `src-tauri/src/publish.rs` 移除
  - `lib.rs` 中 `execute_publish` 命令注销
  - `PublishConfig` 类型去 dotnet 化
  - `App.tsx` 状态编排提取为 `useAppBoot.ts`
- exit criteria:
  - `execute_publish` 路径完全移除，`execute_provider_publish` 成为唯一执行路径
  - 通用执行路径中不再引用 dotnet 特化字段 (configuration/runtime/framework/self_contained)
  - App.tsx < 200 行，仅负责 UI 壳组合
- decomposition_strategy:
  - 严格串行：必须先移除旧路径，才能安全修改类型，才能安全重构组件
- recommended_wave_shape: `serial`
- risks:
  - 移除 `execute_publish` 时可能遗漏隐藏的调用点（需全局搜索确认）
  - 去 dotnet 化可能影响前端已有的 preset 系统（需保留 dotnet preset 但挪到 provider 层）

### Phase 1 — 代码健康 (P1)
- objective:
  - 拆分超大文件，引入轻量状态管理，消除 props drilling
  - 每个 slice 独立、可并行、可单独回滚
- dependencies:
  - 依赖 P0 完成（类型系统和组件结构已稳定）
- outputs:
  - `usePublishRunner` 拆为 validate/execute/notify 三个 hook
  - `registry.rs` 拆为独立 provider 文件
  - 引入 Zustand 状态管理，消除 App.tsx 的手动 DI
  - `repository.rs` 拆为 scanner/connector/resolver 子模块
- exit criteria:
  - 所有 >500 行的关键文件已拆分到 <300 行
  - 组件 props 传递深度减少（不再经过不关心的中间层）
  - 全量测试通过
- decomposition_strategy:
  - 4 个 slice 完全独立（操作不同文件），可同一 wave 并行
- recommended_wave_shape: `parallel-wave`
- risks:
  - Zustand 引入可能影响现有 hook 的测试（需逐 hook 验证）
  - registry.rs 拆分需要保持 Provider trait 的 dyn 分发语义不变

### Phase 2 — 可扩展性 (P2)
- objective:
  - 建立 Tauri command 中间件层，实现 Provider 动态发现，引入事件总线
  - 使系统从「添加语言需修改核心代码」变为「添加 provider 文件即可」
- dependencies:
  - 依赖 P1 完成（代码结构已稳定，中间件模式有清晰的插入点）
- outputs:
  - 统一 command 中间件（日志、错误分类、追踪）
  - Provider 动态发现机制（目录扫描 + schema JSON 加载）
  - 内部事件总线（发布成功/失败事件解耦通知、历史、tray）
- exit criteria:
  - 所有 Tauri command 经过中间件层
  - 新增 Provider 可通过添加文件 + 重启应用完成（无需重新编译）
  - 发布通知不再通过直接调用实现，改为事件订阅
- decomposition_strategy:
  - P2-1（中间件）先于 P2-2/P2-3
  - P2-2（动态发现）和 P2-3（事件总线）可同 wave 并行
- recommended_wave_shape: `mixed`（先串行建中间件，再并行铺开）
- risks:
  - 中间件层可能引入性能开销（需测量 Tauri IPC 调用延迟变化）
  - 动态发现需要定义清晰的 provider 文件格式规范和安全边界

## Current recommended phase
- 🎉 全部完成！
