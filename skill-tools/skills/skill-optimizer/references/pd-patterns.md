# 渐进式披露重构模式库

当审查诊断出问题后，根据问题类型选择对应的重构模式执行。

---

## 模式 1：分支提取（Branch Extraction）

**适用场景**：SKILL.md 中有多个大型 `if/else` 分支，每个分支有专属的详细步骤。

**原则**：SKILL.md 只保留分支判断逻辑和入口指针，细节移到独立 references 文件。

**重构前（SKILL.md）**：
```markdown
## 模式A：新增目录
触发条件：...
步骤1：读取 directory-map.md
步骤2：向用户确认以下信息（20行详细说明）
步骤3：执行重命名（15行操作说明）
...

## 模式B：调整顺序
触发条件：...
步骤1：展示当前目录（10行）
步骤2：用户确认后重排（20行）
...
```

**重构后（SKILL.md）**：
```markdown
## 分支路由

- 用户说"新增目录" → 读取 `references/mode-add-directory.md` 执行
- 用户说"调整顺序" → 读取 `references/mode-reorder-directory.md` 执行
- 用户说"同步目录" → 读取 `references/mode-sync-directory.md` 执行
```

**新增文件**：`references/mode-add-directory.md`（完整步骤）、`references/mode-reorder-directory.md`、`references/mode-sync-directory.md`

---

## 模式 2：初始化提取（Init Extraction）

**适用场景**：有"首次使用"初始化流程，每次调用都会载入但大部分情况下不需要执行。

**重构前（SKILL.md）**：
```markdown
## 第七步：执行写入

### 7.0 Vault 路径初始化（首次使用必读）

步骤一：尝试读取已保存的配置
（10行）

步骤二：检测操作系统
（10行代码示例）

步骤三：引导用户配置 vault 路径
（20行提示文本）

步骤四：验证并保存配置
（15行）

步骤五：路径更新指令
（10行）

步骤六：初始化 directory-map.md
（40行，含完整默认内容）
```

**重构后（SKILL.md）**：
```markdown
## 执行写入前的准备

**Vault 路径确认**：
- 尝试读取 `~/.obsidian-saver-config` 中已保存的路径
- 如果文件不存在，或用户说"更新路径/换vault"，读取 `references/init.md` 执行初始化
- 路径确认后，继续写入流程
```

**新增文件**：`references/init.md`（完整初始化流程 + 默认 directory-map 内容）

---

## 模式 3：模板外置（Template Externalization）

**适用场景**：SKILL.md 中有大段输出模板（Markdown、代码块等）。

**重构前（SKILL.md）**：
```markdown
## 第四步：生成笔记内容

使用以下模板：

​```markdown
---
created: {{YYYY-MM-DD}}
source: Claude对话
tags:
  - {{tag1}}
（以下还有30行模板内容）
​```

### 各区块使用指南
（以下还有25行说明）
```

**重构后（SKILL.md）**：
```markdown
## 生成笔记

读取 `references/note-template.md` 获取完整笔记模板和各区块填写指南，按模板生成笔记内容。
```

**新增文件**：`references/note-template.md`（模板 + 填写说明）

---

## 模式 4：脚本固化（Script Hardening）

**适用场景**：每次调用都有重复性的、确定性的操作逻辑（文件写入、路径拼接、编号递增等）。

**重构前**：每次 Claude 都要重新思考"怎么拼接路径"、"怎么递增编号"、"怎么写入文件"。

**重构后**：创建 `scripts/obsidian_write.py`，接收参数直接执行，Claude 不需要思考实现细节。

**示例脚本接口**（obsidian-knowledge-saver 场景）：
```python
# scripts/obsidian_write.py
# 用法：python scripts/obsidian_write.py \
#   --vault /path/to/vault \
#   --category "01_AI产品经理/方法论与认知" \
#   --title "PRD写作方法论" \
#   --content-file /tmp/note_content.md \
#   --tags "AI产品,方法论"

# 脚本内部处理：
# 1. 读取当天已有文件数量，确定编号（001, 002...）
# 2. 生成文件名：YYYYMMDD-NNN-主题-细节.md
# 3. 拼接完整路径（Mac/Windows 兼容）
# 4. 确保目录存在（自动创建）
# 5. 写入文件
# 6. 输出写入结果（路径 + 是否成功）
```

**SKILL.md 中的调用方式**：
```markdown
## 写入文件

将笔记内容写入临时文件 `/tmp/note_content.md`，然后执行：
​```bash
python {skill_path}/scripts/obsidian_write.py \
  --vault {vault_path} \
  --category "{分类路径}" \
  --title "{笔记标题}" \
  --content-file /tmp/note_content.md \
  --tags "{标签列表}"
​```
```

---

## 模式 5：参考分层（Reference Layering）

**适用场景**：`references/` 文件本身也很大，需要进一步分层。

**结构示例**：
```
references/
├── index.md                ← 简短目录，说明各文件用途（<20行）
├── mode-write.md           ← 写入模式（按需读取）
├── mode-directory.md       ← 目录管理（按需读取）
├── init.md                 ← 初始化（首次读取）
└── note-template.md        ← 笔记模板（生成时读取）
```

`references/index.md` 内容示例：
```markdown
# References 目录

- `init.md`：首次使用时的 Vault 路径配置和目录初始化
- `note-template.md`：笔记生成模板和各区块填写规范
- `mode-directory.md`：目录管理三种模式（新增/调整/同步）的详细步骤
- `note-writing.md`：标签策略和双向链接建立规范
```

---

## 执行重构时的注意事项

1. **先画新结构图**，经用户确认后再动文件
2. **不改功能逻辑**，只是把内容从一个文件搬到另一个文件，并在 SKILL.md 中留好指针
3. **保留关键决策在 SKILL.md**：什么时候进入什么模式、什么时候读什么 references 文件——这些判断逻辑必须留在 SKILL.md，不能迁移
4. **测试指针可达性**：重构后在 SKILL.md 中，每个 references/ 文件都应该有明确的触发条件和读取时机
5. **对比行数**：重构前后分别统计 SKILL.md 行数，确认确实压缩了
