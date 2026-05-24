# ledger-v3-activity-isolation roadmap

## Goal
- 六层执行系统资源从「按层分桶」→「按活动隔离」
- ACTIVE.md: 474→50 行薄索引
- ~12 checker + ~6 文档同步适配

## Contract reference
- contracts/ledger-v3-activity-isolation-contract.md

## Validation baseline
- `run_execution_system_checks.py checks` 全绿
- `run_execution_system_full_tests.py` 全绿
- 恢复链可走通

## Phases

### Phase 0 — Governance setup (G)
- objective: 为本次重构建立六层治理链
- dependencies: none
- outputs: demand + contract + roadmap + tasks + ACTIVE entry
- exit criteria: 治理链可被 checker 识别
- decomposition_strategy: 单 slice 完成全部治理文件
- recommended_wave_shape: serial
- risks: low

### Phase 1 — File migration (M)
- objective: 将所有 activity 资源从按层目录迁移到 `activities/<id>/` 目录
- dependencies: Phase 0
- outputs: `activities/` 目录含 8 个 activity 子目录
- exit criteria: 所有资源归位，旧目录清空
- decomposition_strategy: M-1 先提取卡片模板，M-2~M-8 并行迁移各 activity，M-9 清理
- recommended_wave_shape: mixed (M-1 串行 → M-2~M-8 并行 → M-9 串行)
- risks: medium（大量文件移动，需保证不丢失数据）

### Phase 2 — ACTIVE.md rewrite (A)
- objective: 重写 ACTIVE.md 为 ~50 行薄索引
- dependencies: Phase 1
- outputs: 新 ACTIVE.md
- exit criteria: checker 可通过新 ACTIVE.md
- decomposition_strategy: 单 slice
- recommended_wave_shape: serial
- risks: medium（ACTIVE.md 是唯一真相入口）

### Phase 3 — Checker/script adaptation (C)
- objective: ~12 个脚本适配新路径结构
- dependencies: Phase 2
- outputs: 更新后的 checker 脚本
- exit criteria: 所有 checker 绿
- decomposition_strategy: C-1 先适配核心 parser，C-2~C-5 并行适配其他 checker，C-6 适配 runner
- recommended_wave_shape: mixed
- risks: high（checker 是质量 gate，改错会导致假阳性/假阴性）

### Phase 4 — Spec/doc sync (D)
- objective: 6 个规范文档同步新结构
- dependencies: Phase 3
- outputs: 更新后的文档
- exit criteria: 文档描述与实际情况一致
- decomposition_strategy: D-1~D-6 全并行
- recommended_wave_shape: parallel-wave
- risks: low

### Phase 5 — Full validation (V)
- objective: 全量验证
- dependencies: Phase 4
- outputs: 验证报告
- exit criteria: 全绿 + 恢复链走通
- decomposition_strategy: V-1~V-4 全并行
- recommended_wave_shape: parallel-wave
- risks: low

## Current recommended phase
- Phase 0
