# OFDD 双文件输出契约

> 用途：规定 `ofdd-decision-doc` skill 的默认交付物。Markdown 面向人类审查和知识库沉淀；JSON 面向下游 HTML Review skill。

## 一、输出包

每次完整运行默认输出两个文件：

```text
[项目名]-OFDD库.md
[项目名]-ofdd-data.json
```

其中：

| 文件 | 职责 | 主要读者 | 下游优先级 |
| --- | --- | --- | --- |
| Markdown 库文件 | 人类阅读、知识沉淀、人工审查、变更记录 | 人 | 次要 |
| JSON 数据文件 | 结构化实体、关系、状态、审查信号 | HTML Review skill / 程序 | 主要 |

若 Markdown 与 JSON 出现冲突，下游 HTML Review 应以 JSON 为准，并在页面中提示数据不一致风险。

## 二、Markdown 库文件结构

```markdown
# [项目名] OFDD 分析库

## 0. 文档元信息
- 项目：
- 生成日期：
- OFDD 版本：
- 输入材料：
- 当前阶段：探索 / 待决策 / 已拍板 / 执行反馈
- 生成者：
- 使用范围：

## 1. 本轮目标
- 本次要解决：
- 本次不解决：

## 2. 来源 Source
| ID | 类型 | 标题 | 文件或链接 | 日期 | 版本 | 备注 |
| --- | --- | --- | --- | --- | --- | --- |

## 3. 证据引用 Evidence Reference
| ID | 来源 ID | 显示名称 | 位置 | 稳定锚点 | 原文快照 | 完整性 |
| --- | --- | --- | --- | --- | --- | --- |

## 4. 观察 Observation
| ID | 内容 | 证据引用 | 记录日期 | 备注 |
| --- | --- | --- | --- | --- |

## 5. 发现 Finding

### 5.1 推断 Inference
| ID | 内容 | 基于观察 | 状态 | 验证方式 |
| --- | --- | --- | --- | --- |

### 5.2 判断 Judgment
| ID | 评价对象 | 评价标准 | 判断结果 | 依据 | 状态 |
| --- | --- | --- | --- | --- | --- |

### 5.3 疑问 Question
| ID | 问题 | 触发依据 | 验证方式 | 阻塞性 | 阻塞对象 | 状态 |
| --- | --- | --- | --- | --- | --- | --- |

## 6. 方向 Direction
| ID | 方向 | 目标 | 依据 | 边界 | 状态 |
| --- | --- | --- | --- | --- | --- |

## 7. 决策审查节点 Review Gate

### 7.1 可以进入决策的方向

### 7.2 不能直接决策的方向

### 7.3 阻塞性疑问

### 7.4 证据不足或证据冲突

### 7.5 建议决策口径

## 8. 决定 Decision
| ID | 决定动作 | 目标方向 | 状态 | 依据 | 适用范围 | 未决项 | 未决项阻塞性 | 重评条件 | 决策日期 | 决策人 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |

## 9. 下游 HTML Review 生成说明
- 推荐首页视图：
- 需要高亮的疑问：
- 需要高亮的判断：
- 需要展开的证据链：
- 交互建议：

## 10. 变更记录
| 日期 | 变更 | 触发证据 | 原因 |
| --- | --- | --- | --- |
```

## 三、JSON 顶层结构

```json
{
  "_comment": "OFDD 结构化数据文件。用于下游 HTML Review skill 生成审查页面。",
  "schema_version": "1.0.0",
  "ofdd_version": "v5",
  "document_meta": {},
  "sources": [],
  "evidence_refs": [],
  "observations": [],
  "findings": {
    "inferences": [],
    "judgments": [],
    "questions": []
  },
  "directions": [],
  "decisions": [],
  "review_gate": {},
  "traceability": {},
  "html_review_hints": {},
  "change_log": []
}
```

## 四、字段契约

### 4.1 document_meta

```json
{
  "project_name": "",
  "title": "",
  "created_at": "YYYY-MM-DD",
  "updated_at": "YYYY-MM-DD",
  "author": "AI",
  "status": "review_required",
  "input_files": [
    {
      "path": "",
      "role": "source|reference|existing_output"
    }
  ],
  "scope": "",
  "out_of_scope": []
}
```

推荐 `status`：`draft`、`review_required`、`decision_ready`、`approved`、`blocked`、`superseded`。

### 4.2 sources

```json
{
  "id": "S-001",
  "type": "document",
  "title": "",
  "file_or_url": "",
  "date": "YYYY-MM-DD|null",
  "version": "",
  "notes": ""
}
```

推荐 `type`：`interview`、`document`、`communication`、`data`、`event`、`meeting`、`other`。

### 4.3 evidence_refs

```json
{
  "id": "E-001",
  "source_id": "S-001",
  "label": "",
  "locator": "行号 / 时间戳 / 页码 / 事件时间",
  "anchor": "",
  "quote_snapshot": "",
  "context_summary": "概括：",
  "integrity": "complete"
}
```

