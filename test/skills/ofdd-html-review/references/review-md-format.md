# review.md 配置格式

## 1. 定位

`*-Review.md` 是每次 Review 的**实例配置 + 完整文档**：

- YAML front-matter：机器可解析（`build_review_from_md.py` 读取）；
- Markdown 正文：人类可读的完整 Review 文档，不生成 HTML 也自成一份 Review。

## 2. front-matter 字段

```yaml
---
review_id: REV-YYYYMMDD-01       # Review 线 ID；续轮保持不变
review_version: 1                 # 同一 Review 线递增，不是清空重开
review_instance_id: REV-YYYYMMDD-01-v1
parent_review_id: null             # 续轮填写上一实例 ID；首轮为空
resumes_from_review_id: null       # 继承式重启时填写上一轮实例 ID
source_ofdd_version: v5            # 本轮基于的 OFDD 版本
activation_mode: initial            # initial / inherited_resume
session_state: running              # running / paused_for_writeback / resumed_inherited / superseded / closed
writeback_required: false
execution_impact: none              # none / potential / blocking
execution_action: continue          # 由脚本根据 execution_impact 计算，不作为执行指令
affected_scope: []                  # 受新信息影响的决定、方向、计划或执行范围
resume_conditions: []               # blocking 时恢复受影响执行必须满足的条件
inherited_artifacts: []             # 续轮承接的上一轮成果 ID 或模块
type: 认知型 Review                  # 认知型 / 判断型 / 决策型 / 重评型
title: Review 标题
subtitle: Review 副标题
date: YYYY-MM-DD
time_basis: 材料截至日期；Review 计划时间
owner: 负责人
decider: 谁拍板；或"本次不拍板，由 XXX 确认"

goal: 本次目标（一句话）
task: 本次任务（一句话，谁布置）
core_question: 本次要回答的核心问题
expected_result: 预期结果
scope: 覆盖范围
excluded:
  - 不包含内容

filter:
  include:                      # 本次任务范围（脚本自动补链）
    observations: [O-012, O-014]
    inferences: [F-I-006]
    judgments: [F-J-004]
    directions: []              # 空 = 由判断反查 OFDD 方向
  exclude: {}                   # 显式排除（可选）
  blocking_questions_only: false
  highlight: auto               # auto = 用 OFDD 高亮信号
  extra_inferences:             # 本次新增候选推断（待回写）
    - {id: C-I-01, text: 推断内容, status: 候选（待回写）, observations: [O-012], writeback_status: pending, execution_impact: none}
  extra_judgments: []           # 同样支持 writeback_status / execution_impact
  extra_directions:             # 本次新增候选方向（待回写）
    - {id: DIR-C-01, title: 方向名, responds: F-J-004, goal: 目标, basis: [O-012], risk: 风险, status: 候选，待回写, writeback_status: pending, execution_impact: none}
  extra_questions:              # 本次任务疑问
    - {id: Q-01, text: 问题, trigger: O-014, impact: 影响对象, blocking: 否, writeback_status: pending, execution_impact: none}

verification:                   # 核验结论（Review 现场/人工填写）
  - {id: O-014, status: 部分确认, checks: [{name: 忠于来源, ok: true, note: 依据}, {name: 仍有效, ok: true, note: 依据}, {name: 适用当前范围, ok: true, note: 依据}, {name: 反例 / 局限, ok: false, note: 依据}]}

conclusion:
  current: 当前结论
  basis: [O-012, F-J-004]
  uncertainty: 最大不确定性

modules:                        # 展示配置：模板按此渲染
  - {id: declaration, number: "00", title: Review 声明, kind: declaration}
  - {id: facts, number: "01", title: 事实, kind: facts}
  - {id: verification, number: "02", title: 关键观察核验, kind: verification}
  - {id: inferences, number: "03", title: 推断, kind: inferences}
  - {id: judgments, number: "04", title: 判断, kind: judgments}
  - {id: directions, number: "05", title: 方向, kind: directions}
  - {id: questions, number: "06", title: 疑问, kind: questions}
  - {id: unresolved, number: "07", title: 未决事项, kind: unresolved}
  - {id: conclusion, number: "08", title: 结论汇总, kind: conclusion}
---
```

