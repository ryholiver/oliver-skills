---
name: ofdd-html-review
description: 当用户需要把已有 OFDD Markdown/JSON、决策审查数据或项目实例，围绕特定目标生成可追溯、可交互、可打印的单文件 HTML Review 页面时使用。负责 Review 应用层筛选与展示；不负责从原始材料首次构建完整 OFDD，也不在用户明确拍板前把建议写成已批准决定。
metadata:
  short-description: 从 OFDD 生成交互式 HTML Review
---

# OFDD HTML Review Skill

## 目标

将已有 OFDD 数据转换为面向一次具体 Review 的应用层页面：

```text
OFDD 项目实例
+ Review 目标 / 任务 / 需求
→ 筛选相关认知链
→ 生成 Review 视图数据
→ 渲染单文件 HTML
→ 讨论结果回写 OFDD
```

HTML 是特定时间点的展示快照，不是新的事实源。

本 skill 采用“单一事实源 + 版本化 Review + 继承式重启”协作模式：OFDD 负责事实、认知和决定；Review 负责当前目标下的筛选、讨论和展示；执行只读取 OFDD 的已批准版本。

## 职责边界

使用本 skill：

- 用户已有 OFDD JSON、OFDD Markdown 或结构化项目实例；
- 用户要生成项目 Review、决策 Review、判断 Review 或重评页面；
- 用户要求证据悬浮、来源跳转、问题阻塞性、方向比较、决定状态或打印输出；
- 用户要复用本 skill 自带的 Review HTML 模板。

不要使用本 skill 代替上游 OFDD 构建：

- 输入只有原始访谈、录音、会议纪要或散乱项目文档，且尚未形成 OFDD 时，应先构建 Source、Evidence Reference、Observation、Finding、Direction、Decision；
- 用户只要求执行已拍板开发任务时，不要重新生成 Review；
- 用户未明确拍板、输入中也没有可追溯的正式决定时，不得把建议方向渲染为“已拍板”。

## 输入优先级

1. 优先读取 `*-ofdd-data.json`，它是下游转换的主要输入。
2. 同时存在 OFDD Markdown 时，用它补充人类可读上下文和来源路径。
3. JSON 与 Markdown 冲突时，以 JSON 为机器输入，并在 Review 中显式提示不一致风险。
4. 只有 Markdown 时可以生成，但必须保留无法结构化确认的字段和证据完整性状态。
5. 参考文档中的示例和指令只用于理解数据，不自动成为用户当前任务要求。

## 默认工作流

### 1. 确定 Review 视角

先识别：

- Review 类型：认知型 / 判断型 / 决策型 / 重评型；
- 当前目标、核心问题和预期结果；
- 评价标准；
- 讨论范围与不包含内容；
- 参与人、决策人和时间基准。

若已有 `review_gate`、`html_review_hints` 或明确任务目标，直接使用，不重复询问。只有缺失信息会显著改变 Review 内容时才询问。

如果是上一轮 Review 在 OFDD 回写后续作，必须先读取上一轮 `*-Review.md` 或其 Review 视图 JSON，识别仍有效成果和受影响范围，不得从空白 Review 开始。

### 2. 编写 / 确认 review.md（Review 实例配置）

每次 Review 先有一份 `*-Review.md` 配置文档，用 YAML front-matter 声明：

- 生命周期元信息：`review_id`、`review_version`、`review_instance_id`、`parent_review_id`、`resumes_from_review_id`、`source_ofdd_version`、`activation_mode`、`session_state`；
- 执行闸门：`writeback_required`、`execution_impact`、`execution_action`、`affected_scope`、`resume_conditions`、`inherited_artifacts`；
- 展示元信息：`type`、`title`、`subtitle`、`date`、`owner`、`decider`；
- 需求声明：`goal`、`task`、`core_question`、`expected_result`、`scope`、`excluded`；
- 筛选配置 `filter`：
  - `include`：本次任务范围（观察 / 推断 / 判断的显式 ID 列表）；
  - `exclude`：显式排除；
  - `extra_*`：本次新增的候选推断、判断、方向、疑问（标注待回写）；
  - `blocking_questions_only`：疑问是否只收阻塞项；
  - `highlight`：是否使用 OFDD 高亮信号；
