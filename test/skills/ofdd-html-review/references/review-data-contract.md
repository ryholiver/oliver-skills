# Review 应用层数据契约

## 一、定位

该对象是 OFDD 面向一次具体 Review 的派生视图，用于嵌入单文件 HTML。它不是新的事实源。

输入优先来自上游 OFDD JSON：

```text
sources / evidence_refs / observations
findings.inferences / judgments / questions
directions / decisions
review_gate / traceability / html_review_hints
```

输出为：

```text
meta / objective / summary / reasoningChains / questions
directions / recommendation / decision / unresolved / writeback
```

## 二、顶层结构

```json
{
  "meta": {},
  "objective": {},
  "summary": {},
  "reasoningChains": [],
  "questions": [],
  "directions": [],
  "recommendation": {},
  "decision": {},
  "unresolved": [],
  "writeback": []
}
```

所有顶层字段均应存在。某一阶段尚未产生方向或决定时，用空数组和明确占位对象表达，不删除字段。

## 三、字段定义

### 3.1 meta

```json
{
  "id": "REV-YYYYMMDD-01",
  "title": "项目名",
  "subtitle": "本次 Review 主题",
  "type": "认知型 Review / 判断型 Review / 决策型 Review / 重评型 Review",
  "date": "YYYY-MM-DD",
  "status": "待 Review / 待负责人确认 / 已完成 / 待重评",
  "owner": "决策人或待补",
  "sourceOfTruth": "上游 OFDD 文件名",
  "timeBasis": "截至 YYYY-MM-DD"
}
```

### 3.2 objective

```json
{
  "question": "本次需要回答的一个核心问题",
  "goal": "本次 Review 预期形成什么结果",
  "scope": "覆盖范围",
  "excluded": "明确不处理什么",
  "criteria": ["评价标准一", "评价标准二"]
}
```

### 3.3 summary

```json
{
  "current": "当前核心判断",
  "recommendation": "当前建议；不是正式决定",
  "uncertainty": "最大不确定性或阻塞问题"
}
```

### 3.4 reasoningChains

每条链以 Judgment 为入口，向下连接 Inference、Observation 和 Evidence：

```json
{
  "id": "CHAIN-01",
  "title": "人类可读的判断链标题",
  "status": "待验证",
  "statusTone": "pending",
  "judgment": {
    "id": "F-J-001",
    "text": "相对于评价标准形成的判断",
    "criteria": ["评价标准"],
    "condition": "判断成立条件"
  },
  "inference": {
    "id": "F-I-001",
    "text": "观察可能说明什么"
  },
  "observations": [
    {
      "id": "O-001",
      "text": "证据直接支持的观察",
      "evidence": {
        "id": "E-001",
        "label": "人类可读证据名称",
        "quote": "短原文快照",
        "locator": "S-001 · L10-L14",
        "integrity": "完整 / 待补位置 / 待加锚点 / 已漂移",
        "href": "相对路径或可打开链接"
      }
    }
  ]
}
```

`statusTone` 使用：

- `pending`
- `supported`
- `selected`
- `decided`
- `blocked`
- `neutral`

若 Judgment 直接基于 Observation，没有独立 Inference，可创建明确占位：

```json
{
  "id": "N/A",
  "text": "本判断直接基于观察，未新增独立推断。"
}
```

### 3.5 questions

```json
{
  "id": "F-Q-001",
  "text": "需要回答什么",
  "purpose": "为什么问",
  "impact": "影响哪个判断、方向、决定、计划或执行",
  "blocking": "具体阻塞性",
  "evidenceNeeded": "需要什么信息或证据",
  "owner": "回答人或负责人",
  "tone": "blocking / later"
}
```

`tone` 只是页面展示分类，由 OFDD 的阻塞性和阻塞对象推导，不是新的问题状态。`blocking` 建议输出成可读文本，如“阻塞：decision、DIR-001”或“当前不阻塞”。

### 3.6 directions

```json
{
  "id": "DIR-001",
  "letter": "A",
  "title": "方向名称",
  "goal": "方向目标",
  "benefits": ["支持理由一", "支持理由二"],
  "risk": "主要风险",
  "boundary": "范围与不包含内容",
  "status": "待决策 / 探索中 / 已替代",
  "reviewReady": true,
  "selected": false
}
```

- `status` 用于展示方向当前所处阶段；
- `reviewReady: true` 表示可进入本轮 Review，但不等于已经被推荐或批准；
- `selected: true` 表示当前推荐或已选择方向。若只是推荐、尚未拍板，必须由 `decision.status` 明确区分。

### 3.7 recommendation

```json
{
  "directionId": "DIR-001",
  "title": "建议选择某方向",
  "rationale": "建议理由",
  "condition": "成立条件或需要先确认的问题"
}
```

### 3.8 decision

```json
{
  "id": "DEC-001 或 N/A",
  "title": "选择某方向 / 本次尚未形成正式决定",
  "status": "拟议 / 已拍板 / 待决策 / 暂缓 / 已撤销 / 已替代",
  "selected": "DIR-001 或无",
  "rejected": "被拒绝方向或无",
  "deferred": "暂缓方向或无",
  "decisionMaker": "姓名或待补",
  "decidedAt": "日期时间或待补",
  "scope": "决定适用范围",
  "rationale": "决定依据",
  "reconsiderWhen": "重新评估条件"
}
```

不得依据推荐方向自行把 `status` 改成“已拍板”。

### 3.9 unresolved

```json
{
  "id": "F-Q-001",
  "issue": "未决事项",
  "blocking": "阻塞什么",
  "owner": "负责人",
  "due": "确认时间或待确认"
}
```

### 3.10 writeback

```json
{
  "title": "新增 Source / 更新 Finding / 更新 Decision",
  "detail": "需要回写的具体内容",
  "complete": false
}
```

## 四、上游 OFDD 到 Review 的映射

| Review 字段 | OFDD 主要来源 |
| --- | --- |
| `objective` | 用户目标、`document_meta`、`review_gate` |
| `reasoningChains.judgment` | `findings.judgments` |
| `reasoningChains.inference` | `findings.inferences` 与 traceability |
| `observations` | `observations` |
| `evidence` | `evidence_refs` + `sources` |
| `questions` | `findings.questions` |
| `directions` | `directions` |
| `recommendation` | `review_gate`、`html_review_hints`、候选方向比较 |
| `decision` | `decisions`；不得从 recommendation 伪造 |
| `unresolved` | open questions、缺失元信息、证据完整性问题 |
| `writeback` | 本轮 Review 预期产生的 Source、Observation 与状态更新 |

## 五、最小质量门槛

- 至少一个核心问题；
- 至少一条判断链；
- 每条关键判断链至少一个观察和一个证据引用；
- 决策型 Review 至少两个真实候选方向，或明确说明为什么只有一个；
- 阻塞问题必须写明阻塞对象；
- Decision 状态忠于输入；
- 所有缺失信息用“待补 / 待确认 / N/A”表达，不编造。