## 3. 新信息分流与继承式重启

### 3.1 先判断是否需要回写

新内容按“是否改变事实源、是否改变当前执行风险”分流，而不是按“是否已经写进 HTML”分流：

- **只影响展示**：只是措辞、排序、版式或导航变化，不改变事实、判断、方向、决定和执行范围；留在当前 Review，不回写 OFDD。
- **候选但未确认**：新假设、新判断或新疑问尚未有足够证据，但可能改变结论；先写入当前 Review 的 `extra_*`，标记 `writeback_status: pending`，Review 可以继续，结束时回写或明确丢弃。
- **执行阻塞**：新信息已经确认，或其不确定性足以让继续执行产生不可逆成本，并且可能改变事实、判断、方向、决定、验收标准、依赖或执行前置条件；立即暂停 Review，先回写 OFDD。

只有第三类才触发即时 OFDD 版本递增。第二类不是绕过 OFDD，而是允许 Review 先完成候选整理，再统一回流。

### 3.1 三类处理

| 新信息类型 | Review 处理 | OFDD 处理 | 执行处理 |
| --- | --- | --- | --- |
| 只影响表达、排序或展示 | 当前 Review 内处理 | 不回写 | 不影响执行 |
| 尚未确认、但可能影响判断 | 写入 `extra_*`，标记 `候选（待回写）` | Review 结束后回写 | 当前执行继续，但需标注风险 |
| 已确认，或继续执行会产生不可逆成本且影响事实、决定、范围或执行前置条件 | 当前 Review 暂停 | 立即回写并生成新 OFDD 版本 | 只冻结受影响范围；未受影响范围可继续 |

### 3.2 继承式重启

当 `execution_impact: blocking` 或新信息会改变 OFDD 事实、判断、方向、决定、阻塞项或执行范围时：

1. 当前 Review 实例改为 `paused_for_writeback`，不得继续以旧 OFDD 版本指导受影响的执行；
2. 将新信息回写 OFDD，生成新的 `ofdd_version`；
3. 创建同一 `review_id` 的下一版 Review，递增 `review_version`，填写 `parent_review_id` 和 `resumes_from_review_id`；
4. 新版必须继承上一版仍有效的目标、范围、结论、已确认链路、未决项和回写清单；
5. 只对受影响部分重算，不得清空上一版有效成果；未受影响的事实、结论、未决项和讨论记录作为 `inherited_artifacts` 继续带入。
6. 新 Review Gate 明确恢复条件和范围后，执行层才可以恢复受影响项；Review 页面本身不直接恢复执行。

因此，这不是第一次激活，也不是清空式重开，而是 `activation_mode: inherited_resume` 的继承式重启。

## 4. 注意事项

1. front-matter 结束标记必须是**独立一行的 `---`**（正则按行匹配，注释里的 `----` 不影响）；
2. `date` 会被 YAML 解析为日期对象，脚本输出 JSON 时自动转字符串；
3. `extra_*` 是本次 Review 推导的新内容，必须标注 `writeback_status: pending` 和 `execution_impact`；
4. `execution_impact: blocking` 的内容不得继续停留在普通候选区，必须暂停 Review 并触发 OFDD 回写；
5. 正文应完整列出筛选结果（观察 / 推断 / 判断 / 方向 / 疑问 / 核验 / 结论 / 回写清单），让人不依赖 HTML 也能读完整 Review；
6. 用户的新想法（如"确认 agent 基座可复用性"）由 AI 理解后转为 `extra_questions` / `include` / `extra_directions` 等结构化字段放进来，再重新生成；若影响执行，必须按继承式重启处理。