推荐 `integrity`：`complete`、`needs_locator`、`needs_anchor`、`drifted`。

### 4.4 observations

```json
{
  "id": "O-001",
  "content": "",
  "evidence_ref_ids": ["E-001"],
  "recorded_at": "YYYY-MM-DD",
  "notes": ""
}
```

约束：Observation 只引用 Evidence Reference，不直接引用 Source。

### 4.5 findings.inferences

```json
{
  "id": "F-I-001",
  "type": "inference",
  "content": "",
  "based_on_observation_ids": ["O-001"],
  "status": "pending",
  "verification_method": "",
  "status_change_log": []
}
```

推荐 `status`：`pending`、`supported`、`refuted`、`inconclusive`、`conflicted`。

### 4.6 findings.judgments

```json
{
  "id": "F-J-001",
  "type": "judgment",
  "evaluation_object": "",
  "criterion": "",
  "result": "",
  "supported_by_ids": ["F-I-001"],
  "status": "pending",
  "status_change_log": []
}
```

约束：判断必须说明评价对象和评价标准。

### 4.7 findings.questions

```json
{
  "id": "F-Q-001",
  "type": "question",
  "question": "",
  "triggered_by_ids": ["F-J-001"],
  "verification_method": "",
  "blocking": true,
  "blocking_targets": ["decision"],
  "status": "open"
}
```

推荐 `status`：`open`、`answered`、`deferred`、`unanswerable`、`cancelled`。

### 4.8 directions

```json
{
  "id": "DIR-001",
  "direction": "",
  "goal": "",
  "basis_ids": ["F-J-001"],
  "boundary": "",
  "status": "awaiting_decision"
}
```

推荐 `status`：`exploring`、`awaiting_decision`、`in_decision`。

### 4.9 decisions

```json
{
  "id": "DEC-001",
  "action": "select",
  "target_direction_ids": ["DIR-001"],
  "status": "proposed",
  "basis_ids": ["F-J-001"],
  "scope": "",
  "open_question_ids": [],
  "open_question_blocking": false,
  "reevaluation_conditions": [],
  "decision_date": null,
  "decision_maker": null
}
```

推荐 `action`：`select`、`reject`、`defer`。

推荐 `status`：`proposed`、`approved`、`revoked`、`superseded`。

### 4.10 review_gate

```json
{
  "_comment": "决策审查节点。用于告诉下游 HTML Review skill 当前哪些内容可以审查、哪些内容不能拍板。",
  "review_required": true,
  "review_status": "needs_human_review",
  "summary": "",
  "decision_readiness": "not_ready",
  "ready_direction_ids": [],
  "blocked_direction_ids": [],
  "blocking_question_ids": [],
  "evidence_issues": [
    {
      "type": "needs_anchor",
      "target_id": "E-001",
      "message": ""
    }
  ],
  "recommended_review_questions": [],
  "recommended_decision_wording": {
    "status": "proposed",
    "content": ""
  }
}
```

推荐 `review_status`：`needs_human_review`、`ready_for_decision`、`blocked_by_questions`、`approved`。

推荐 `decision_readiness`：`ready`、`partially_ready`、`not_ready`、`blocked`。

### 4.11 traceability

```json
{
  "decision_to_evidence": [
    {
      "decision_id": "DEC-001",
      "direction_ids": [],
      "finding_ids": [],
      "observation_ids": [],
      "evidence_ref_ids": [],
      "source_ids": []
    }
  ],
  "direction_to_evidence": [
    {
      "direction_id": "DIR-001",
      "finding_ids": [],
      "observation_ids": [],
      "evidence_ref_ids": [],
      "source_ids": []
    }
  ]
}
```

### 4.12 html_review_hints

```json
{
  "page_title": "",
  "primary_view": "review_gate",
  "sections": [
    "overview",
    "review_gate",
    "directions",
    "decisions",
    "blocking_questions",
    "evidence_chain",
    "source_index"
  ],
  "highlight_ids": {
    "critical_questions": [],
    "high_risk_judgments": [],
    "decision_candidates": []
  },
  "interaction_hints": {
    "enable_evidence_hover": true,
    "enable_trace_expand": true,
    "enable_status_filter": true,
    "enable_blocking_filter": true
  }
}
```

### 4.13 change_log

```json
{
  "date": "YYYY-MM-DD",
  "change": "",
  "trigger_evidence_ids": [],
  "reason": ""
}
```

## 五、下游 HTML Review 使用建议

HTML Review skill 应优先读取：

1. `review_gate`：生成首页审查面板；
2. `directions` 与 `decisions`：生成方向与拟议决定卡片；
3. `findings.questions`：生成阻塞问题列表；
4. `traceability`：生成证据链展开结构；
5. `evidence_refs`：生成悬停原文快照；
6. `sources`：生成来源索引。

HTML Review skill 不应把 `html_review_hints` 当作强制样式，只将其作为展示意图。
