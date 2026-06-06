---
name: optimize-skill
description: 对一个 skill 文件做迭代执行-反思-修改-验证的自优化循环，产出 optimized best_skill.md。当你对一个 skill 质量不满意、或想系统性提升 skill 的覆盖率和准确率时使用。
---

# Skill Self-Optimizer

一个可自优化的 meta-skill。将 SkillOpt 的评估循环核心逻辑编码为自然语言 skill + 生成式硬约束脚本，让当前 agent 在单会话内对目标 skill 做迭代优化。

## 核心思想

```
初始 skill → epoch 循环:
  ├─ 1. 生成 N 个测试任务（覆盖 skill 描述的目标场景）
  ├─ 2. 用当前 skill 执行所有测试任务，逐条评分
  ├─ 3. 反思失败案例，输出修改建议（不超过编辑预算）
  ├─ 4. 应用修改，重新执行测试任务
  ├─ 5. 比较分数：有提升 → 保留；无提升 → 回滚
  └─ 6. 连续 2 轮无提升 → 停止
↓
输出 best_skill.md
```

## 输入

调用时用户需指定：

- **目标 skill 路径**（必填）：要优化的 skill 文件，如 `pre-coding/skills/scenario-alignment/SKILL.md`
- **测试任务数 N**（可选，默认 5）：每轮生成的测试场景数
- **最大 epoch 数**（可选，默认 5）：最大迭代轮数
- **编辑预算**（可选，默认 3）：每轮最多修改几处

示例：`/optimize-skill pre-coding/skills/scenario-alignment/SKILL.md --tasks 8 --epochs 5 --budget 3`

## 工作流程

### Step 1：读取目标 skill 并理解其职责

读取目标 skill 的完整内容，理解它的：
- 触发条件（name / description）
- 核心工作流程
- 输入输出格式
- 评分标准（如果有）

### Step 2：生成测试任务集

基于 skill 的 description 和工作流程，生成 N 个覆盖主要场景的测试任务。每个测试任务包含：

- 场景描述（模拟用户输入）
- 期望输出标准（什么算"正确"）
- 可验证的检查点（3-5 条）

确保覆盖：成功路径、边界情况、异常输入、空状态。

### Step 3：生成优化脚本并执行

生成一个**临时 bash 脚本**（`optimize-run-<timestamp>.sh`），脚本内实现 epoch 循环，并强制执行以下硬约束。

脚本结构：

```bash
#!/usr/bin/env bash
set -euo pipefail

SKILL_FILE="<目标 skill 路径>"
MAX_EPOCHS=<N>
EDIT_BUDGET=<每轮最大修改数>
TASK_COUNT=<每轮任务数>
OUT_DIR="outputs/skill-optimize-<时间戳>"

mkdir -p "$OUT_DIR"
cp "$SKILL_FILE" "$OUT_DIR/initial.md"
cp "$SKILL_FILE" "$OUT_DIR/current.md"

BEST_SCORE=0
STALE=0

for epoch in $(seq 1 $MAX_EPOCHS); do
  echo "=== Epoch $epoch/$MAX_EPOCHS ==="

  # --- Step A: 用当前 skill 执行测试任务并评分 ---
  # 调用 Claude Code CLI 或直接由 agent 串行执行
  # 输出到 $OUT_DIR/epoch-${epoch}-results.json
  # 包含：每个任务的 pass/fail、分数、失败原因

  # --- Step B: 计算总分 ---
  SCORE=$(<从结果中计算 pass rate>)

  # --- Step C: 如果分数下降，回滚并提前结束 ---
  if (( $(echo "$SCORE < $BEST_SCORE" | bc -l) )); then
    echo "Score dropped ($BEST_SCORE → $SCORE). Reverting."
    cp "$OUT_DIR/best.md" "$OUT_DIR/current.md"
    STALE=$((STALE + 1))
    if [ $STALE -ge 2 ]; then echo "2 rounds no improvement. Stopping."; break; fi
    continue
  fi

  # --- Step D: 更新最佳分数 ---
  BEST_SCORE=$SCORE
  cp "$OUT_DIR/current.md" "$OUT_DIR/best.md"
  STALE=0

  # --- Step E: 分析失败案例并生成修改建议 ---
  # 调用 agent 反思失败案例，输出修改建议

  # --- Step F: 应用修改（编辑预算硬约束） ---
  # 统计修改数量，不超过 EDIT_BUDGET
  # 修改应用到 "$SKILL_FILE"
  # 同时更新 $OUT_DIR/current.md
done

echo "=== Done ==="
echo "Best score: $BEST_SCORE"
echo "Best skill: $OUT_DIR/best.md"
```

