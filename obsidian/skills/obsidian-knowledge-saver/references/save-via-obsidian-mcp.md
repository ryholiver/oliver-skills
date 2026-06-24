# 通过 obsidian-mcp-tools 保存笔记

**适用环境**：Chat 环境，且 Obsidian 软件正在运行

---

## 保存流程

### 1. 确认路径格式

obsidian-mcp-tools 使用**相对 vault 根目录的路径**，格式：

```
{编号}_{一级目录}/{二级目录}/{文件名}.md
```

示例：`01_AI产品经理/方法论与认知/20250330-001-AI产品-PRD方法论.md`

### 2. 检查编号

使用 `obsidian-mcp-tools:list_vault_files` 列出目标目录下的文件，查找当天日期前缀的最大编号，新编号为最大编号+1。

示例：
```javascript
// 列出目录
list_vault_files(directory: "01_AI产品经理/方法论与认知")

// 查找当天文件，如发现 20250330-001-xxx.md 和 20250330-002-xxx.md
// 则新编号为 003
```

### 3. 交互确认

**严格遵循以下流程，不可跳过确认步骤：**

1. 生成完整笔记内容
2. 在对话中展示给用户，包括：
   - 📁 目标路径（相对路径）
   - 🏷️ 标签列表
   - 🔗 双向链接列表
   - 📝 笔记全文预览
3. 询问用户："这个内容和分类可以吗？需要调整什么？"
4. **用户确认后**，使用 `obsidian-mcp-tools:create_vault_file` 写入文件
5. 写入成功后告知用户"已成功写入"并给出完整路径

### 4. 写入示例

```javascript
obsidian-mcp-tools:create_vault_file({
  filename: "01_AI产品经理/方法论与认知/20250330-001-AI产品-PRD方法论.md",
  content: "（笔记全文内容）"
})
```

### 5. 错误处理

如果 `create_vault_file` 调用失败（返回错误或超时），说明 Obsidian 未运行或 MCP 连接中断。

此时应告知用户：

> ⚠️ 无法连接到 Obsidian，可能的原因：
> 1. Obsidian 软件未运行
> 2. obsidian-mcp-tools 未正确配置
> 
> 请确保 Obsidian 已打开并正常运行。如果问题持续，可以在 Cowork 或 Code 环境中使用纯代码方式保存（会要求提供 vault 路径）。

---

## 优势

- ✅ 无需手动配置 vault 路径
- ✅ 自动处理跨平台路径问题
- ✅ 保存后 Obsidian 立即同步显示

## 限制

- ⚠️ 需要 Obsidian 软件运行
- ⚠️ 仅在 Chat 环境可用
