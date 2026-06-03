# MCP 工具完整参数参考

所有工具前缀：`mcp__NotebookLM_MCP_Server__`

## 认证

### refresh_auth
重新加载认证 token（无参数）。Cookie 过期时先调用这个，失败再提示 `nlm login`。

### save_auth_tokens
手动保存认证（备用方案）：
- `cookies` (必填): Chrome DevTools 复制的 Cookie 字符串
- `request_body` (可选): 含 CSRF token 的请求体
- `request_url` (可选): 含 session ID 的请求 URL

---

## 笔记本

### notebook_list
- `max_results` (默认 100): 返回最多笔记本数

### notebook_create
- `title` (必填): 笔记本标题

### notebook_get
- `notebook_id` (必填)

### notebook_describe
- `notebook_id` (必填): 返回 AI 自动生成的内容摘要和建议标签

### notebook_query ⭐ 核心 RAG 工具
- `notebook_id` (必填)
- `query` (必填): 问题
- `source_ids` (可选): 限定特定来源 ID 列表
- `conversation_id` (可选): 追问时传入上次返回的 conversation_id
- `timeout` (默认 120s): 超时时间

### notebook_rename
- `notebook_id` (必填)
- `title` (必填): 新标题

### notebook_delete
- `notebook_id` (必填)
- `confirm` (必填, True): 防止误删

---

## 来源管理

### source_add ⭐ 核心摄入工具
- `notebook_id` (必填)
- `source_type` (必填): `url` / `text` / `file` / `drive`
- `url`: 网页或 YouTube URL（source_type=url 时）
- `text`: 文本内容（source_type=text 时）
- `title`: 来源标题（source_type=text 时建议填写）
- `file_path`: 本地文件路径（source_type=file 时）
- `document_id`: Google Drive 文档 ID（source_type=drive 时）
- `doc_type`: `doc` / `slides` / `sheets` / `pdf`（source_type=drive 时）

### source_describe
- `notebook_id` (必填)
- `source_id` (必填): 返回 AI 摘要和关键词

### source_get_content
- `notebook_id` (必填)
- `source_id` (必填): 返回来源的原始文本内容

### source_rename
- `notebook_id` (必填)
- `source_id` (必填)
- `new_title` (必填)

### source_delete
- `notebook_id` (必填)
- `source_id` (必填)
- `confirm` (必填, True)

### source_list_drive
- `notebook_id` (必填): 列出 Drive 来源及新鲜度状态

### source_sync_drive
- `notebook_id` (必填)
- `confirm` (必填, True): 同步所有过期的 Drive 来源
- `source_ids` (可选): 只同步特定来源

---

## 研究发现

### research_start
- `notebook_id` (必填)
- `query` (必填): 研究主题
- `source` (默认 "web"): `web` 或 `drive`
- `mode` (默认 "fast"): `fast`（~30秒）或 `deep`（~5分钟）

### research_status
- `notebook_id` (必填)
- `task_id` (可选): 查特定任务，不填查最新

### research_import
- `notebook_id` (必填)
- `task_id` (必填)
- `indices` (可选): 只导入特定索引，如 `[0,2,5]`，不填导入全部
- `timeout` (默认 300s): 大型笔记本可调至 600

---

## 内容生成（Studio）

### studio_create ⭐ 内容生成核心
- `notebook_id` (必填)
- `artifact_type` (必填): 见下表
- `confirm` (必填, True)
- `source_ids` (可选): 限定来源
- `language` (可选): BCP-47 语言代码，如 "zh-CN", "en"
- `focus_prompt` (可选): 生成焦点提示

| artifact_type | 专属参数 |
|--------------|---------|
| `audio` | `audio_format`: deep_dive/brief/critique/debate; `audio_length`: short/default/long |
| `video` | `video_format`: explainer/brief; `visual_style`: auto_select/classic/whiteboard/kawaii/anime/watercolor/retro_print/heritage/paper_craft |
| `report` | `report_format`: "Briefing Doc"/"Study Guide"/"Blog Post"/"Create Your Own"; `custom_prompt`（Create Your Own 时） |
| `quiz` | `question_count`（默认 2）; `difficulty`: easy/medium/hard |
| `flashcards` | `difficulty`: easy/medium/hard |
| `mind_map` | `title`（可选） |
| `slide_deck` | `slide_format`: detailed_deck/presenter_slides; `slide_length`: short/default |
| `infographic` | `orientation`: landscape/portrait/square; `detail_level`: concise/standard/detailed; `infographic_style`: auto_select/sketch_note/professional/bento_grid/editorial/instructional/bricks/clay/anime/kawaii/scientific |
| `data_table` | `description`（必填，描述要提取什么数据） |

