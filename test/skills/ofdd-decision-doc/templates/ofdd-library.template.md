# {{project_name}} OFDD 分析库

## 0. 文档元信息

- 项目：{{project_name}}
- 生成日期：{{generated_date}}
- OFDD 版本：{{ofdd_version}}
- 输入材料：{{input_materials}}
- 当前阶段：{{current_stage}}
- 生成者：{{author}}
- 使用范围：{{scope}}
- 不包含：{{out_of_scope}}

## 1. 本轮目标

### 1.1 本次要解决

{{round_goal}}

### 1.2 本次不解决

{{round_non_goals}}

## 2. 来源 Source

> 来源表示整份材料或可定位事件，不等于具体证据片段。

| ID | 类型 | 标题 | 文件或链接 | 日期 | 版本 | 备注 |
| --- | --- | --- | --- | --- | --- | --- |
| S-001 | {{source_type}} | {{source_title}} | {{source_path_or_url}} | {{source_date}} | {{source_version}} | {{source_notes}} |

## 3. 证据引用 Evidence Reference

> 证据引用定位来源中的具体片段；关键证据宜包含稳定锚点和原文快照。

| ID | 来源 ID | 显示名称 | 位置 | 稳定锚点 | 原文快照 | 上下文概括 | 完整性 |
| --- | --- | --- | --- | --- | --- | --- | --- |
| E-001 | S-001 | {{evidence_label}} | {{locator}} | {{anchor}} | {{quote_snapshot}} | {{context_summary}} | {{integrity}} |

## 4. 观察 Observation

> 观察只记录证据中实际出现的内容，不加入解释、风险评价或行动建议。

| ID | 内容 | 证据引用 | 记录日期 | 备注 |
| --- | --- | --- | --- | --- |
| O-001 | {{observation_content}} | E-001 | {{recorded_at}} | {{observation_notes}} |

## 5. 发现 Finding

### 5.1 推断 Inference

> 推断描述事实之间可能存在的关系，必须能被证据支持、推翻或判定为证据不足。

| ID | 内容 | 基于观察 | 状态 | 验证方式 | 状态变更记录 |
| --- | --- | --- | --- | --- | --- |
| F-I-001 | {{inference_content}} | O-001 | {{inference_status}} | {{verification_method}} | {{status_change_log}} |

### 5.2 判断 Judgment

> 判断必须声明评价对象和评价标准，避免隐含价值标准。

| ID | 评价对象 | 评价标准 | 判断结果 | 依据 | 状态 | 状态变更记录 |
| --- | --- | --- | --- | --- | --- | --- |
| F-J-001 | {{evaluation_object}} | {{criterion}} | {{judgment_result}} | F-I-001 | {{judgment_status}} | {{status_change_log}} |

### 5.3 疑问 Question

> 疑问必须说明触发依据，并标记是否阻塞方向、决定、计划或执行。

| ID | 问题 | 触发依据 | 验证方式 | 阻塞性 | 阻塞对象 | 状态 |
| --- | --- | --- | --- | --- | --- | --- |
| F-Q-001 | {{question}} | F-J-001 | {{question_verification_method}} | {{blocking}} | {{blocking_targets}} | {{question_status}} |

## 6. 方向 Direction

> 方向表示值得探索或采取的行动指向，但不等于已经拍板。

| ID | 方向 | 目标 | 依据 | 边界 | 状态 |
| --- | --- | --- | --- | --- | --- |
| DIR-001 | {{direction}} | {{direction_goal}} | F-J-001 / F-Q-001 | {{direction_boundary}} | {{direction_status}} |

## 7. 决策审查节点 Review Gate

### 7.1 可以进入决策的方向

{{ready_directions}}

### 7.2 不能直接决策的方向

{{blocked_directions}}

### 7.3 阻塞性疑问

{{blocking_questions}}

### 7.4 证据不足或证据冲突

{{evidence_issues}}

### 7.5 建议决策口径

{{recommended_decision_wording}}

## 8. 决定 Decision

> 仅当用户明确拍板，或输入材料中存在明确决策记录时，状态才能写为“已拍板 / approved”；否则只能写为“拟议 / proposed”。

| ID | 决定动作 | 目标方向 | 状态 | 依据 | 适用范围 | 未决项 | 未决项阻塞性 | 重评条件 | 决策日期 | 决策人 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| DEC-001 | {{decision_action}} | DIR-001 | {{decision_status}} | {{decision_basis}} | {{decision_scope}} | {{open_questions}} | {{open_question_blocking}} | {{reevaluation_conditions}} | {{decision_date}} | {{decision_maker}} |

## 9. 下游 HTML Review 生成说明

- 推荐首页视图：{{primary_view}}
- 需要高亮的疑问：{{critical_questions}}
- 需要高亮的判断：{{high_risk_judgments}}
- 需要展开的证据链：{{evidence_chain_focus}}
- 交互建议：{{interaction_hints}}

## 10. 变更记录

| 日期 | 变更 | 触发证据 | 原因 |
| --- | --- | --- | --- |
| {{change_date}} | {{change}} | {{trigger_evidence}} | {{change_reason}} |
