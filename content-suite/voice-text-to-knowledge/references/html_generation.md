# HTML 知识地图：生成与进度更新

> 本文件在 Step 2 生成 HTML、Step 4 更新进度时读取，其余步骤无需加载。

---

## 生成 HTML（Step 2 末尾）

知识地图 .md 文件保存后立即执行。

**步骤一**：按 `references/knowledge_map_format.md` 中的 JSON 格式，将知识地图内容组织为 JSON。
可直接构建 JSON 字符串，也可先写入临时文件。

**步骤二**：运行生成脚本

```bash
# 方式A：直接传 JSON 字符串
python scripts/generate_map_html.py \
  --data '{"title":"...","date":"...","groups":[...]}' \
  --output '<工作区>/<文档名>_知识地图.html'

# 方式B：先写临时文件再传入（JSON 较长时用这个）
python scripts/generate_map_html.py \
  --data-file /tmp/map_data.json \
  --output '<工作区>/<文档名>_知识地图.html'
```

生成后脚本自动在浏览器打开文件。告知用户：

> 「HTML 知识地图已生成，浏览器已自动打开。建议保持该页面开着——深聊过程中随时可以切换过去查看全局进度，刷新即可看到最新状态。」

---

## 更新进度（Step 3 开始 + Step 4 结束）

所有进度更新都由代码完成，**不消耗任何 token**，用户刷新浏览器页面即生效。

### 开始深聊一个话题时 → 标为进行中

```bash
python scripts/update_progress.py \
  --html '<工作区>/<文档名>_知识地图.html' \
  --card '<知识点标题关键词>' \
  --status doing \
  --note '<可选：说明卡在哪里，用于跨会话恢复>'
```

### 话题深聊完成、结晶保存后 → 标为已吸收

```bash
python scripts/update_progress.py \
  --html '<工作区>/<文档名>_知识地图.html' \
  --card '<知识点标题关键词>' \
  --status done
```

`--card` 参数支持模糊匹配，只需要标题中的关键词即可（如 `LangGraph`、`Agent编排`）。

### 查看所有卡片 ID 和当前状态

```bash
python scripts/update_progress.py \
  --html '<工作区>/<文档名>_知识地图.html' \
  --list
```

---

## 触发时机总结

| 时机 | 操作 | Token 消耗 |
|---|---|---|
| Step 2 末尾，知识地图生成完 | 生成 HTML | 仅 JSON 构建（小） |
| Step 3 开始，用户选定话题 | `--status doing` | 零 |
| Step 4 末尾，结晶保存完成 | `--status done` | 零 |
| 检测到所有卡片均为 done | 触发 Step 5 清理提示 | 零 |
