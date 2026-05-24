# active ledger v2 tasks

## Current phase
- Phase 6 - Real multi-activity validation (`AL-E / Task E2 - finalize docs and acceptance`)

## PR queue

### AL-A - schema v2 skeleton
- goal:
  - 先把 `ACTIVE.md` 升级成三层账本结构，但仍保持单活动兼容运行
- scope:
  - ledger meta
  - workspace rules
  - activity index
  - activity blocks
- files:
  - `<plugin-root>/ACTIVE.md`
  - `<plugin-root>/skills/six-layer-execution-system/SKILL.md`
- validation:
  - `python3 scripts/check_active_consistency.py`
  - 人工检查 `current_focus_activity_id` 与当前 activity 对齐
- done_definition:
  - `ACTIVE.md` 已升级为三层账本结构
  - 当前唯一活动以 `Activity` block 形式存在
  - 不再依赖全局散落的单任务字段
- risk:
  - 中：结构变了，但旧脚本还没统一走 parser

#### Task A1 - migrate ACTIVE.md to ledger skeleton
- objective:
  - 把当前 `ACTIVE.md` 改造成三层账本模型的骨架
- files:
  - `<plugin-root>/ACTIVE.md`
- steps:
  - 新增 `Ledger meta`
  - 新增 `Workspace rules`
  - 新增 `Activity index`
  - 把当前 focus roadmap 包成单个 `Activity` block
  - 增加 `activity_id` / `type` / `autopilot` / `priority`
  - 让 `current_focus_activity_id` 显式指向该 activity
- validation:
  - `python3 scripts/check_active_consistency.py`
- done_definition:
  - 账本已分层
  - 当前 focus activity 可明确定位

#### Task A2 - update recovery rules for ledger v2
- objective:
  - 让 plugin skill 中的恢复说明匹配新账本结构
- files:
  - `<plugin-root>/skills/six-layer-execution-system/SKILL.md`
- steps:
  - 把“先读 ACTIVE”改成“先读 ledger meta，再读 focus activity”
  - 补充 focus-first 语义
  - 补充 activity index / activity type 的恢复说明
- validation:
  - 人工走读无冲突
- done_definition:
  - 文档规则与账本结构一致

### AL-B - unified parser
- goal:
  - 提供 `active_ledger.py` 统一解析接口
- scope:
  - 读取 ledger meta
  - 读取 activity index
  - 获取 current focus
  - typed activity access
- files:
  - `<plugin-root>/scripts/active_ledger.py`
  - `<plugin-root>/scripts/check_active_consistency.py`
- validation:
  - `python3 -m py_compile scripts/active_ledger.py`
- done_definition:
  - 脚本不再直接靠首个匹配字段找当前任务
- risk:
  - Markdown parser 边界问题

#### Task B1 - implement parser skeleton
- objective:
  - 实现 ledger meta / activity block / focus access 的最小 parser
- files:
  - `<plugin-root>/scripts/active_ledger.py`
- steps:
  - 定义数据结构
  - 实现 ledger meta 解析
  - 实现 activity blocks 解析
  - 实现 `get_current_focus_activity()`
- validation:
  - `python3 -m py_compile scripts/active_ledger.py`
- done_definition:
  - 可稳定获取 focus activity

### AL-C - checker v2
- goal:
  - 一致性检查升级为 ledger / activity / focus 三层
- scope:
  - 多活动 schema 校验
  - focus activity 严格校验
- files:
  - `<plugin-root>/scripts/check_active_consistency.py`
- validation:
  - checker 输出能带 activity_id
- done_definition:
  - 多活动下一致性检查可用
- risk:
  - 规则过严

### AL-D - activity-aware closeout
- goal:
  - 让 closeout 与 handoff 支持 `activity_id`
- scope:
  - `complete_slice.py`
  - closeout / payload scripts
- validation:
  - payload 针对 focus activity 生成
- done_definition:
  - roadmap closeout 不串 activity
- risk:
  - 历史状态迁移

### AL-E - real multi-activity validation
- goal:
  - 加入第二 activity 验证真实运行
- scope:
  - roadmap + simple 或 waiting activity 共存
- validation:
  - focus / recovery / checker / handoff 行为都正确
- done_definition:
  - 真正多活动跑通
- risk:
  - 暴露遗漏的单活动假设
