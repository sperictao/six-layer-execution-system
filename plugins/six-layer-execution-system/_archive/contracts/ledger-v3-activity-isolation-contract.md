# ledger-v3-activity-isolation contract

## Goal
- 将六层执行系统的资源组织从「按层分桶」重构为「按活动隔离」
- 每个 activity 拥有独立自包含目录
- ACTIVE.md 精简为薄索引表 (~50 行)，仅存 meta + 索引 + focus 快照

## Scope
- 重组 `plugins/six-layer-execution-system/` 内所有文件
- ACTIVE.md 格式 v2→v3
- ~12 个 checker/脚本路径适配
- ~6 个规范/文档同步
- 旧 tasks 单文件拆成新格式（5 个 activity）
- Hermes skill 副本同步

## Invariants
- ACTIVE.md 仍是唯一运行时真相入口
- focus-first 语义不变
- 恢复链必须可工作：ACTIVE.md → card.md → tasks
- 不丢失任何现有数据
- 旧文件保留为归档（`_archive/` 或原地标记），不删除

## Non-goals
- 不改变六层执行语义（demand→contract→roadmap→tasks→ACTIVE）
- 不改变 checker 验证逻辑（只改路径解析）
- 不改变 closeout 协议
- 不改变外部 repo 治理方式
- 不引入新平台层

## Forbidden moves
- 直接删除旧文件而不归档
- 在迁移完成前修改 ACTIVE.md
- 改变 ACTIVE.md focus-first 语义
- 在 checker 未全绿前标记活动完成
- 并行写同一个 card.md

## Allowed tradeoffs
- ACTIVE.md 失去「一眼看完所有活动」的紧凑感 → 换取 per-activity 自包含
- 旧 tasks 单文件格式在迁移中顺便拆为新格式 → 一次性成本
- 简单 activity 目录几乎空（只有 card.md）→ 一致性优先于紧凑性

## Validation baseline
- `run_execution_system_checks.py checks --timeout 60` 全绿
- `run_execution_system_full_tests.py` 全量测试绿
- 所有 card.md 可被 `active_ledger.py` 解析
- 恢复链手工走通

## Completion philosophy
- 全 checker 绿 + 全测试绿 + 恢复链可走通 = 完成

## Decomposition Guardrails
- allowed_slice_shapes:
  - 每个 slice 只操作一种资源类型（文件迁移 / checker 适配 / 文档同步）
  - 每个 slice 自验证（执行后 checker 可通过）
- forbidden_slice_shapes:
  - 混合文件迁移和 checker 逻辑修改
  - 跳过 governance 直接执行
- preferred_dependency_shape:
  - G-1 → M-1 → M-2..M-8（并行）→ M-9 → A-1 → C-1 → C-2..C-5（并行）→ D-1..D-6（并行）→ V-1..V-4（并行）
- parallelism_policy:
  - M-2~M-8：无共享写目标，可全并行
  - C-2~C-5：C-1 先完成，然后可并行
  - D-1~D-6：无共享写目标，可全并行
- integration_constraints:
  - M-9 必须在所有 M-* 完成后执行
  - A-1 必须在 M-9 完成后执行
  - C-1 必须在 A-1 完成后执行

## Review triggers
- 任何 checker 非预期失败
- 恢复链走不通
- ACTIVE.md 与实际文件结构不一致
