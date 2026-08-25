---
name: okr-feishu
description: 用飞书多维表格完成 OKR 制定→写入→执行→复盘全流程。串联 goals:setting-okrs-goals（制定方法论，产出数字中转站 JSON）与 feishu:lark-base（写入多维表格）。当用户说「设定我的 OKR」「把 OKR 写进多维表格」「用 Base 做 OKR」「OKR 制定并入库」「更新 OKR 进度」时使用。
---

# OKR → 飞书多维表格（okr-feishu）

个人 OKR 的制定与入库编排层：把「制定」和「写入」两个 skill 串起来。

## 前置

- 依赖 `lark-cli` 与 base scope。未认证时按 `feishu:lark-shared` 的流程发起授权：`lark-cli auth login --domain base`（agent 场景用 `--no-wait --json` 分步）。
- 目标 Base：🟡 个人 OKR 执行与复盘（`BCC3bXivFaq2DBs1UbucpyWvn3c`）。用户给其它链接时先用 `lark-cli wiki +node-get --as user --token <链接>` 解析 `data.obj_token`。
- **模型物化**：数据模型是演进中的用户数据，**不在 skill 内**。默认工作副本位于【当前目录隐藏文件夹】`.okrsetting/okr-model.json`。开始前先执行 `scripts/setup.sh --ensure-model`：`.okrsetting/` 无模型时自动从 seed（`references/okr-model.default.json`）复制一份（只增不覆盖，skill 更新不会动它）。之后所有读写都以这份工作副本为准。
- **模型优先**：默认读写按工作副本 `okr-model.json` 的字段映射执行，**不每次读表**。模板结构有变化时，先跑「模式 D · 同步数据模型」（或 `/okr-sync`）。

## 操作路由（新操作怎么处理）

模型每次收到 Base 操作需求，先判断走哪条路：

1. **已固化路径**（如模式 A 的 O→KR 写入）→ 直接跑 `scripts/okr-write.sh`，不临场拼命令；
2. **未覆盖的新操作**（建新表 / 加字段 / 读记录 / 模式 B 更新 / 换 Base 等）→ **先调用 `feishu:lark-base` skill** 拿操作指南，再据此操作 lark-cli（全程 `--as user`）；不要跳过指南直接试——这正是首次测试出错的根源；
3. **高频化固化**：同一新操作第二次出现时，向用户提议把它固化进 `scripts/`（像 okr-write.sh 那样），减少每次临场出错。

## 模式

### 模式 A · 制定并写入（核心）

1. 调用 `goals:setting-okrs-goals`，得到其**输出契约**中的「数字中转站 JSON」。
2. **【审核门 · 必停】生成 Obsidian 审核 Markdown，等用户确认**：
   - 中转站 JSON 是**给下游 AI 消费**的数据契约，人不能直接看 JSON。先把 JSON 落成一份 Obsidian 可打开的 Markdown 审核文件：`OKR/check/<周期>/<周期>-okr-review.md`，例如 `OKR/check/2026-Q3/2026-Q3-okr-review.md`。
   - 未获用户明确确认前，**禁止**进入写入步骤（不物化模型、不写表）。
   - 用户提出修改 → 更新中转站 JSON → 重新生成/更新审核 Markdown → 继续在 Obsidian 中审阅，直到用户确认。
3. 确保模型就绪：`.okrsetting/` 无 `okr-model.json` 则跑 `scripts/setup.sh --ensure-model`。按工作副本 `.okrsetting/okr-model.json` 校验字段映射：
   - 必需字段缺失 → 问用户跑 `/okr-sync`，或允许 `+field-create` 增量新增（只增不改不删）；
   - 可选字段缺失 → 跳过。
4. **写入**：把中转站 JSON 存成临时文件，运行 `scripts/okr-write.sh --relay <relay.json> [--dry-run]`（全程 `--as user`）。脚本自动处理本次测试踩过的三个坑：
   - **link/user 字段按模型 `cell_shape` 自动数组包裹**（写 `[{"id":"..."}]`，不再手拼）；
   - **批量 payload 走当前目录 `.okrsetting/tmp/` 相对路径** 传给 `lark-cli`（`@-` stdin 与绝对路径都会被拒）；
   - **`--dry-run` 只校验+预览不写表**（模型缺必需字段 / 值形状不匹配就报错），建议真写前先跑一次。
   脚本不渲染审核视图、不物化模型——那是上面步骤的职责；它只负责把已确认的中转站 JSON 落表。审核文件本身应先由上游步骤写成 Obsidian 的 Markdown 再确认。
