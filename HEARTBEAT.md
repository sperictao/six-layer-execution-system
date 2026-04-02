# HEARTBEAT.md

# 分级通知版 heartbeat：低打扰，但该提醒时一定提醒。
# 默认做检查、整理、推进 active；只在达到通知条件时主动发消息。

## Trigger Rule

收到 heartbeat 时，按下面顺序执行；若没有达到通知条件，则回复 `HEARTBEAT_OK`。

- heartbeat 与人工触发必须遵守同一套恢复规则；不得因为是 heartbeat 就跳过 `ACTIVE.md` / focus activity / roadmap/tasks / repo fact check 这些步骤

## Notification Levels

- `P0`：立即提醒
  - 2 小时内日程
  - 真实阻塞
  - 高风险外部动作前确认
  - 关键方向冲突 / 可能导致错误推进
- `P1`：重要提醒
  - roadmap 切片完成
  - 验证通过
  - 自动切换到下一切片
  - 执行策略变化
- `P2`：轻提醒
  - 高价值、低风险的主动补位
  - 明确重复模式，值得自动化
- `P3`：静默
  - 常规扫描
  - 内部整理
  - 未形成新结论的中间推进

## Suppression Rules

- 同类通知 30 分钟内不重复发
- 同一切片未形成新结论不重复汇报
- 23:00-08:00 默认只发 `P0`
- 若只是内部推进、状态未形成新结论，保持静默
- 使用 `memory/heartbeat-state.json` 记录最近检查与最近提醒，避免重复打扰

## 1) Quiet Hours

- 如果当前时间在 23:00-08:00，且没有 `P0` 级事项，直接回复 `HEARTBEAT_OK`

## 2) Calendar Check

- 看未来 24-48 小时内有没有日程
- 如果 2 小时内有事件，触发 `P0`
- 如果没有新变化，不重复提醒

## 3) Active Work Check

- 先运行 `/Users/erictao/source/repos/six-layer-execution-system/scripts/run_execution_system_checks.py`
- 如果统一 checker 套件失败：先定位失败的子命令；若是 `check_active_consistency.py` 失败，先修复 `ACTIVE.md`，未修复前不要对外汇报进度；若是 task-slice checker / smoke 失败，则按当前 execution-system focus 继续修复；若影响继续推进，按 `P0`
- 先读 `ACTIVE.md` 的 ledger meta，再定位 `current_focus_activity_id`，然后读取该 focus activity 对应的 `roadmap_doc` / `tasks_doc`
- 对 heartbeat 来说，这一步与人工收到 `go` / `continue` / `继续` / `resume` / `next` / `start` 时的恢复顺序保持一致：若 `memory/working-buffer.md` 存在，先读它；然后读 `ACTIVE.md`；再读 focus activity card；再读 roadmap/tasks；最后做 repo/workspace fact check，之后才能汇报进度或继续执行
- heartbeat 内的执行规划也必须与人工执行遵守同一套并行调度口径：先识别依赖图，再区分可并行节点与必须串行节点；将无前置依赖、且无写冲突的子任务按同一波次并行处理，待本轮结果全部返回后再统一汇总进入下一轮
- 并行仅适用于读操作、独立分析、或不会触碰同一文件区域 / 同一运行态状态的实现任务；若存在硬依赖链、共享写目标、或后续决策依赖前一步输出，则必须保持串行
- 只有 current focus activity 可以进入自动执行路径；非 focus activities 只用于恢复、提醒、展示状态，不得在 heartbeat 中擅自推进
- 若 `ACTIVE.md` 已声明 execution truth，则 heartbeat 不得仅凭聊天记忆、旧通知或旧 daily note 推断当前任务状态；工作空间执行文件优先于会话推断
- 把当前 focus activity 视为默认执行队列：只有当它 `autopilot=true`、状态允许、且存在明确下一步并可安全推进时，才直接继续做，不等待主人额外催促
- 默认目标不是“推进一小步就停”，而是持续推进当前 focus 的当前切片；切片完成后，更新 `ACTIVE.md` 并自动切到该 roadmap activity 的下一切片
- 如果 current focus 不是可自动推进活动（如 waiting / simple / blocked / autopilot=false），默认不切到别的 activity，除非主人明确改 focus 或未来规则显式允许 fallback
- 只有在出现真实阻塞（缺权限、缺凭据、需求分歧、高风险外部动作）时才停下
- 形成下列结果时决定通知级别：
  - 切片完成 / 验证通过 / 下一切片切换，且通知已入队或已发送 -> `P1`
  - 真实阻塞 / 风险升级 -> `P0`
  - 只有内部推进、未形成结论 -> `P3`
- 如果验证已过但 `/Users/erictao/source/repos/six-layer-execution-system/scripts/check_slice_closeout.py` 未通过：视为切片未收口，不得宣布完成，优先补跑通知链路
- 如果检测到 `memory/notifications-state.json` 中有 pending 通知：先执行 `complete_slice.sh prepare` 或读取既有 inflight，然后通过 `complete_slice.sh payload` 获取标准消息体；该消息体必须来自 `memory/last-slice-closeout.json` 对应的完成事件。`complete_slice.sh prepare` 只允许把 ACTIVE 中的字段当作显式参数传给 closeout 生成器，不允许由通知脚本直接读取 ACTIVE 推导完成对象。发送成功后再 ack 为 sent，避免丢消息或重复
- 如果 `inflight` 中残留未 ack 的通知：优先读取 `memory/last-slice-notification.json` 或 `/Users/erictao/source/repos/six-layer-execution-system/scripts/get_inflight_notification.py` 获取当前 payload；发送失败时执行 `complete_slice.sh fail` 回滚，发送成功时执行 `complete_slice.sh ack <dedupe_key>`

## 4) Memory Hygiene

- 读今天的 `memory/YYYY-MM-DD.md`
- 如果当天出现了值得长期保留的偏好、决定、项目约定，择机整理进 `MEMORY.md`
- 如果刚发生了重要决定但还没落盘，优先补到 `ACTIVE.md`
- 纯整理不通知，除非修复了会影响执行判断的关键信息

## 5) Proactive Check

问自己这四个问题：
- 主人有没有一个我现在就能补上的小缺口？
- 有没有一个该提醒但还没提醒的时间点？
- 有没有一个重复出现 3 次以上、值得自动化的模式？
- roadmap 上有没有下一个已经足够明确、可以直接吃掉的小切片？

如果答案明确：
- 高价值且低风险 -> `P2`
- 只是想法，还不够具体 -> `P3`

## Reach Out When

- `P0`：立即发
- `P1`：有新里程碑就发
- `P2`：仅在不触发抑制规则时发
- `P3`：不发

## Response Style

- 只发结论，不发流水账
- 优先说：发生了什么、影响是什么、需不需要主人现在处理
- 对 roadmap 进展，默认包含：当前切片、验证结果、下一切片
