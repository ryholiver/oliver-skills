# OFDD JSON → Review 视图 JSON 筛选映射（v3）

## 1. 适用范围

本文件规定 `build_review_from_md.py` 如何把 OFDD JSON + review.md 配置转换为 Review 视图 JSON（v3 契约）。

```text
review.md（目标 / 版本 / 生命周期 / filter / 模块）
+ OFDD JSON（事实与关系）
→ 自动筛选（include → 补链 → extra 合并 → exclude）
→ 执行影响判定
→ Review 视图 JSON（v3）
→ 通用模板渲染 HTML
```

## 2. 筛选逻辑

### 2.1 include：声明本次任务范围

review.md 的 `filter.include` 显式列出本次任务关注的观察 / 推断 / 判断。这是"本次 Review 要什么"的机械表达。

### 2.2 自动补链（脚本执行）

从 include 出发，沿 OFDD 已有引用关系反复补齐上下游，直到稳定：

```text
判断 → 支撑推断（judgment.supported_by_ids）
推断 → 基于的观察（inference.based_on_observation_ids）
方向 → 依据的判断 / 推断（direction.basis_ids）
判断 / 推断 → 引用它们的 OFDD 方向（当 include.directions 为空时反向推导）
```

保证：进入主体的判断有完整推断依据，推断有完整观察依据，观察有证据引用。

### 2.3 extra_*：本次新增内容

`extra_inferences` / `extra_judgments` / `extra_directions` / `extra_questions` 合并进筛选结果，用于承载本次 Review 现场推导的新内容（候选提效点、新疑问等）。

每个 `extra_*` 必须标注：

- `writeback_status`：默认 `pending`，表示尚未成为 OFDD 事实源；
- `execution_impact`：`none` / `potential` / `blocking`；
- 需要时补充 `affected_scope`，说明影响的决定、方向、计划或执行范围。

分流规则：

- `none`：可以留在当前 Review，不影响 OFDD 或执行；
- `potential`：当前 Review 可以继续，但必须显示风险并纳入回写清单；
- `blocking`：不得仅作为普通候选展示，必须把 Review 标记为 `paused_for_writeback`，先回写 OFDD，再生成继承式重启版本。

### 2.4 exclude：显式排除

`exclude` 在补链完成后按 ID 排除，优先级最高。

### 2.5 疑问筛选

```text
extra_questions（本次任务疑问）
+ OFDD 中阻塞（blocking=true）且 triggered_by_ids 与链路有交集的疑问
```

`blocking_questions_only: true` 时只保留阻塞疑问。

## 3. 字段映射

| OFDD JSON | Review 视图（v3） | 映射规则 |
|---|---|---|
| `observations[].id/content/evidence_ref_ids` | `facts[]` | 筛选后保留；状态由核验阶段填写 |
| `evidence_refs` + `sources` | `facts[].evidence[]` | 证据对象：label / quote / locator / integrity / href |
| `findings.inferences` | `inferences[]` | 保留 OFDD ID 与 based_on 关系 |
| `findings.judgments` | `judgments[]` | 保留评价对象、标准与 supported_by 关系 |
| `directions` | `directions[]` | 按 basis_ids 引用判断 / 推断 |
| `findings.questions` | `questions[]` | 阻塞 + 链路相关；trigger 标注触发来源 |
| `html_review_hints` | 高亮信号 | `highlight: auto` 时取 high_risk_judgments / critical_questions |
| 全部观察 / 推断 / 判断 | `*Pool` | 查询池：供关系悬浮查内容，不受筛选影响 |

## 4. 决策安全与执行影响

- 候选方向、候选推断、候选判断必须标注“待回写”，不得渲染为已拍板；
- 阻塞疑问未解决时，不得暗示对应范围可进入执行；
- 新增内容不覆盖 OFDD 旧证据；先进入 `extra_*`，再依据执行影响决定继续、回写或暂停；
- `execution_impact: none`：Review 可继续，新增内容仍是展示层候选；
- `execution_impact: potential`：Review 可继续，但当前执行需保留风险标记，Review 结束后回写 OFDD；
- `execution_impact: blocking`：Review 暂停、受影响执行冻结，先更新 OFDD，再创建同一 Review 线的下一版本；
- 新版 Review 必须使用 `parent_review_id`、`resumes_from_review_id` 和 `inherited_artifacts` 承接上一版有效成果，只对受影响链路重算；
- HTML 是展示快照，不是事实源。

## 5. 校验

生成后至少校验：

1. 顶层字段符合 v3 契约；
2. `modules` 非空且每个 kind 都有对应渲染器；
3. 每条关系的引用 ID 都能在查询池或主体列表中找到；
4. `exclude` 生效；
5. 候选内容带"待回写"标记；
6. 页面可渲染、关系悬浮可查到内容。