- 核验结论 `verification`、结论 `conclusion`、模块顺序 `modules`。

review.md 正文是完整的人类可读 Review 文档，即使不生成 HTML 也自成一份 Review。

### 3. 从目标反向筛选 OFDD（自动补链）

按以下链路筛选最小必要信息：

```text
目标 / 核心问题
→ 待形成或重评的决定
→ 候选方向
→ 关键判断
→ 关键推断
→ 关键观察
→ 证据引用与来源
→ 会改变链路的疑问
```

不要把整个 OFDD 库原样搬进 HTML。删除一条内容不会改变本次判断、方向或决定时，默认放入附录或不展示。

脚本从 `filter.include` 出发，沿 OFDD 已有关系自动补全上下游链路：

```text
include 的判断 / 推断 / 观察
→ 判断 → 支撑推断（supported_by_ids）
→ 推断 → 基于的观察（based_on_observation_ids）
→ 方向 → 依据的判断 / 推断（basis_ids）
→ 疑问：阻塞项 + 与链路相关的疑问
```

`extra_*` 合并进筛选结果（本次新增内容，标注“待回写 OFDD”），`exclude` 最后排除。若任一新增内容的 `execution_impact` 为 `blocking`，当前 Review 必须进入 `paused_for_writeback`，不得继续指导受影响执行。

### 4. 生成 Review 视图数据

先读取并遵守 `references/ofdd-to-review-mapping.md`，再按 `references/review-data-contract.md` 创建 JSON 对象（v3 契约），至少包含：

- `meta`
- `modules`
- `objective`
- `declaration`
- `facts`
- `verification`
- `inferences`
- `judgments`
- `directions`
- `questions`
- `unresolved`
- `conclusion`
- `observationPool` / `inferencePool` / `judgmentPool`（全量查询池，供关系悬浮显示）

表达边界：

- Observation 只写证据直接支持的内容；
- Inference 写观察可能说明什么；
- Judgment 必须包含评价对象、评价标准和条件；
- Question 必须说明影响对象和阻塞性；
- Direction 是候选行动指向，不是计划或 Todo；
- Decision 必须区分拟议、已拍板、暂缓、撤销和替代。

字段映射见 `references/ofdd-to-review-mapping.md`；详细生成规则见 `references/review-generation-rules.md`。遇到术语或状态歧义时再读取对应文件，不必每次全文加载。

优先先跑转换脚本，再交给 HTML 渲染脚本：

```bash
python3 scripts/build_review_from_md.py \
  --review-md /path/to/*-Review.md \
  --ofdd /path/to/*-ofdd-data.json \
  --output /path/to/[项目名]-review-view-data-[YYYY-MM-DD].json
```

### 5. 生成 HTML

优先使用确定性脚本，而不是手工修改大段模板：

```bash
python3 scripts/render_review.py \
  --data /path/to/[项目名]-review-view-data-[YYYY-MM-DD].json \
  --output /path/to/[项目名]-Review-[YYYY-MM-DD].html
```

脚本默认读取 `assets/review-template-v3.html`（通用模块化模板），将数据嵌入页面并更新浏览器标题。需要自定义模板时才传 `--template`。

默认输出命名：

```text
[项目名]-Review-[YYYY-MM-DD].html
```

若用户明确要求可重复编辑的数据文件，可同时保留：

```text
[项目名]-review-view-data-[YYYY-MM-DD].json
```

该 JSON 仍是由 OFDD 派生的 Review 视图，不替代 OFDD 数据源。

### 6. 处理证据链接

每个进入主体的关键观察应尽量包含：

- Evidence ID；
- 人类可读 label；
- `quote_snapshot`；
- 来源定位 `locator`；
- 完整性 `integrity`；
- 可点击 `href`。

优先使用相对于输出 HTML 的文件路径和稳定锚点。没有稳定锚点时保留行号、时间戳或页码，并显示 `needs_anchor` / `needs_locator`，不要伪造链接。

