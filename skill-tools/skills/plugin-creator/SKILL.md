---
name: plugin-creator
description: 创建 Claude Code 插件并发布到市场。用于：创建插件，制作插件、分享插件、发布插件、插件开发、修改插件、修复插件、调整插件。触发词：create a plugin, build a plugin, make a plugin, share a plugin, publish plugin, plugin development, 创建插件, 制作插件, 发布插件, 修复插件, 调整插件。
---

# Plugin Creator

把 skill 打包成 plugin 或修改现有 plugin，验证结构符合规范后发布到市场。

***

## 第一步：确认要做什么

询问用户是哪一类需求：

- 创建一个新插件？（把 skill 打包成 plugin）
- 创建多插件合集？（多个 plugins 一起管理/发布）
- 修改现有插件？（修复问题或调整结构）

确认需求后，按对应流程执行。

***

## 第二步：按需求执行

> 根据第一步确认的结果，选择下方对应分支执行。

### 分支 A：创建新插件

查阅 [references/单独插件规范.md](references/单独插件规范.md) 按规范搭建结构。

1. **找** → 用户没声明 skill 路径则询问
2. **建** → 按规范创建目录结构、plugin.json、SKILL.md
3. **→ 进入验证**

### 分支 B：创建多插件合集

查阅 [references/多插件合集规范.md](references/多插件合集规范.md) 按规范搭建结构。

1. **找** → 用户没声明 skill 路径则询问
2. **分** → 多个 skills 是否需要分拆成不同 plugin，用户没说则询问
3. **建** → 按规范创建合集结构
4. **→ 进入验证**

### 分支 C：修改现有插件

1. **判断** → 先确认是单插件还是多插件合集
2. **找** → 用户没声明路径则询问
3. **改什么** → 用户没声明修改需求则询问，loop循环直到修改完成
4. **→ 进入验证**

***

## 第三步：验证

根据插件类型选择对应清单逐项检查。不需要验证的修改（只改内容不影响安装使用）跳过此步。

1. 跑 `validate_plugin.py` 修掉存在性错误
2. 改动涉及 plugin.json / 目录结构 / marketplace.json 时才需继续：
   - 查 [checklists/插件联动修改表.md](checklists/插件联动修改表.md) 确认变更项是否同步更新
   - 查 [checklists/插件验证检查清单.md](checklists/插件验证检查清单.md)（单插件）
   - 查 [checklists/多插件合集验证检查清单.md](checklists/多插件合集验证检查清单.md)（多合集）
3. 发现问题 → 查 [checklists/插件排障清单.md](checklists/插件排障清单.md)
4. loop 直到通过。
5. **→ 进入发布前向用户确认操作**

***

## 第四步：发布

```bash
python scripts/publish.py --plugin-path ./xxx --category xxx
```

***

## 第五步：告知安装代码

```
/plugin install xxx@claude-code-plugins-plus
```

***

## 常用命令

```
/plugin install xxx@claude-code-plugins-plus
/plugin marketplace add owner/repo
```

