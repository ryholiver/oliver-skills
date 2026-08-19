# OFDD JSON → Review View JSON 映射规范

## 1. 适用范围

本文件规定 `ofdd-decision-doc` 输出的 OFDD JSON 如何转换为 `ofdd-html-review` 消费的 Review View JSON。

它是 `ofdd-html-review` 的通用映射规范，不是某个项目的事实材料，也不是 HTML 模板本身。

标准数据流：

```text
OFDD JSON
  → Review 目标筛选
  → Review View JSON
  → HTML Review
```

职责边界：

- OFDD JSON 保存事实、证据、观察、推断、判断、疑问、方向、决定和审查门槛。
- Review View JSON 保存一次具体 Review 所需的筛选结果和展示结构。
- HTML 只负责渲染、交互和打印，不负责重新解释事实或生成决定。

---

## 2. 输入与输出

### 2.1 上游输入

优先读取：

```text
*-ofdd-data.json
```

可选读取：

```text
*-OFDD库.md
```

当 JSON 与 Markdown 不一致时，以 JSON 作为机器输入，并在 Review 的未决事项或回写清单中提示不一致风险。

### 2.2 下游输出

Review View JSON 至少包含：

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

转换器不得删除这些顶层字段。当前 Review 数据契约使用单个 `decision` 对象，因此每次生成 Review 时必须先明确本次 Review 的**焦点决定**。

若上游存在多个 Decision：

1. 依据 Review 目标选出一个焦点决定进入 `decision`；
2. 其他决定不能被改写、冒充焦点决定或静默丢弃；
3. 其他决定应进入 Review 的 `unresolved`、`writeback`，或在后续扩展契约后放入 `relatedDecisions`；
4. 如果无法确定焦点决定，应使用“本次尚未形成正式决定”的占位对象，并把多决定冲突列为未决事项。

---

## 3. 顶层字段映射

| OFDD JSON | Review View JSON | 映射规则 |
|---|---|---|
| `document_meta` | `meta` | 重组项目名称、Review 标题、日期、状态、Owner、上游来源和时间基准 |
| 用户目标、`document_meta.scope`、`review_gate` | `objective` | 收敛为一个核心问题、Review 目标、范围、排除项和评价标准 |
| 关键 `judgments`、`review_gate.summary` | `summary.current` | 汇总当前判断，不新增上游没有的事实 |
| `recommended_decision_wording`、候选方向比较 | `summary.recommendation`、`recommendation` | 明确是建议，不得转成正式决定 |
| `blocking_question_ids`、`evidence_issues` | `summary.uncertainty`、`unresolved` | 展示最大阻塞点和证据完整性问题 |
| `findings.judgments` | `reasoningChains[].judgment` | 作为每条判断链的入口 |
| `findings.inferences` | `reasoningChains[].inference` | 按 Observation 关系接入对应判断链 |
| `observations` | `reasoningChains[].observations` | 只接入被当前判断链实际使用的观察 |
| `evidence_refs` + `sources` | `reasoningChains[].observations[].evidence` | 形成证据卡片和来源链接 |
| `findings.questions` | `questions` | 映射问题、目的、影响、阻塞性、所需证据和负责人 |
| `directions` | `directions` | 直接映射方向内容，并增加展示所需的字母、理由和风险 |
| `decisions` | `decision` | 只映射本次 Review 的焦点决定，保持原始状态 |
| `traceability` | 判断链和审计辅助 | 用于校验引用关系，不替代具体证据对象 |
| `html_review_hints` | 展示提示 | 只影响筛选、高亮、章节顺序和交互，不作为事实来源 |

---

## 4. 具体字段规则

### 4.1 `meta`