### studio_status
- `notebook_id` (必填)
- `action` (可选): 默认 "list"，或 "rename"（配合 artifact_id + new_title）
- `artifact_id` (可选): 查特定 artifact

状态值：`completed` ✓ / `in_progress` ● / `failed` ✗

### studio_revise（修改幻灯片）
- `artifact_id` (必填): 从 studio_status 获取
- `slide_instructions` (必填): 修改指令，格式 `"1 加大标题字号"`（1-based 页码）
- `confirm` (必填, True)
- 注意：生成新 artifact，原始不变

### studio_delete
- `notebook_id` (必填)
- `artifact_id` (必填)
- `confirm` (必填, True)

### download_artifact
- `notebook_id` (必填)
- `artifact_type` (必填): audio/video/report/slide_deck/quiz
- `output_path` (必填): 保存路径
- `format` (可选): slide_deck 支持 pdf/pptx；quiz 支持 json

### export_artifact（导出到 Google Docs/Sheets）
- `notebook_id` (必填)
- `artifact_id` (必填)
- `export_type` (必填): "docs" 或 "sheets"
- `title` (可选): 导出文件标题

---

## 聊天配置

### chat_configure
- `notebook_id` (必填)
- `goal` (必填): `default` / `learning_guide` / `custom`
- `custom_prompt` (goal=custom 时): 自定义行为提示
- `response_length` (可选): `shorter` / `default` / `longer`

---

## 笔记

### note
- `notebook_id` (必填)
- `action` (必填): `create` / `list` / `update` / `delete`
- `content`: 笔记内容（create/update 时）
- `title`: 笔记标题（create 时）
- `note_id`: 笔记 ID（update/delete 时）
- `confirm`: True（delete 时必填）

---

## 批量操作

### batch
- `action` (必填): `query` / `add_source` / `create` / `delete` / `studio`
- 目标选择（三选一）:
  - `notebook_names`: "笔记本A, 笔记本B"（逗号分隔）
  - `tags`: "ai,research"
  - `all`: True（全部笔记本）
- 按 action 的专属参数：
  - query: `query`
  - add_source: `source_url` / `source_text` / `source_title`
  - create: `titles`（逗号分隔标题列表）
  - delete: `confirm=True`
  - studio: `artifact_type` + `confirm=True`

---

## 跨笔记本查询

### cross_notebook_query
- `query` (必填)
- 目标选择（三选一）:
  - `notebook_names`: "笔记本A, 笔记本B"
  - `tags`: "ai,research"
  - `all`: True

---

## 标签

### tag
- `action` (必填): `add` / `remove` / `list` / `select`
- `notebook_id`: add/remove 时必填
- `tags`: "tag1,tag2"（add/remove 时）
- `query`: 搜索词（select 时）

---

## 流水线

### pipeline
- `action` (必填): `list` / `run`
- `notebook_id`: run 时必填
- `pipeline_name`: `ingest-and-podcast` / `research-and-report` / `multi-format`
- `input_url` (可选): ingest-and-podcast / research-and-report 时的 URL

---

## 分享

### notebook_share_status
- `notebook_id` (必填)

### notebook_share_public
- `notebook_id` (必填)
- `enabled` (默认 True): False 为关闭公开链接

### notebook_share_invite
- `notebook_id` (必填)
- `email` (必填)
- `role` (默认 "viewer"): `viewer` / `editor`

### notebook_share_batch
- `notebook_id` (必填)
- `emails` (必填): 邮件列表
- `role` (默认 "viewer")

---

## 服务器信息

### server_info
无参数。返回版本号、是否有更新、更新命令。
