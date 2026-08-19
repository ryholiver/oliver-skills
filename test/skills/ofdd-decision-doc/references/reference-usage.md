# 参考文件使用说明

## 一、两个参考文件的分工

`ofdd-work-system-overview.md` 是总纲，主要用于判断任务流程位置：

- 当前输入是否属于认知决策；
- 是否已经进入决定后的计划、执行和反馈；
- 何时应该停在审查节点；
- 何时可以从 Decision 衔接到 Plan。

`ofdd-cognitive-decision-framework.md` 是核心规则库，主要用于约束输出质量：

- Source、Evidence Reference、Observation、Finding、Direction、Decision 的定义；
- Inference、Judgment、Question 的边界；
- 各实体状态枚举；
- 证据追溯关系；
- 标准记录模板。

## 二、默认产出边界

本 skill 默认产出的是 OFDD 中间层，而不是最终 HTML 页面：

```text
输入材料
↓
OFDD Markdown 库文件
↓
OFDD JSON 数据文件
↓
下游 HTML Review skill
↓
可交互审查页面
```

## 三、审查节点优先

当用户没有明确拍板时：

- 可以生成 Direction；
- 可以生成 proposed Decision；
- 必须生成 Review Gate；
- 不得把 proposed Decision 写成 approved Decision；
- 不得直接进入执行计划。

当用户明确拍板且没有阻塞性未决项时，才可以把 Decision 状态写为 `approved`，并提示可以进入执行闭环。
