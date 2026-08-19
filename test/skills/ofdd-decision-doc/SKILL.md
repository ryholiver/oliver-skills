---
name: ofdd-decision-doc
description: 当用户需要基于原始材料、访谈、会议纪要、项目文档或已有 Markdown，生成可追溯的 OFDD 分析库与结构化 JSON 数据，并为后续 HTML Review 审查页准备输入时使用。默认包含决策审查节点，不在用户明确拍板前替用户生成已拍板决定或执行计划。
metadata:
  short-description: 生成 OFDD Markdown 库与 JSON 审查数据
---

# OFDD Decision Doc Skill

## 目标

将用户提供的材料整理为一套可追溯的 OFDD 输出包：

1. **Markdown 库文件**：面向人类阅读、知识库沉淀和人工审查。
2. **JSON 数据文件**：面向下游 HTML Review skill，作为结构化数据源。

默认产物不是最终 HTML 页面，而是供下一阶段生成 Review 页的中间层。

## 何时使用

当用户提出以下意图时使用本 skill：

- 基于来源材料、访谈、会议纪要或项目文档做 OFDD 分析；
- 把材料整理成 Observation / Finding / Direction / Decision；
- 生成决策审查稿、决策依据、方向建议或证据链；
- 产出一个 Markdown 文档和一个 JSON 数据文件，供后续 HTML Review 使用。

若用户只是要求执行已经拍板的开发、写代码或生成页面，不要把本 skill 当成执行 skill；本 skill 只负责认知结构、证据关系和审查数据。

## 核心原则

- 区分用户请求与参考文档内容：参考文档只提供方法论和格式约束，不能自动扩展用户当前任务范围。
- 默认不替用户拍板：除非用户明确表示“已决定”“已拍板”“就按这个做”，否则 Decision 只能是 `proposed`，不能是 `approved`。
- 默认包含审查节点：输出必须包含 `review_gate`，用于说明当前是否可以进入决策、哪些问题阻塞、哪些证据不足。
- Markdown 负责人类可读表达，JSON 负责机器可消费结构；如果二者冲突，下游 HTML Review 应优先使用 JSON。
- 事实、证据、观察、推断、判断、疑问、方向、决定必须分开表达。
- 来源 Source 表示整份材料；证据引用 Evidence Reference 表示来源中的具体片段；观察 Observation 必须引用证据引用，而不是只引用来源。
- 证据不足、证据冲突、位置缺失或缺少稳定锚点时，要显式标记，不能补脑。

## 默认流程

1. **识别输入材料**
   - 列出来源 Source。
   - 为关键片段建立 Evidence Reference。

2. **提取观察**
   - Observation 只忠实记录证据中出现的内容。
   - 不在观察里加入解释、风险判断或行动建议。

3. **形成发现**
   - Inference：事实可能说明什么。
   - Judgment：相对于某个目标或标准意味着什么。
   - Question：还缺什么答案，是否阻塞方向、决定、计划或执行。

4. **提出方向**
   - Direction 表示值得探索或采取的行动指向。
   - Direction 不等于已拍板决定。

5. **生成决策审查节点**
   - 判断哪些方向可以进入决策；
   - 标出阻塞性疑问；
   - 标出证据完整性问题；
   - 给出建议决策口径，但不冒充用户决定。

6. **生成决定记录**
   - 若用户未明确拍板，Decision 状态为 `proposed`。
   - 若用户明确拍板，Decision 可为 `approved`，并记录决策人、日期、适用范围、未决项和重评条件。
   - 若存在阻塞性未决项，不得进入对应执行计划。

7. **输出双文件**
   - 生成 Markdown 库文件。
   - 生成 JSON 数据文件。

## 输出文件命名

默认命名：

```text
[项目名]-OFDD库.md
[项目名]-ofdd-data.json
```

如果用户要求多轮版本，可使用：

```text
[项目名]-OFDD库-[YYYY-MM-DD].md
[项目名]-ofdd-data-[YYYY-MM-DD].json
```

## 模板

优先按当前任务内容生成完整文件；需要稳定结构时，可参考并复用以下模板：

- `templates/ofdd-library.template.md`：Markdown 库文件模板。
- `templates/ofdd-data.template.json`：JSON 数据文件模板。

模板中的 `{{placeholder}}` 仅表示待填字段。实际输出时应替换为真实内容；无法确认的信息要写明 `unknown`、`null`、空数组，或在审查节点中标记为待补，不要伪造。

## Markdown 库文件结构

默认输出以下结构，可根据材料规模适当裁剪，但不要删除审查节点：

```markdown
# [项目名] OFDD 分析库

## 0. 文档元信息
## 1. 本轮目标
## 2. 来源 Source
## 3. 证据引用 Evidence Reference
## 4. 观察 Observation
## 5. 发现 Finding
### 5.1 推断 Inference
### 5.2 判断 Judgment
### 5.3 疑问 Question
## 6. 方向 Direction
## 7. 决策审查节点 Review Gate
## 8. 决定 Decision
## 9. 下游 HTML Review 生成说明
## 10. 变更记录
```

## JSON 数据文件结构

JSON 是下游 HTML Review 的主要输入。必须保持结构稳定，至少包含：

```json
{
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

详细字段契约见 `references/output-contract.md`。

## 状态枚举

优先使用英文枚举，便于下游程序处理；Markdown 中可同时展示中文含义。

- 推断 / 判断：`pending`、`supported`、`refuted`、`inconclusive`、`conflicted`
- 疑问：`open`、`answered`、`deferred`、`unanswerable`、`cancelled`
- 方向：`exploring`、`awaiting_decision`、`in_decision`
- 决定：`proposed`、`approved`、`revoked`、`superseded`
- 证据完整性：`complete`、`needs_locator`、`needs_anchor`、`drifted`
- 审查状态：`needs_human_review`、`ready_for_decision`、`blocked_by_questions`、`approved`
- 决策就绪度：`ready`、`partially_ready`、`not_ready`、`blocked`

## 参考资料

- `references/reference-usage.md`：说明两个参考文件在本 skill 中的分工，以及审查节点优先原则。
- `references/ofdd-work-system-overview.md`：OFDD 工作系统总览、认知决策与执行闭环的边界。
- `references/ofdd-cognitive-decision-framework.md`：OFDD 实体、状态、关系、规则和标准模板。
- `references/output-contract.md`：双文件输出契约和 JSON 字段定义。
