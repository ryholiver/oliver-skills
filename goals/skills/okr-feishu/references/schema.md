# 个人 OKR 多维表格：基线结构与演进规则

## 概述

- **Base**：🟡 个人 OKR 执行与复盘
- **base_token**：`BCC3bXivFaq2DBs1UbucpyWvn3c`
- **数据模型**：O 记录在「目标管理」表，KR 记录在「OKR」表；「OKR」表的「目标」字段（link）关联到「目标管理」的 O 记录。
- **模型位置**：演进中的工作副本 `okr-model.json` 默认在【当前目录】（不在 skill 内）。skill 只带 seed 模板 `okr-model.default.json`；当前目录无模型时由 `setup.sh --ensure-model` 复制一份。之后所有读写都以工作副本为准，`/okr-sync` 也只更新工作副本。
- **模型优先**：默认读写以工作副本 `okr-model.json` 为准，不每次读表。本文件是**结构基线**的说明。

## 基线表结构（2026-08-16）

### 目标管理（`tbljBIOMT63u4sQz`，role: objectives）

| 字段 | 类型 | 必需 | 说明 |
|---|---|---|---|
| 季度 | select | ✅ | 周期选项 `YYYY-Qn`，当前含 2022-Q1..Q4；`setup.sh` 会按 `CYCLE` 追加当前季度 |
| O | text | ✅ | 目标一句话 |

### OKR（`tblV1ORKFPGs9DBq`，role: key_results）

| 字段 | 类型 | 必需 | 说明 |
|---|---|---|---|
| 目标 | link → 目标管理 | ✅ | 关联 O 记录，CellValue 写 `[{"id":"<O record_id>"}]` |
| OKR | text | ✅ | KR 一句话（可度量结果，不是任务） |
| 季度 | select | ✅ | 同目标管理 |
| 状态 | select | ✅ | 未开始 / 进行中 / 延期 / 已完成 |
| 负责人 | user | 否 | CellValue 写 `[{"id":"ou_xxx"}]` |
| 开始时间 | datetime | 否 | `YYYY-MM-DD HH:mm:ss` |
| 完成时间 | datetime | 否 | 同上 |
| 复盘：做的好的 | text | 否 | 模式 B 复盘写入 |
| 复盘：有待提升 | text | 否 | 模式 B 复盘写入 |
| 输出文档 | text | 否 | 成果/文档链接 |

> 其余表（任务 / 复盘 / 关注的人 / 💡模版使用说明）本次不改动。若模板后续新增表，通过 `/okr-sync` 纳入。

## 数字中转站 JSON → 表字段映射

「制定」skill（`goals:setting-okrs-goals`）输出的数字中转站 JSON 是**表无关**的；下表把它的语义字段映射到实际表字段（`okr-model.json` 的 `semantic → preferred_names`）：

| 中转站 JSON 字段 | 目标表字段（preferred_names 首选） | 值格式 |
|---|---|---|
| `period` | 目标管理.季度、OKR.季度 | select 选项名，如 `2026-Q3` |
| `objective` | 目标管理.O | text |
| （每条 O 生成的 record_id） | OKR.目标（link） | `[{"id":"<O record_id>"}]` |
| `key_result` | OKR.OKR | text |
| `status` | OKR.状态 | select 选项名 |
| `owner.open_id` | OKR.负责人 | `[{"id":"ou_xxx"}]` |
| `start` / `due` | OKR.开始时间 / OKR.完成时间 | `YYYY-MM-DD HH:mm:ss` |
| `kr_type` / `metric` / `baseline` / `target` | 演进钩子：模板若新增量化字段（如 量化指标/目标值/当前值/权重）→ `/okr-sync` 自动纳入可选写入 | — |

## 演进规则（必读）

1. **模型在用户侧**：工作副本 `okr-model.json` 默认在【当前目录】，不在 skill 里；skill 只带 seed `okr-model.default.json`，缺失时用 `setup.sh --ensure-model` 物化。这样 `/okr-sync` 的演进结果归用户所有，插件更新不会覆盖。
2. **模型优先**：默认用工作副本，不每次读表（省时）。结构变化必须先同步。
3. **只增不改不删**：写表 / 同步都只增量；不删字段、不改类型、不覆盖已有值；字段消失只标记 `deprecated: true`，历史定义保留。
4. **显式同步**：模板变化（加字段/改名/换季度）时跑 `/okr-sync`（或 `setup.sh --sync-model`）→ 全量读 → diff → 更新工作副本 + 落快照。前期优化频繁多跑，稳定后偶尔跑。
5. **快照**：每次同步/对齐后落 `okr-snapshots/snapshot-<日期>.json`（默认在【当前目录】），供 diff 与回看。
6. **演进钩子**：`--sync-model` 遇到模型外的新字段，自动纳入为 `auto_discovered` 可选字段（不破坏既有定义），并提示可升级为正式语义映射。
7. **写失败回退**：写入报「字段不存在/字段名不匹配」→ 停止重试，提示用户跑 `/okr-sync`，或直接自动跑同步后重试。
8. **对齐幂等**：`setup.sh` 可每季度复跑；`季度` 选项重复时跳过，不会重复追加。