| Review 字段 | 主要来源 | 规则 |
|---|---|---|
| `id` | 转换器生成 | 使用 `REV-YYYYMMDD-NN`，同一天不同 Review 不重复 |
| `title` | `document_meta.title` / `project_name` | 适合页面标题，不改变项目事实名称 |
| `subtitle` | Review 目标 | 简短说明本次审查主题 |
| `type` | Review 任务意图 | 使用认知型、判断型、决策型或重评型 Review |
| `date` | 生成日期 | 使用页面生成日期 |
| `status` | `review_gate.review_status`、`decision_readiness` | 人类可读化，但不得弱化阻塞状态 |
| `owner` | 正式 Owner / 决策人 | 未知时写“待补”，不能从材料猜测 |
| `sourceOfTruth` | 上游 OFDD 文件名 | 指向 OFDD 数据文件，不指向 Review HTML |
| `timeBasis` | 上游更新时间、状态快照时间 | 明确“截至”日期，不能把历史快照写成实时状态 |

状态示例：

| OFDD 状态 | Review 展示建议 |
|---|---|
| `blocked` | `待负责人确认` / `阻塞中` |
| `blocked_by_questions` | `问题阻塞` |
| `partially_ready` | `部分就绪` |
| `ready_for_decision` | `待决策` |
| `approved` | `已完成决定`，前提是有决策人和日期 |

### 4.2 `objective`

| Review 字段 | 主要来源 | 规则 |
|---|---|---|
| `question` | 用户明确目标、`recommended_review_questions`、关键开放问题 | 必须收敛为一个核心问题；其余问题进入 `questions` |
| `goal` | `review_gate.summary`、推荐决策措辞 | 描述本次 Review 要形成的结果，不写执行计划 |
| `scope` | `document_meta.scope` | 只保留本次 Review 相关范围 |
| `excluded` | `document_meta.out_of_scope` | 明确本次不处理内容 |
| `criteria` | `judgments[].criterion`、合同验收门槛 | 评价标准必须可回溯到 OFDD 判断或门槛 |

### 4.3 `summary`

- `current`：汇总关键 Judgment 的 `result`，不得把 Inference 直接写成事实。
- `recommendation`：引用或压缩 `review_gate.recommended_decision_wording.content`，必须标明“建议”。
- `uncertainty`：优先展示阻塞性问题和证据完整性问题；不能用泛化的“信息不足”替代具体问题。

### 4.4 `reasoningChains`

每条链必须遵循：

```text
Judgment → Inference → Observation → Evidence Reference → Source
```

字段规则：

| Review 字段 | OFDD 来源 | 规则 |
|---|---|---|
| `id` | 转换器生成 | 例如 `CHAIN-01` |
| `title` | Judgment 的评价对象或人工标题 | 能说明这条链在审查什么 |
| `status` | Judgment / Inference 状态 | 不得高于上游状态 |
| `statusTone` | 状态映射 | 只允许 `pending`、`supported`、`selected`、`decided`、`blocked`、`neutral` |
| `judgment.id` | `findings.judgments[].id` | 直接保留 |
| `judgment.text` | `evaluation_object` + `criterion` + `result` | 页面文字必须保留评价对象和标准 |
| `judgment.criteria` | `criterion` | 可拆成多个展示标签 |
| `judgment.condition` | `result` 中的成立条件 | 没有明确条件时写 `N/A` |
| `inference.id` | `findings.inferences[].id` | 直接保留 |
| `inference.text` | `findings.inferences[].content` | 不把推断改写为 Observation |
| `observations[].id` | `observations[].id` | 直接保留 |
| `observations[].text` | `observations[].content` | 只保留证据直接支持的观察 |
| `observations[].evidence` | `evidence_refs` + `sources` | 必须保留完整证据状态和来源定位 |

链路筛选规则：

1. 先选本次 Review 相关的 Judgment；
2. 沿 `supported_by_ids` 找到相关 Inference；
3. 沿 `based_on_observation_ids` 找到相关 Observation；
4. 沿 `evidence_ref_ids` 找到 Evidence Reference；
5. 沿 `source_id` 找到 Source；
6. 若任一关键引用缺失，列入 `writeback` 或 `unresolved`，不要补造关系。

