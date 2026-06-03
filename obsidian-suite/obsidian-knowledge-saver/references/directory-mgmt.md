# 目录管理模式

当用户说出以下任意表达时，进入目录管理模式，**不执行笔记沉淀流程**：

- "管理目录"
- "新增目录" / "新增一级目录 XX"
- "调整目录顺序" / "调整顺序"
- "同步目录"

---

## 模式 A：新增一级目录

**触发**：用户说"新增目录"或"新增一级目录 XX"

**流程：**

1. 读取 `.skill-config/directory-map.md`，展示当前所有一级目录和编号
2. 向用户确认以下信息（一次性提问，不要分多轮）：

   > 📁 新增一级目录确认
   >
   > - **目录名称**：（如未提供，请告诉我）
   > - **排在第几位**：（当前共 N 个一级目录，新目录排在哪？）
   > - **适用内容备注**：这个目录主要存放什么类型的内容？
   >   例如：`理财学习、投资记录、资产配置笔记`

3. 用户确认后执行：
   - 根据插入位置，**重新编排所有受影响目录的编号**（如插入第3位，原03→04，04→05……）
   - 在 vault 中创建新文件夹（含编号前缀，如 `03_新目录名`）
   - 如有编号变更，**重命名 vault 中对应的文件夹**
   - 更新 `.skill-config/directory-map.md`，写入新的完整映射表
   - 告知用户操作结果，列出所有变更的目录名

> ⚠️ 文件夹重命名不会影响已有笔记的内容，只影响文件夹名称。Obsidian 内部链接依赖文件名而非文件夹名，无需担心链接断裂。

---

## 模式 B：调整目录顺序

**触发**：用户说"调整目录顺序"

**流程：**

1. 读取 `.skill-config/directory-map.md`，以列表形式展示当前所有一级目录：

   > 当前目录顺序：
   > 01 - AI产品经理
   > 02 - 课程体系
   > 03 - 个人成长
   > ……
   >
   > 请告诉我新的顺序（可以只说移动哪个到哪，也可以给出完整新顺序）

2. 用户确认新顺序后执行：
   - 重新分配所有编号
   - 重命名 vault 中所有编号有变化的文件夹
   - 更新 `.skill-config/directory-map.md`
   - 告知用户所有重命名操作的列表

---

## 模式 C：同步 vault 与映射表

**触发**：用户说"同步目录"

**流程：**

1. 扫描 vault 根目录，获取实际存在的一级目录列表
2. 与 `.skill-config/directory-map.md` 对比，找出差异：
   - **vault 有但映射表没有**：新文件夹，可能是用户在 Obsidian 里手动创建的
   - **映射表有但 vault 没有**：文件夹被删除或重命名了
3. 展示差异给用户确认：

   > 🔍 检测到以下差异：
   >
   > **vault 中新增（映射表未记录）**：
   > - `10_健康与运动`
   >
   > **映射表中存在但 vault 已删除**：
   > - `08_个人生活/其他`
   >
   > 对于 vault 中的新目录，请告诉我它的适用内容备注，以便加入映射表。

4. 用户补充备注后，更新 `.skill-config/directory-map.md`

---

## 目录操作技术实现

### Chat 环境（obsidian-mcp-tools 可用）
- 列出目录：`obsidian-mcp-tools:list_vault_files(directory: "")`
- 创建文件夹：先创建占位文件，如 `03_新目录/.gitkeep`
- 读取配置：`obsidian-mcp-tools:get_vault_file(filename: ".skill-config/directory-map.md")`
- 更新配置：`obsidian-mcp-tools:create_vault_file(filename: ".skill-config/directory-map.md", content: "...")`

### Cowork/Code 环境（纯文件系统）
- 列出目录：`view {vault_path}`
- 创建文件夹：`bash_tool: mkdir -p "{vault_path}/03_新目录"`
- 重命名文件夹：`bash_tool: mv "{vault_path}/03_旧名" "{vault_path}/04_旧名"`
- 读取配置：`view {vault_path}/.skill-config/directory-map.md`
- 更新配置：`create_file(path: "{vault_path}/.skill-config/directory-map.md", content: "...")`

---

## 注意事项

- 永远不要在用户确认之前重命名文件夹或修改配置文件
- 目录管理操作完成后，回到主模式，提示用户"目录管理完成，现在可以沉淀笔记了"
