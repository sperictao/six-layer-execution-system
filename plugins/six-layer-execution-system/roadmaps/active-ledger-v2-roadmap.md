# active ledger v2 roadmap

## Goal
- 把当前单活动 `ACTIVE.md` 升级成支持多活动的三层账本模型。
- 保持 `ACTIVE.md` 仍是唯一运行时真相源。
- 让 heartbeat、consistency check、closeout、notification 都能在多活动下稳定工作。

## Constraints / non-goals
- 不恢复 `SESSION-STATE.md`
- 不把运行时状态拆到多个平行状态文件
- 不直接切纯 JSON/YAML 作为主账本
- 不让 heartbeat 默认在多个活动之间自由切换
- 第一阶段先升级 schema 与解析层，不抢先改所有通知链路细节

## Validation baseline
- `python3 scripts/check_active_consistency.py`
- `python3 -m py_compile scripts/active_ledger.py`
- 手工校验：当前 focus activity 可被稳定解析

## Phases

### Phase 1 - Ledger schema v2
- objective:
  - 定义三层账本模型并把 `ACTIVE.md` 升级为 v2 结构
- outputs:
  - `ACTIVE.md` 新增 ledger meta / focus index / activity index / activities 四段结构
  - 当前唯一活动迁移成 `Activity` block
  - 保持单活动运行兼容
- exit criteria:
  - `ACTIVE.md` 已采用三层账本模型
  - 当前 focus activity 可明确定位
  - 旧的单活动字段不再散落在文件全局
- validation:
  - `check_active_consistency.py` 能读取 focus activity
- risks:
  - 新结构落地后，旧脚本若仍按首个字段匹配会读错

### Phase 2 - Unified parser
- objective:
  - 提供统一解析层，结束脚本直接 grep `ACTIVE.md`
- outputs:
  - `scripts/active_ledger.py`
  - 统一接口：ledger meta / activity list / current focus / typed activity access
- exit criteria:
  - 解析器能稳定返回当前 focus activity
  - 脚本不再依赖“第一个 `- path:`”语义
- validation:
  - `python3 -m py_compile scripts/active_ledger.py`
  - 手工 smoke test：列出 focus / activity ids / roadmap fields
- risks:
  - Markdown 解析边界与字段命名耦合

### Phase 3 - Consistency checker v2
- objective:
  - 把一致性校验升级为 ledger 级 + activity 级 + focus 级
- outputs:
  - 改造后的 `scripts/check_active_consistency.py`
- exit criteria:
  - 多活动下能定位具体 activity 的问题
  - focus activity 漂移时能精确告警
- validation:
  - checker 正常通过当前 focus
  - checker 能对缺字段 activity 报清晰错误
- risks:
  - 规则太严导致噪音过高

### Phase 4 - Activity-aware closeout & notification
- objective:
  - 让 closeout / notification / dedupe 支持多活动，不串线
- outputs:
  - `complete_slice.sh` 与通知链路脚本支持 `activity_id`
  - dedupe key 升级为 `activity_id + completed_slice_id + commit`
- exit criteria:
  - roadmap activity 的通知链路不再依赖全文件唯一任务假设
- validation:
  - prepare / payload / ack 走 focus activity
- risks:
  - 历史 pending / inflight 状态迁移

### Phase 5 - Focus-first heartbeat semantics
- objective:
  - 在多活动下保持 heartbeat 可控，只推进 focus
- outputs:
  - plugin skill 中的 heartbeat / recovery 语义升级为 `focus-first`
- exit criteria:
  - heartbeat 默认只推进 focus activity
  - blocked / waiting activity 不会误跑
- validation:
  - 手工走读规则与 recovery 行为一致
- risks:
  - 如果切换策略不清，会产生预期差

### Phase 6 - Real multi-activity validation
- objective:
  - 引入第二个真实 activity，验证恢复/通知/heartbeat/校验全链路
- outputs:
  - 至少两个并存的 activity
- exit criteria:
  - 可同时容纳 roadmap + simple / waiting activity
- validation:
  - 恢复问答、focus 切换、checker、closeout 全通过
- risks:
  - 暴露遗漏的单活动假设

## Dependency notes
- Phase 1 是基础，Phase 2 之后才能安全放开真正多活动
- Phase 4 依赖 Phase 2/3 的 typed activity access
- Phase 5 要以 Phase 2 的 focus 解析为前提

## Current recommended phase
- Phase 6 - Real multi-activity validation