### 4.5 `questions`

| Review 字段 | OFDD 来源 | 规则 |
|---|---|---|
| `id` | `findings.questions[].id` | 直接保留 |
| `text` | `question` | 直接保留或做不改变语义的展示压缩 |
| `purpose` | `verification_method` | 说明为什么需要回答 |
| `impact` | `blocking_targets` + `triggered_by_ids` | 明确影响判断、方向、决定、计划或执行中的哪一项 |
| `blocking` | `blocking` | 直接保留 |
| `evidenceNeeded` | `verification_method` | 说明需要回收的信息或证据 |
| `owner` | 已明确负责人 | 未明确时写“待补” |
| `tone` | `blocking` 推导 | `true` → `blocking`；`false` → `later` |

### 4.6 `directions`

| Review 字段 | OFDD 来源 | 规则 |
|---|---|---|
| `id` | `directions[].id` | 直接保留 |
| `letter` | 转换器生成 | 按页面顺序生成 A、B、C…… |
| `title` | `direction` | 做展示标题，不改变原意 |
| `goal` | `goal` | 直接保留 |
| `benefits` | `basis_ids` 对应 Judgment / Inference | 只列证据支持的方向理由 |
| `risk` | 相关 Judgment、Question、`boundary` | 说明主要风险，不写 Todo |
| `boundary` | `boundary` | 直接保留 |
| `status` | `directions[].status` | 展示方向所处阶段，如 `awaiting_decision` → `待决策`、`exploring` → `探索中`；只做人类可读化，不改变原意 |
| `reviewReady` | `review_gate.ready_direction_ids` | 只表示可进入本轮 Review 审查，不等于被推荐或已批准 |
| `selected` | 正式推荐或已批准 Decision | `ready_direction_ids` 不能单独导致 `selected: true`；由 `recommendation.directionId` 或 `approved` Decision 的 `target_direction_ids` 回填 |

方向状态必须区分：

- 可审查：方向位于 `review_gate.ready_direction_ids`；
- 当前推荐：`recommendation.directionId` 指向该方向；
- 已决定：存在 `approved` Decision 指向该方向；
- 阻塞：方向被未解决的 blocking Question 实际阻塞。

### 4.7 `recommendation`

| Review 字段 | OFDD 来源 | 规则 |
|---|---|---|
| `directionId` | 明确推荐方向、`recommended_decision_wording` | 没有明确推荐时写 `N/A`，不从 ready 方向猜测 |
| `title` | 推荐方向标题 | 使用“建议……”等措辞 |
| `rationale` | 方向基础 Judgment / Review Gate 摘要 | 说明为什么推荐，不写成决定 |
| `condition` | 相关 blocking Questions、重评条件 | 说明必须先确认的条件 |

### 4.8 `decision`

`decision` 必须忠实反映上游 Decision：

| Review 字段 | OFDD 来源 | 规则 |
|---|---|---|
| `id` | `decisions[].id` | 焦点决定直接保留；没有正式决定时为 `N/A` |
| `title` | 决定动作的展示文本 | `proposed` 时使用“拟议……/本次尚未形成正式决定” |
| `status` | `decisions[].status` | 不得改变 `proposed`、`approved`、`revoked`、`superseded` |
| `selected` | `target_direction_ids` | 只表达目标方向，不代表已经批准 |
| `rejected` | 正式拒绝关系 | 没有拒绝信息时写“无” |
| `deferred` | `action=defer` 或明确暂缓关系 | 没有则写“无” |
| `decisionMaker` | `decision_maker` | 空值显示为“待补” |
| `decidedAt` | `decision_date` | 空值显示为“待补” |
| `scope` | `scope` | 直接保留 |
| `rationale` | `basis_ids` 对应 Judgment | 说明决定依据，不将推荐理由伪装成决定依据 |
| `reconsiderWhen` | `reevaluation_conditions` | 直接保留 |

安全规则：

