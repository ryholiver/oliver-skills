---
name: okr-feishu
description: 用飞书多维表格完成 OKR 制定→写入→执行→复盘全流程。串联 goals:setting-okrs-goals（制定方法论，产出数字中转站 JSON）与 feishu:lark-base（写入多维表格）。当用户说「设定我的 OKR」「把 OKR 写进多维表格」「用 Base 做 OKR」「OKR 制定并入库」「更新 OKR 进度」时使用。
---

# OKR → 飞书多维表格（okr-feishu）

个人 OKR 的制定与入库编排层：把「制定」和「写入」两个 skill 串起来。

## 前置

- 依赖 `lark-cli` 与 base scope。未认证时按 `feishu:lark-shared` 的流程发起授权：`lark-cli auth login --domain base`（agent 场景用 `--no-wait --json` 分步）。
- 目标 Base：🟡 个人 OKR 执行与复盘（`BCC3bXivFaq2DBs1UbucpyWvn3c`）。用户给其它链接时先用 `lark-cli wiki +node-get --as user --token <链接>` 解析 `data.obj_token`。
- **模型物化**：数据模型是演进中的用户数据，**不在 skill 内**。默认工作副本位于【当前目录隐藏文件夹】`.okrsetting/okr-model.json`。开始前先执行 `references/setup.sh --ensure-model`：`.okrsetting/` 无模型时自动从 seed（`references/okr-model.default.json`）复制一份（只增不覆盖，skill 更新不会动它）。之后所有读写都以这份工作副本为准。
- **模型优先**：默认读写按工作副本 `okr-model.json` 的字段映射执行，**不每次读表**。模板结构有变化时，先跑「模式 D · 同步数据模型」（或 `/okr-sync`）。

## 模式

### 模式 A · 制定并写入（核心）

1. 调用 `goals:setting-okrs-goals`，得到其**输出契约**中的「数字中转站 JSON」。
2. 先确保模型就绪：`.okrsetting/` 无 `okr-model.json` 则跑 `references/setup.sh --ensure-model`。再按工作副本 `.okrsetting/okr-model.json` 把中转站 JSON 映射到实际表字段：
   - 必需字段缺失 → 问用户跑 `/okr-sync`，或允许 `+field-create` 增量新增（只增不改不删）；
   - 可选字段缺失 → 跳过。
3. 用 `feishu:lark-base` 写入（全程 `--as user`）：
   a. 先在「目标管理」建每条 O 记录（`+record-upsert`，字段 `季度`+`O`），拿到 `record_id`；
   b. 再在「OKR」表 `+record-batch-create` 批量建 KR：`目标` 字段写 `[{"id":"<O record_id>"}]`，其余按模型映射（`OKR`/`季度`/`状态`/`负责人`/`开始时间`/`完成时间`）；
   c. 负责人 `user` 字段写 `[{"id":"ou_xxx"}]`；未知 open_id 用 `lark-cli contact +search-user --query <姓名> --as user` 查；默认本人 `ou_7c81df7a7e93d9c5cd5679d54e908004`。
4. 返回 Base 链接 + 写入清单（每条 O 及对应 KR）。

### 模式 B · 更新进度 / 复盘

按 季度 / 目标 定位记录（`+record-search` / `+record-list`），用 `+record-batch-update` 更新 `状态` / `完成时间`；复盘内容写入 OKR 表复盘列（`复盘：做的好的` / `复盘：有待提升`）或「复盘」表。

### 模式 C · 一键对齐当前周期

运行 `references/setup.sh`：补当前季度选项、可选清理示例、落结构快照（幂等，可每季度复跑）。

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

- **模型在用户侧**：工作副本 `okr-model.json` 默认在【当前目录 `.okrsetting/`】，不在 skill 里（skill 只有 seed `references/okr-model.default.json`）。缺失时用 `setup.sh --ensure-model` 物化。
- **模型优先**：默认用工作副本 `okr-model.json`，不每次读表（省时）。
- **只增不改不删**：写表 / 同步都只增量；不删字段、不改类型、不覆盖已有值，历史快照保留。
- **写失败回退**：写记录报「字段不存在 / 字段名不匹配」→ 停止重试，提示用户跑 `/okr-sync`，或直接自动跑同步后重试。
- **演进钩子**：模板出现模型外的新字段（如 量化指标 / 目标值 / 当前值 / 权重）→ 自动纳入可选写入，并提示可升级进工作副本 `okr-model.json`。

## 相关

- `references/okr-model.default.json` — seed 模板（skill 内基线，只读）；`.okrsetting/okr-model.json` — 演进中的工作副本（默认读写依据）
- `references/setup.sh` — 一键脚本（`--ensure-model` 物化 / `--sync-model` / `--ensure-fields` / `--clean-samples`）
- `references/schema.md` — 基线表结构 + 演进规则说明