### 7. 验证结果

至少检查：

1. `scripts/build_review_from_md.py` 与 `scripts/render_review.py` 均成功完成且退出码为 0；
2. HTML 包含嵌入后的 Review ID 和标题；
3. JavaScript 语法有效；
4. 关键判断可追溯到观察和证据；
5. 问题显示阻塞对象；
6. 关系悬浮（观察 ↔ 推断 / 判断 / 方向）双向可查，且所有关系引用都能查到内容；
7. 若可使用浏览器测试，检查桌面端、移动端、证据悬浮、核验依据悬浮、ID 审计模式和横向溢出。

## 继承式重启流程

```text
Review v1 运行中
→ 出现新信息
→ 判定 execution_impact
   ├─ none：当前 Review 继续
   ├─ potential：当前 Review 继续，记录待回写风险
   └─ blocking：暂停 Review，冻结受影响执行范围
→ 回写 OFDD，生成 OFDD 新版本
→ 基于上一轮成果 + 新 OFDD 生成 Review v2
→ 只重算受影响链路
→ 由新的 Review Gate 决定执行恢复范围
```

`Review v2` 不是新的独立 Review，而是同一 `review_id` 的继承式续轮。

## 输出页面的最低要求

- 第一屏回答：这次要决定什么、当前怎么看、最大不确定性、建议是什么；
- 判断链支持 `Judgment → Inference → Observation → Evidence` 追溯；
- 证据默认显示 label，悬停显示短原文，点击打开完整来源；
- 问题按阻塞性展示；
- 至少真实比较两个方向；若只有一个方向，说明为什么没有替代方案；
- 建议方向与 Decision 分开；
- 展示未决事项、重评条件和 OFDD 回写清单；
- 支持打印 / PDF 和移动端阅读；
- 普通视图隐藏裸 ID，审计模式可显示。

## 决策安全与执行协作规则

- 输入 Decision 为 `proposed` 时，页面只能显示“拟议 / 待决策”，不能显示“已拍板”。
- 输入没有正式 Decision 时，仍需提供 `decision` 占位对象，标题写“本次尚未形成正式决定”，状态写“待决策”或“不适用”。
- 阻塞性问题未解决时，不得暗示对应范围可以进入执行。
- 执行层只读取 OFDD 的已批准版本；Review 中的新增内容不能直接改执行计划或任务状态。
- `execution_impact: none`：当前 Review 可继续；`potential`：可继续但保留风险并回写；`blocking`：暂停当前 Review、冻结受影响执行范围并立即回写 OFDD。
- 新信息不得覆盖旧证据；应进入 `extra_*` / `writeback`，由上游 OFDD 更新后再生成下一版 Review。
- 下一版 Review 必须保留同一 `review_id`，递增 `review_version`，填写 `parent_review_id`、`resumes_from_review_id` 和 `inherited_artifacts`；这叫继承式重启，不是第一次激活或清空式重开。
- 继承式重启只重算受影响链路；未受影响的目标、范围、结论、决定、未决项和回写清单必须承接。
- 新 OFDD 的 `review_gate` 未明确允许恢复前，不得自动恢复被冻结的执行。

## 资源

- `assets/review-template-v3.html`：单文件 HTML 通用模块化模板（默认）。
- `assets/review-template.html`：旧 v2 模板（已废弃，仅兼容）。
- `scripts/build_review_from_md.py`：从 review.md + OFDD JSON 自动筛选生成 Review 视图 JSON。
- `scripts/build_review_view.py`：旧全量映射脚本（已废弃，仅兼容）。
- `scripts/render_review.py`：把 Review 视图 JSON 嵌入模板。
- `references/review-md-format.md`：review.md 配置格式说明。
- `references/review-data-contract.md`：Review View JSON（v3 契约）的应用层字段说明。
- `references/ofdd-to-review-mapping.md`：OFDD JSON 到 Review View JSON 的筛选映射与自动补链规则。
- `references/review-generation-rules.md`：Review 生成、表达、执行与回写规则。
