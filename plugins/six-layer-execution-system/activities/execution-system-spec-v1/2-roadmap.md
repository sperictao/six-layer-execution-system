# execution system spec v1 roadmap

## Goal
- 将 `execution-system-spec-v1` 从“文档规范”推进为“可实施、可迁移、可验证”的执行系统。
- 在不破坏当前运行稳定性的前提下，逐步把现有项目与运行规则收敛到统一规范。

## Contract reference
- `docs/execution-system-spec-v1.md`
- `contracts/execution-system-contract.md`

## Validation baseline
- `python3 scripts/check_active_consistency.py`
- 文档与模板之间无明显冲突
- 迁移后不引入双重运行时真相

## Phases

### Phase 6 - First enforcement implementation prep
- objective:
  - 为第一条真正准备落地的 checker/workflow 规则定义实现切片
- dependencies:
  - Phase 5
- outputs:
  - 第一条 enforcement implementation slice
  - 明确的字段检查范围、失败模式、恢复路径
- exit criteria:
  - 第一条 checker/workflow 已从 backlog 候选变成可执行 implementation slice
- risks:
  - 过早把设计规则写死到实现


### Phase 1 - Spec hardening
- objective:
  - 固化执行系统规范与模板，使其成为后续迁移的唯一设计基线
- dependencies:
  - `docs/execution-system-spec-v1.md`
  - `references/templates.md`
- outputs:
  - 明确 contract / roadmap / tasks / ACTIVE / decisions / memory 的职责边界
  - 明确 activity schema 与 completion protocol
- exit criteria:
  - 总规范已成稿
  - 模板可直接被真实项目复用
  - 现有 active-ledger-v2 与 execution-system contract 无明显冲突
- risks:
  - 规范过宽，无法真正约束后续迁移

### Phase 2 - Runtime truth slimming
- objective:
  - 将 `ACTIVE.md` 从“过厚运行手册”收紧为“最小完备运行时真相”
- dependencies:
  - Phase 1
- outputs:
  - `ACTIVE.md` 保留 ledger meta / runtime rules / activity cards / pointers
  - 过长说明迁移到 spec 文档
- exit criteria:
  - ACTIVE 不再承载大段制度性说明
  - 仍可完整恢复当前 focus activity
- risks:
  - 过度瘦身导致恢复所需信息丢失

### Phase 3 - Execution-system template migration
- objective:
  - 用新模板收紧 execution-system 自身样例的 roadmap/tasks 结构
- dependencies:
  - Phase 1
  - Phase 2 部分完成或边做边对齐
- outputs:
  - `execution-system-testing` 的 roadmap/tasks 对齐到新模板
  - phase / slice / rollback / validation 关系更明确
- exit criteria:
  - 至少一个 execution-system-owned 样例完成模板迁移
  - phase 和 slice 的边界比旧版更清晰
- risks:
  - 迁移时引入双重表述或新旧字段并存

### Phase 4 - Decision layer landing
- objective:
  - 为执行系统补上正式 decisions 层
- dependencies:
  - Phase 1
- outputs:
  - `decisions/` 目录与决策模板启用
  - 至少补两条关键决策样例
- exit criteria:
  - 长期约束变化与关键取舍不再只漂浮在 ACTIVE / memory 中
- risks:
  - decision 粒度失控，变成第二份 memory

### Phase 5 - Validation and migration policy
- objective:
  - 补齐实施后的检查口径与迁移准则
- dependencies:
  - Phases 2-4
- outputs:
  - 明确哪些规则仍靠文档约束，哪些应进入 checker / workflow
  - 给出逐步迁移策略
- exit criteria:
  - 系统从“文档规范”升级为“可持续执行规范”
- risks:
  - 规范与脚本能力脱节

## Current recommended phase
- Phase 7 - Maintenance mode planning (`ES-F.F33` should freeze the first thin integration plan for acceptance / summary / closeout orchestration)
