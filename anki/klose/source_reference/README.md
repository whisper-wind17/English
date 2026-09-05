# Klose Actual Textbook Source References

本目录保存来自 Klose 手中实际教材的人工核对资料，用于修正/校验现有 Source Adapter。这里是 **source reference / reconciliation input**，不是 generated publish output。

## 当前四年级上基准

### Core Vocabulary

```text
rj_start1-grade4-upper-klose-actual.csv
```

来源：2026-09-05 用户上传的《四年级上》教材词汇表照片，共 6 个 Unit、110 条词条记录。`cook` 在 Unit 1 与 Unit 4 以不同义项各出现一次，因此为 109 个不同 surface entries。

字段：

```text
Unit
Order
Starred       # 是否带教材中的 * 标记
Entry
Meaning
Page
SourceStatus
```

### Useful Expressions 原文

```text
rj_start1-grade4-upper-klose-expressions.csv
```

来源：2026-09-05 用户上传的《四年级上 Useful expressions / 常用表达法》照片。原句与教材中文译文按 Unit、顺序保存。这里的每一行都是 Source Fact，不等于未来必须生成一张 Anki Card。

### Expression Pattern Candidates

```text
rj_start1-grade4-upper-pattern-candidates.csv
```

从 Useful Expressions 中抽取的可迁移句型候选。它属于 derived curation，不是教材原文事实；`ReleaseStatus=candidate` 表示尚未进入正式 Expressions 学习系统。

Pattern 候选应优先保留：

```text
What's [person]'s job?
There is / There are ...
What's the weather like in [place]?
Whose [noun] is this?
Can I [verb phrase]?
Which [category] do you like?
```

而上下文依赖很强的完整句子只保留为 Source Expression，不机械制卡。

## 重要规则

1. 在完成与现有 `rj_start1` 第三方 XLSX、Source Occurrence、Identity 的系统 reconciliation 前，不直接覆盖 `source_occurrences.csv`、Master 或 Anki release。
2. Klose 手中实际教材应作为高优先级 Source Fact 证据；若与现有第三方整理 XLSX 冲突，应先识别版本差异，再修 Source Adapter。不能把两个版本误当作同一个教材事实集合。
3. 词条粒度必须保留教材事实，例如 `office worker`、`factory worker`、`bus stop`、`delivery worker`、`police officer`、`make the bed` 等不能仅凭包含已有单词就视为已覆盖。
4. `cook` 在本教材中至少有两个 target sense：Unit 1 `烹饪；煮`（动词）与 Unit 4 `厨师`（名词）。后续 reconciliation 必须按 learning-unit / sense-aware 规则处理，不能静默合并为同一义项。
5. Useful Expressions 同时提供 Context Vocabulary 证据。例如 `firefighter / gym / museum / neighbour / degree / festival / mooncake` 等即使未列入 Core Vocabulary，也是真实进入四上语言环境的词。后续可用于 LearnerLevel=4 的例句难度约束，但不能自动升级为 Core Vocabulary。
6. Source Grade、LearnerLevel、Learning Object Type 三个维度必须分离：教材四上事实不意味着只能在 LearnerLevel=4 学习，也不意味着 Expression 与 Vocabulary 共用同一 Note Type。