脚本执行期间，如果满足以下任一条件则立即停止并回滚：

- 同一验证集上连续 2 轮分数无提升
- 单轮修改数超过编辑预算

### Step 4：回滚与回溯

脚本执行完毕后：

- 如果 `$OUT_DIR/best.md` 存在且分数 > 初始分数 → 用 best.md 覆盖原始 skill 文件
- 否则 → 输出"当前版本已是最优，无需修改"，不覆盖原始文件
- 清理临时脚本

### Step 5：输出优化报告

向用户展示：

- 优化前 vs 优化后的评分对比
- 每轮分数变化曲线
- 主要做了哪些修改（修改摘要）
- 哪些场景得到了改善
- 建议下一步做什么

## 硬约束

### 编辑预算

每轮只允许最多 `budget` 处修改。"一处修改"定义为：对一个连续逻辑段落（3-15 行）的非删除性更改。新增的规则或说明按段落计数。

实现方式：脚本中设置 `EDIT_COUNT=0`，每次编辑前 `EDIT_COUNT++`，达到 `EDIT_BUDGET` 后拒绝更多修改。

### 验证门控

只能在验证集上评分**有提升**时接受本轮修改。判定标准：

- `new_score >= old_score + 0.01`（或至少 1 个额外测试通过）
- 如果分数持平但修改只是修复了文案/格式问题，也可接受
- 任何分数下降都触发回滚

实现方式：脚本保存 `BEST_SCORE` 变量，每轮结束后比较，下降则执行 `git checkout` 或 `cp` 还原。

### 停止条件

- 达到最大 epoch 数（硬上限）
- 连续 2 轮验证分数无提升（早停）

## 优化报告格式

```markdown
# Skill 优化报告: <target-skill-name>

## 评分变化
| Epoch | Score | 操作 |
|-------|-------|------|
| 0 (初始) | xx% | baseline |
| 1 | xx% | 接受/回滚 |
| 2 | xx% | 接受/回滚 |
| ... | ... | ... |

## 修改摘要
- [epoch 1] 修改了 xxx 部分：原因说明
- [epoch 3] 新增了 xxx 规则：原因说明

## 提升场景
- xxx 场景从 fail → pass
- yyy 场景评分从 2/5 → 4/5

## 推荐后续
- 将此 skill 放入更多真实场景测试
- 考虑增加测试任务覆盖更多边界
```

## 禁止行为

- 不要修改目标 skill 的核心职责和触发条件
- 不要删除不可测试但必要的安全/边界说明
- 不要用此 skill 优化自身，避免递归
- 优化结束后必须清理临时脚本文件
- 不要在未经用户确认的情况下覆盖原始文件（除非用户明确要求自动覆盖）

## 已知局限

- **同模型偏见**：反思和执行使用同一个模型，缺乏外部视角。如果优化进入局部最优，可尝试手动调整初始 skill 后重新运行。
- **串行执行**：测试任务逐条执行而非批量并行，小模型下速度较慢。
- **测试覆盖有限**：N 个测试任务不能覆盖真实世界的所有场景。优化后的 skill 建议在实际使用中继续验证。
