---
name: skill-optimizer
description: Skill 渐进式披露审查与重构工具。当用户提到"审查 skill"、"优化 skill 结构"、"skill 太长了"、"skill 消耗 token 太多"、"帮我重构 skill"、"新建 skill 框架"、"skill 设计"时立即触发。也适用于用户说"帮我看看这个 skill 写得好不好"、"这个 skill 能不能减少 token"、"我想创建一个新 skill"、"skill 结构怎么设计"等表达。即使用户只说"帮我看看这个 skill"，只要涉及 skill 结构审查、渐进式披露优化、新 skill 框架设计，都应触发此 skill。
---

# Skill 渐进式披露审查与重构工具

## 三层加载体系（核心认知）

| 层级 | 内容 | 何时加载 |
|------|------|----------|
| 第1层 | `description` 字段 | 永远在 context |
| 第2层 | `SKILL.md` 正文 | skill 触发后全文载入 |
| 第3层 | `references/`、`scripts/`、`assets/` | Claude 主动读取/执行时才载入 |

注：工具定义（MCP、内置工具）属于系统 prompt，第一条消息就全量载入，无法渐进控制。

**设计原则**：SKILL.md 只放路由判断，执行细节推到第3层，按需加载。

**AskUserQuestion 使用规范**：
- 适用：用户需要在有限选项中选择，且选择结果直接决定下一步（如模式选择、格式偏好）
- 不适用：输出大量内容（报告/分析）之后——用户需要消化，等用户自然发起下一步即可
- 调用时不输出前置文字，问题和选项完全在工具内声明

---

## 模式识别与路由

**模式 A：审查现有 Skill**
用户提供一个已有 skill，想了解问题或优化方向
→ 读取 `references/audit-workflow.md` 执行

**模式 B：设计新 Skill 框架**
用户想创建新 skill，尚未开始写内容
→ 读取 `references/design-workflow.md` 执行

**模式 A+B 组合**：先审查诊断，完成后继续重构

**模式不明确时**：用 AskUserQuestion 工具询问：
- A：审查现有 skill（诊断问题 + 优化建议）
- B：设计新 skill 框架（从头开始）
- C：先审查，再直接重构

---

## 执行模式

默认：**计划确认**（本 skill 涉及文件修改，需用户确认）
- 输出诊断/计划 → 讨论调整（可多轮）→ 收到执行信号后才执行 → 简洁变更摘要

**执行确认原则**：没有收到明确的执行信号前，只讨论、不执行。
- 执行信号：「执行」「重构」「做吧」「直接做」「开始」「确认」
- 非执行信号：提问、调整建议、「如果…怎样」、「这里能不能…」——这些属于讨论，继续讨论，不触发执行

用户可覆盖：说"直接做"跳过确认，输出完计划立即执行

---

## 流程状态管理

完整审查+重构步骤较长，每个等待确认节点输出：
```
[STATE:skill-optimizer | target:{skill名} | phase:{audit|plan|execute} | step:X | pending:{下一步}]
```

Cowork 环境改用文件存储（路径：`{skill所在目录}/scripts/save_state.py`）：
```bash
python {skill_path}/scripts/save_state.py save --skill skill-optimizer --step X --data '{"target":"xxx"}'
python {skill_path}/scripts/save_state.py load --skill skill-optimizer
```

被打断时：完成当前最小步骤 → 输出 STATE → 处理插入内容 → 主动提示继续

---

## 渐进式需求处理

最小信息启动：只问当前步骤必需的信息，随工作流推进再按需澄清。
任何步骤都允许修正之前的决定，修正后重新评估后续路径。