- `recommendation` 不得自动生成 `approved` Decision；
- `ready_direction_ids` 不得自动生成已选择方向；
- 有 blocking Question 时，不得把对应范围写成可执行；
- 多个上游 Decision 不能静默合并成一个没有来源的综合决定。

### 4.9 `unresolved`

`unresolved` 汇总两类内容：

1. 尚未回答且影响 Review 的 Questions；
2. 证据完整性问题，如 `needs_anchor`、`needs_locator`、`drifted`。

| Review 字段 | 来源 | 规则 |
|---|---|---|
| `id` | Question ID 或 Evidence ID | 直接保留原编号 |
| `issue` | 问题文本或证据问题说明 | 适合页面阅读 |
| `blocking` | `blocking_targets` 或证据问题类型 | 明确阻塞对象 |
| `owner` | 已知负责人 | 未知时写“待补” |
| `due` | 已知时间要求 | 没有明确日期时写“待确认” |

### 4.10 `writeback`

Review 结束后需要回写 OFDD 的内容包括：

- 新确认的 Source 或稳定证据定位；
- 新增或修正的 Observation；
- Judgment / Question 的状态变化；
- Direction 的选择状态；
- Decision 的决策人、日期、范围和状态；
- 被确认、关闭或新增的阻塞问题；
- 旧事实被新信息替代时的变更记录。

Review 不能直接覆盖上游事实源。所有现场新信息先进入 `writeback`，再由上游 OFDD 更新后重新生成 Review。

---

## 5. 证据对象映射

Review 中每条主体 Observation 尽量包含：

```json
{
  "id": "E-001",
  "label": "人类可读证据名称",
  "quote": "短原文快照",
  "locator": "来源定位",
  "integrity": "complete / needs_locator / needs_anchor / drifted",
  "href": "相对路径或可打开链接"
}
```

字段来源：

| Review 字段 | OFDD 来源 |
|---|---|
| `id` | `evidence_refs[].id` |
| `label` | `evidence_refs[].label` |
| `quote` | `evidence_refs[].quote_snapshot` |
| `locator` | `evidence_refs[].locator` |
| `integrity` | `evidence_refs[].integrity` |
| `href` | `sources[].file_or_url` + 稳定锚点 |

处理规则：

| OFDD `integrity` | Review 展示 |
|---|---|
| `complete` | 正常证据 |
| `needs_locator` | 显示“待补定位” |
| `needs_anchor` | 显示“待加锚点” |
| `drifted` | 显示“已漂移，需重新核验” |

没有稳定锚点时，可以保留行号、时间戳或页码，但不得伪造 `#anchor`。如果不能生成可靠链接，保留证据对象并将链接状态列入 `unresolved` 或 `writeback`。

---

## 6. 转换前后校验

生成 Review View JSON 后，至少校验：

1. 顶层字段完整；
2. 每条 `reasoningChains` 都有 Judgment、Inference、Observation 和 Evidence；
3. 每条 Evidence 的 ID 在上游 `evidence_refs` 中存在；
4. 每条 Question 的 ID 在上游 `findings.questions` 中存在；
5. 每条 Direction 的 ID 在上游 `directions` 中存在；
6. `decision.status` 与上游焦点 Decision 状态一致；
7. `recommendation.directionId` 不得自动变成已批准方向；
8. `blocking` 问题的影响对象可见；
9. `needs_anchor`、`needs_locator`、`drifted` 没有被降级成完整证据；
10. HTML 模板所需字段可被 `render_review.py` 校验通过。

---

## 7. 与其他 skill 的关系

- `ofdd-decision-doc`：负责从事实材料生成 OFDD JSON；
- `ofdd-html-review`：依据本文件将 OFDD JSON 转成 Review View JSON，并渲染 HTML；
- HTML 模板：只消费 Review View JSON，不直接解释 OFDD 原始结构。

如果项目需要记录某次具体 Review 采用了哪些筛选和决定，应另存项目级映射说明，不要把项目事实写入本通用 skill 规范。
