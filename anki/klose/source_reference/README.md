# Klose Actual Textbook Source References

本目录保存来自 Klose 手中实际教材的人工核对词表，用于修正/校验现有 Source Adapter。

当前文件：

```text
rj_start1-grade4-upper-klose-actual.csv
```

来源：2026-09-05 用户上传的《四年级上》教材词汇表照片，共 6 个 Unit、110 条词条记录（`cook` 在 Unit 1 与 Unit 4 以不同义项各出现一次，因此为 109 个不同 surface entries）。

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

重要规则：

1. 本目录当前是 **source reference / reconciliation input**，不是 generated publish output。
2. 在完成与现有 `rj_start1` 原始 XLSX、Source Occurrence、Identity 的系统 reconciliation 前，不直接覆盖 `source_occurrences.csv`、Master 或 Anki release。
3. Klose 手中实际教材应作为高优先级 Source Fact 证据；若与现有第三方整理 XLSX 冲突，应先确认教材版本，再修 Source Adapter。
4. 词条粒度必须保留教材事实，例如 `office worker`、`factory worker`、`bus stop`、`delivery worker`、`police officer`、`make the bed` 等不能仅凭包含已有单词就视为已覆盖。
5. `cook` 在本教材中至少有两个 target sense：Unit 1 `烹饪；煮`（动词）与 Unit 4 `厨师`（名词）。后续 reconciliation 必须按 learning-unit / sense-aware 规则处理，不能静默合并为同一义项。
