# 通过文件系统保存笔记

**适用环境**：Cowork/Code 环境，或 Chat 环境但 obsidian-mcp-tools 不可用时的兜底方案

---

## 第一步：Vault 路径配置

### 1.1 尝试读取已保存的配置

尝试读取配置文件：
- Mac 配置路径：`~/.obsidian-saver-config`
- Windows 配置路径：`%USERPROFILE%\.obsidian-saver-config`

如果文件存在且包含有效的 `vault_path`，直接使用，**跳到第二步**。

### 1.2 检测操作系统

若配置文件不存在，执行命令判断系统类型：

```bash
# Mac/Linux
uname -s  # 返回 Darwin

# Windows
echo %OS%  # 返回 Windows_NT
```

### 1.3 引导用户配置 vault 路径

**Mac 示例提示：**
```
🗂️ 检测到你的系统是 macOS。
请告诉我你的 Obsidian vault 路径，例如：
  /Users/你的用户名/Documents/MyVault
  /Users/你的用户名/Desktop/我的知识库

你的 vault 路径是？
```

**Windows 示例提示：**
```
🗂️ 检测到你的系统是 Windows。
请告诉我你的 Obsidian vault 路径，例如：
  C:\Users\你的用户名\Documents\MyVault
  D:\ObsidianVault\我的知识库

你的 vault 路径是？
```

### 1.4 验证并保存配置

用户提供路径后：

1. 用 `view` 验证该路径是否可访问
2. 路径有效后，将配置写入本地文件：

```bash
# Mac
create_file(
  path: ~/.obsidian-saver-config
  content: vault_path=/Users/你的用户名/Documents/MyVault
)

# Windows
create_file(
  path: %USERPROFILE%\.obsidian-saver-config
  content: vault_path=C:\Users\你的用户名\Documents\MyVault
)
```

3. 告知用户："✅ 已记住你的 vault 路径，下次无需重新配置。如需修改，请说「更新 vault 路径」。"

---

## 第二步：完整路径拼接

根据系统类型和已确认的 vault 根目录，拼接写入路径：

**Mac 格式：**
```
{vault_path}/{编号}_{一级目录}/{二级目录}/{文件名}.md
```
示例：`/Users/simin/Documents/MyVault/01_AI产品经理/方法论与认知/20250330-001-AI产品-PRD方法论.md`

**Windows 格式：**
```
{vault_path}\{编号}_{一级目录}\{二级目录}\{文件名}.md
```
示例：`C:\Users\simin\Documents\MyVault\01_AI产品经理\方法论与认知\20250330-001-AI产品-PRD方法论.md`

> ⚠️ Windows 路径注意：在 `create_file` 的 path 参数中，可以使用正斜杠 `/` 替代反斜杠 `\`，大多数工具兼容。

---

## 第三步：写入前检查

1. 用 `view` 检查目标目录是否存在
2. 不存在则用 `bash_tool` 的 `mkdir -p` 创建（包括中间层级目录）
3. 用 `view` 在目标目录下查找当天日期前缀的文件，确定编号

示例：
```bash
# 创建目录（Mac）
mkdir -p "/Users/simin/Documents/MyVault/01_AI产品经理/方法论与认知"

# 创建目录（Windows，使用正斜杠兼容）
mkdir -p "C:/Users/simin/Documents/MyVault/01_AI产品经理/方法论与认知"
```

---

## 第四步：交互确认并写入

**严格遵循以下流程，不可跳过确认步骤：**

1. 生成完整笔记内容
2. 在对话中展示给用户，包括：
   - 📁 目标路径（含完整绝对路径）
   - 🏷️ 标签列表
   - 🔗 双向链接列表
   - 📝 笔记全文预览
3. 询问用户："这个内容和分类可以吗？需要调整什么？"
4. **用户确认后**，使用 `create_file` 写入文件
5. 写入后用 `view` 回读确认，告知用户"已成功写入"并给出完整路径

### 写入示例

**Mac：**
```javascript
create_file({
  path: "/Users/simin/Documents/MyVault/01_AI产品经理/方法论与认知/20250330-001-AI产品-PRD方法论.md",
  file_text: "（笔记全文内容）",
  description: "保存笔记到 Obsidian vault"
})
```

**Windows：**
```javascript
create_file({
  path: "C:/Users/simin/Documents/MyVault/01_AI产品经理/方法论与认知/20250330-001-AI产品-PRD方法论.md",
  file_text: "（笔记全文内容）",
  description: "保存笔记到 Obsidian vault"
})
```

---

## 路径更新指令

若用户说出以下任意表达，触发路径重新配置流程（回到第一步的 1.3）：
- "更新 vault 路径"
- "换一个 vault"
- "修改保存路径"
- "我换电脑了"
- "路径变了"

---

## 优势

- ✅ 无需 Obsidian 运行
- ✅ 全平台通用（Mac/Windows/Linux）
- ✅ 配置一次永久有效

## 限制

- ⚠️ 需要用户手动提供 vault 路径（仅首次）
- ⚠️ 保存后需手动在 Obsidian 中刷新查看
