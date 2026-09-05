# Klose Actual Textbook Source References

本目录保存来自 Klose 手中实际教材的人工核对资料，用于修正/校验现有 Source Adapter。这里是 **source reference / reconciliation input**，不是 generated publish output。

通用处理规则：

```text
docs/SOURCE_RECONCILIATION.md
docs/EXPRESSIONS_SYSTEM.md
```

当前动态任务入口：

```text
/NEXT.md
```

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
Starred
Entry
Meaning
Page
SourceStatus
```

### Useful Expressions 原文

```text
rj_start1-grade4-upper-klose-expressions.csv
```

教材原句与中文译文按 Unit、顺序保存。每一行都是 Source Fact，不等于未来必须生成一张 Anki Card。

### Expression Pattern Candidates

```text
rj_start1-grade4-upper-pattern-candidates.csv
```

从 Useful Expressions 中抽取的可迁移句型候选。它属于 derived curation，不是教材原文；当前全部保持 candidate，不进入正式 Anki release。

### 四上专项 Reconciliation

```text
rj_start1-grade4-upper-reconciliation.md
```

该文件记录当前版本冲突、identity blocker 和 Definition of Done。

## 重要规则

1. 在完成与现有第三方 XLSX、Source Occurrence、Identity 的系统 reconciliation 前，不直接覆盖 `source_occurrences.csv`、Master 或 Anki release。
2. Klose 手中实际教材是当前学习场景的高优先级 Source Fact 证据；冲突时先识别 Edition / Revision，不能把两个版本误当作同一教材事实集合。
3. 词条粒度必须保留教材事实，例如 `office worker`、`factory worker`、`bus stop`、`delivery worker`、`police officer`、`make the bed` 等不能仅凭包含已有单词就视为已覆盖。
4. `cook` 在本教材中至少有两个 target sense：Unit 1 `烹饪；煮`（verb）与 Unit 4 `厨师`（noun）。必须按 sense-aware 规则处理，不能静默合并。
5. Useful Expressions 同时提供 Context Vocabulary 证据；它可以用于 LearnerLevel 例句难度和教材暴露范围判断，但不能自动升级为 Core Vocabulary。
6. Source Grade、LearnerLevel、Learning Object Type 三个维度必须分离。
7. 本目录中的 actual-textbook reference 不直接赋予 NoteID；NoteID 决策必须经过 reconciliation / identity layer。
8. 如果旧 Note 已进入 Anki Learning/Review，任何 source correction 都必须保护其 Review History / FSRS state。

## 后续新增教材

四年级下以及未来 Grade 5/6 实际教材资料，沿用同样结构：

```text
actual core vocabulary
raw useful expressions
pattern candidates
reconciliation report
```

先 Capture，再 Reconcile；不要从图片直接跳到 publish CSV。
