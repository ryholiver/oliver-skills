# 端到端场景工作流

## 场景 1：快速问答（最常用）

用户说：「Manus 的商业模式是什么？」

```python
# 1. 已知笔记本，直接查
notebook_query(
    notebook_id="ff7f96b4-...",
    query="Manus 的商业模式是什么"
)

# 2. 返回答案 + citations → 呈现给用户
# 格式：
# 答案要点...
# > 引用原文 —— 来源名称
```

---

## 场景 2：不确定用哪个笔记本

用户说：「帮我找一下关于提示词工程的内容」

```python
# 1. 先列出笔记本
notebook_list()

# 2. 看标题，选「经典大模型提示词工程技术路线综述」
# 3. 查询
notebook_query(
    notebook_id="928acd11-...",
    query="提示词工程的主要技术和路线"
)
```

---

## 场景 3：追问（多轮对话）

```python
# 第一轮
result1 = notebook_query(notebook_id="...", query="Manus 的优势是什么")
conv_id = result1["conversation_id"]

# 第二轮，使用同一个 conversation_id 保持上下文
result2 = notebook_query(
    notebook_id="...",
    query="那它的劣势和风险呢？",
    conversation_id=conv_id
)
```

---

## 场景 4：添加新资料后查询

用户说：「把这篇文章加进去，然后问 X」

```python
# 1. 添加来源
source_add(
    notebook_id="...",
    source_type="url",
    url="https://example.com/article"
)

# 2. 等待处理（通常几秒）

# 3. 查询（新来源已可用）
notebook_query(notebook_id="...", query="X")
```

---

## 场景 5：研究调研工作流

用户说：「帮我调研 Agent 最新进展，加入到我的 AI 笔记本」

```python
# 1. 启动深度研究
result = research_start(
    notebook_id="...",
    query="AI Agent 2025 最新进展",
    source="web",
    mode="deep"  # 深度模式，约 5 分钟，~40 个资料
)
task_id = result["task_id"]

# 2. 轮询状态（告知用户需要等待）
research_status(notebook_id="...", task_id=task_id)

# 3. 状态为 completed 后导入
research_import(notebook_id="...", task_id=task_id)

# 4. 告知用户已导入 N 个资料，可以开始提问
```

---

## 场景 6：生成学习材料全套

用户说：「帮我基于提示词工程那本笔记本生成学习材料」

```python
nb_id = "928acd11-..."

# 学习报告
studio_create(notebook_id=nb_id, artifact_type="report",
              report_format="Study Guide", confirm=True)

# 测验（10 题，中等难度）
studio_create(notebook_id=nb_id, artifact_type="quiz",
              question_count=10, difficulty="medium", confirm=True)

# 闪卡
studio_create(notebook_id=nb_id, artifact_type="flashcards",
              difficulty="medium", confirm=True)

# 思维导图
studio_create(notebook_id=nb_id, artifact_type="mind_map", confirm=True)

# 所有任务是异步的，统一检查状态
studio_status(notebook_id=nb_id)
```

---

## 场景 7：跨笔记本综合研究

用户说：「综合我所有笔记本，告诉我 AI Agent 的核心观点」

```python
cross_notebook_query(
    query="AI Agent 的核心观点和未来趋势",
    all=True
)

# 返回每个笔记本各自的答案，按本分组呈现
```

---

## 场景 8：批量生成播客

用户说：「把我所有带 'ai' 标签的笔记本都生成播客」

```python
# 先确认标签下有哪些笔记本
tag(action="list")

# 批量生成
batch(
    action="studio",
    artifact_type="audio",
    audio_format="deep_dive",
    tags="ai",
    confirm=True
)
```

---

## 场景 9：一键摄入 + 播客

用户说：「把这个链接的内容做成播客放进我的笔记本」

```python
# 使用内置流水线，一步完成「摄入 + 生成播客」
pipeline(
    action="run",
    notebook_id="...",
    pipeline_name="ingest-and-podcast",
    input_url="https://example.com/article"
)
```

---

## 场景 10：整理知识库（标签管理）

```python
# 给笔记本添加标签
tag(action="add", notebook_id="928acd11-...", tags="prompting,llm,study")
tag(action="add", notebook_id="ff7f96b4-...", tags="agent,manus,product")

# 按标签查询
cross_notebook_query(query="大模型的核心技术", tags="llm,prompting")

# 批量操作同标签笔记本
batch(action="query", query="最重要的结论是什么", tags="agent")
```

---

## 呈现引用的推荐格式

```markdown
根据您的笔记本资料，[答案要点]...

**关键引用：**
> [原文引用片段] —— 《笔记本标题》

[进一步解释或补充...]
```

如果跨笔记本：
```markdown
**来自《笔记本A》：**
[答案] > [引用]

**来自《笔记本B》：**
[答案] > [引用]

**综合结论：**
[综合分析]
```
