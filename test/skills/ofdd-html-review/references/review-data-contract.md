# Review 视图数据契约（v3）

## 一、定位

该 JSON 是 review.md + OFDD 派生的 Review 视图数据，嵌入通用模板 `assets/review-template-v3.html` 渲染。它不是新的事实源。

## 二、顶层结构

```json
{
  "meta": {},
  "lifecycle": {},
  "executionGate": {},
  "modules": [],
  "declaration": [],
  "facts": [],
  "verification": [],
  "inferences": [],
  "judgments": [],
  "directions": [],
  "questions": [],
  "unresolved": [],
  "conclusion": {},
  "observationPool": {},
  "inferencePool": {},
  "judgmentPool": {}
}
```

## 三、字段定义

### 3.1 meta

```json
{
  "id": "REV-YYYYMMDD-01",
  "title": "Review 标题",
  "subtitle": "Review 副标题",
  "date": "YYYY-MM-DD",
  "type": "认知型 / 判断型 / 决策型 / 重评型 Review",
  "owner": "负责人或待补",
  "timeBasis": "材料截至 YYYY-MM-DD",
  "instanceId": "REV-YYYYMMDD-01-v1",
  "reviewVersion": 1,
  "sessionState": "running",
  "activationMode": "initial",
  "sourceOfddVersion": "v5",
  "parentReviewId": null
}
```

`meta` 中的 `reviewVersion`、`sessionState`、`activationMode` 和 `sourceOfddVersion` 用于区分首次激活与继承式重启。

### 3.2 lifecycle（Review 生命周期）

```json
{
  "review_id": "REV-YYYYMMDD-01",
  "review_instance_id": "REV-YYYYMMDD-01-v2",
  "review_version": 2,
  "parent_review_id": "REV-YYYYMMDD-01-v1",
  "resumes_from_review_id": "REV-YYYYMMDD-01-v1",
  "source_ofdd_version": "v6",
  "activation_mode": "inherited_resume",
  "session_state": "resumed_inherited",
  "writeback_required": false,
  "execution_impact": "none",
  "execution_action": "continue",
  "can_continue_execution": true,
  "can_continue_affected_scope": true,
  "can_continue_unaffected_scope": true,
  "execution_status": "active",
  "affected_scope": [],
  "resume_conditions": [],
  "inherited_artifacts": ["结论", "F-J-004", "DEC-001"],
  "validation_warnings": [],
  "ofdd_version_mismatch": false
}
```

`session_state` 建议使用：`running`、`paused_for_writeback`、`resumed_inherited`、`superseded`、`closed`。

`review_id` 标识同一条 Review 线，`review_instance_id` 标识一次具体快照；继承式重启只递增 `review_version`，不更换 `review_id`，也不清空上一轮的有效成果。
### 3.3 executionGate（执行闸门）

```json
{
  "impact": "blocking",
  "action": "freeze_and_replan",
  "canContinue": false,
  "canContinueAffectedScope": false,
  "canContinueUnaffectedScope": true,
  "executionStatus": "partially_frozen",
  "affectedScope": ["DEC-001", "计划 P-003"],
  "resumeConditions": ["新 OFDD 版本获批", "新的 Review Gate 明确恢复范围"],
  "writebackRequired": true
}
```

`blocking` 时，HTML 只能展示暂停状态、受影响范围和续作条件；`canContinueUnaffectedScope: true` 仅表示未受影响的执行项可以继续，不能被解读为受影响范围也可继续。HTML 不直接修改执行状态。

### 3.4 modules（模块配置，模板按此渲染）

```json
[
  {"id": "declaration", "navTitle": "Review 声明", "number": "00", "title": "Review 声明", "kind": "declaration"},
  {"id": "facts", "navTitle": "事实", "number": "01", "title": "事实", "kind": "facts"}
]
```

`kind` 决定使用哪个渲染器：`declaration` / `facts` / `verification` / `inferences` / `judgments` / `directions` / `questions` / `unresolved` / `conclusion`。模块顺序由数组决定，可增删。

### 3.5 declaration（Review 声明）

```json
[{"label": "核心问题", "value": "本次要回答的问题"}]
```

### 3.6 facts（观察条目）

```json
{
  "id": "O-012",
  "text": "观察内容",
  "status": "已确认 / 部分确认 / 待核验",
  "evidence": [{"id": "E-003", "label": "证据名", "quote": "原文快照", "locator": "定位", "integrity": "complete", "href": "相对路径"}],
  "relations": {"inferences": ["F-I-001"], "judgments": [], "directions": ["DIR-C-01"]}
}
```

`status` 决定条目颜色：已确认（绿）、部分确认（琥珀）、待核验（红）。

### 3.7 verification（核验条目）

```json
{
  "id": "O-014",
  "status": "部分确认",
  "checks": [
    {"name": "忠于来源", "ok": true, "note": "判断依据，悬停显示"},
    {"name": "仍有效", "ok": true, "note": "判断依据"},
    {"name": "适用当前范围", "ok": true, "note": "判断依据"},
    {"name": "反例 / 局限", "ok": false, "note": "判断依据"}
  ]
}
```

### 3.8 inferences（推断）

```json
{"id": "F-I-006", "text": "推断内容", "status": "已支持 / 待验证 / 候选（待回写）", "observations": ["O-013"]}
```

### 3.9 judgments（判断）

```json
{"id": "F-J-004", "text": "判断结果", "evaluation_object": "评价对象", "criterion": "评价标准", "status": "已支持 / 待验证", "inferences": ["F-I-005"]}
```

### 3.10 directions（方向）

```json
{"id": "DIR-C-01", "title": "方向名", "responds": "F-J-004", "goal": "目标", "basis": ["O-012"], "risk": "风险与依赖", "status": "候选，待回写"}
```

`responds` 和 `trigger` 可引用判断或推断，模板自动识别类型。

### 3.11 questions（疑问）

```json
{"id": "Q-01", "text": "问题", "trigger": "O-014 或 F-I-006", "impact": "影响对象", "blocking": "是 / 否"}
```

### 3.12 unresolved / conclusion

```json
{"id": "Q-01", "issue": "未决事项", "impact": "影响对象", "owner": "待补"}

{"current": "当前结论", "basis": ["O-012", "F-J-004"], "uncertainty": "最大不确定性"}
```

`basis` 为混合 ID 列表（观察 / 推断 / 判断），模板按查询池自动识别类型。

### 3.13 查询池（observationPool / inferencePool / judgmentPool）

包含 OFDD **全部**观察 / 推断 / 判断（含未在主体展示的），供关系悬浮按 ID 查内容。主体展示仍由 `facts` 等数组决定。

## 四、关系悬浮

- 观察条目显示它支撑的推断 / 判断 / 方向（`relations` + 反向推导）；
- 推断、判断、方向条目显示它们依赖的观察（`observations` / `basis`）；
- 悬停任意关系链接，显示目标条目的类型 + ID + 内容；
- 所有关系引用必须能在查询池或主体列表中找到，否则列入 writeback 由 OFDD 补齐。

## 五、最小质量门槛

- `modules` 至少包含 `declaration` 和一个内容模块；
- 至少一条观察事实；
- 关键推断 / 判断 / 方向保留 OFDD ID 与关系引用；
- 所有缺失信息用"待补 / 待确认 / 候选（待回写）"表达，不编造。
