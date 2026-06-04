# 可选模块：状态管理设计

**适用条件**：满足以下任一条件时读取本文件
- 工作流 > 4 步，且有多个"等待用户确认"节点
- 预期任务会跨越打断或多次对话
- 涉及跨 skill 调用（参数型或上下文型）

---

## 状态标注格式

不只是"在第几步"，而是"步骤 + 到此确认的所有关键变量"：

```
[STATE:{skill名} | step:X/N | {变量1}:{值} | {变量2}:{值} | pending:{待执行}]
```

示例：
```
[STATE:obsidian-saver | step:3/5 | vault:/Users/simin/vault | cat:01_AI/方法论 | pending:user_confirm]
```

**放置位置**：回复末尾（步骤完成后状态才确定，末尾最新且最易定位）。

---

## 两种实现方案

**Chat 环境 → 文字标注**（唯一可用方案）
每个等待节点结束时输出 STATE 标注，依赖 Claude 扫描对话历史恢复。

**Cowork 环境 → 文件存储**（推荐，成本固定）
```bash
# 保存
python {skill_path}/scripts/save_state.py save \
  --skill {skill名} --step X --data '{"var1":"val1"}'

# 恢复
python {skill_path}/scripts/save_state.py load --skill {skill名}
```

文件存储不依赖对话长度，恢复成本固定为一次 Read，比扫描长对话省 token。

---

## 在 SKILL.md 里的写法

状态管理声明放在 SKILL.md 的"流程状态管理"区块（不超过 8 行）：

```markdown
## 流程状态管理
工作流较长时，在每个等待确认节点输出：
[STATE:{skill名} | step:X/N | {关键变量} | pending:{下一步}]

Cowork 环境改用：python scripts/save_state.py save/load
被打断时：完成当前最小步骤 → 输出 STATE → 处理插入 → 提示继续
```

若状态逻辑复杂（如多个变量、多分支状态），可迁移到对应 references/ 工作流文件末尾，SKILL.md 只保留调用指针。