5. 返回 Base 链接 + 写入清单（每条 O 及对应 KR）。

#### 审核文件（Obsidian Markdown 模板）

审核门（第 2 步）生成的文件，默认保存到 `OKR/check/<周期>/<周期>-okr-review.md`。**这里以 Markdown 文件为准，不再只渲染临时人可读视图。**

**全量展示数据模型字段**：中转站 JSON 里的字段（周期 / 层级 / 负责人 / KR / 类型 / 度量 / 基线→目标 / 状态 / 开始时间 / 完成时间）逐项写入；**缺失的字段标记 ⛔ 并向用户询问**，不允许静默留空。

```markdown
# OKR 审核｜{period}

- 审核工具：Obsidian
- 保存路径：`OKR/check/{period}/{period}-okr-review.md`
- 层级：{level}
- 负责人：{owner 名}

## Objective {序号}｜{objective}

| 序号 | KR（可度量结果） | 类型 | 度量 | 基线→目标 | 状态 | 时间 |
|---|---|---|---|---|---|---|
| 1 | {key_result} | {kr_type} | {metric} | {baseline}→{target} | {status} | {start} ~ {due} |

## 审核问题

- 这条 KR 是否真的是结果，而不是任务？
- 这个目标是否足够鼓舞人心？
- 如果达成但伤害用户体验，是否仍算成功？

## 审核结论

- [ ] 通过
- [ ] 需修改
- [ ] 驳回

## 修改记录

- {date}：首次生成
```

> 缺失字段示例：`状态：未开始｜时间：⛔（未提供，问用户：KR1 的开始/完成时间是什么？）`

展示完成后，明确提示用户：**「请在 Obsidian 中打开这份审核文件，确认后再继续写入。」**


### 模式 B · 更新进度 / 复盘

按 季度 / 目标 定位记录（`+record-search` / `+record-list`），用 `+record-batch-update` 更新 `状态` / `完成时间`；复盘内容写入 OKR 表复盘列（`复盘：做的好的` / `复盘：有待提升`）或「复盘」表。

### 模式 C · 一键对齐当前周期

运行 `scripts/setup.sh`：补当前季度选项、可选清理示例、落结构快照（幂等，可每季度复跑）。

### 模式 D · 同步数据模型（`/okr-sync`）

全量读取模板结构并更新模型。**只读，不改表数据。**

1. `lark-cli base +table-list` + 目标表（目标管理 / OKR）`+field-list`；
2. 与**工作副本** `.okrsetting/okr-model.json`（缺失先物化）diff：
   - 新增字段 → 按语义加入模型（判断 `required/optional`）；
   - 字段改名 → 更新 `preferred_names`；
   - 字段删除 → 标记 `deprecated: true`（保留历史定义，不删）；
3. 更新工作副本 `.okrsetting/okr-model.json`（`version+1`、`updated_at`）+ 落 `.okrsetting/snapshots/snapshot-<日期>.json`；
4. 输出变化摘要（新增 / 变更 / 移除）。

## 演进原则（必读）

- **模型在用户侧**：工作副本 `okr-model.json` 默认在【当前目录 `.okrsetting/`】，不在 skill 里（skill 只有 seed `references/okr-model.default.json`）。缺失时用 `scripts/setup.sh --ensure-model` 物化。
- **模型优先**：默认用工作副本 `okr-model.json`，不每次读表（省时）。
- **只增不改不删**：写表 / 同步都只增量；不删字段、不改类型、不覆盖已有值，历史快照保留。
- **写失败回退**：写记录报「字段不存在 / 字段名不匹配」→ 停止重试，提示用户跑 `/okr-sync`，或直接自动跑同步后重试。
- **演进钩子**：模板出现模型外的新字段（如 量化指标 / 目标值 / 当前值 / 权重）→ 自动纳入可选写入，并提示可升级进工作副本 `okr-model.json`。

## 相关

- `references/okr-model.default.json` — seed 模板（skill 内基线，只读）；`.okrsetting/okr-model.json` — 演进中的工作副本（默认读写依据）。每个字段带 `cell_shape`（`string` / `object_array` / `number` / `boolean`），写入脚本据此决定 CellValue 形状
- `scripts/okr-write.sh` — 写入脚本（模式 A 第 4 步用）：消费中转站 JSON + 工作副本模型，O→KR 落表，`--dry-run` 校验不写
- `scripts/setup.sh` — 一键脚本（`--ensure-model` 物化 / `--sync-model` / `--ensure-fields` / `--clean-samples`）
- `references/schema.md` — 基线表结构 + 演进规则说明
