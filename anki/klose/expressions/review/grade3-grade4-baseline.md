# Grade 3–4 Expression Candidate Baseline

Scope: Klose 实际使用教材的三年级上/下、四年级上/下 Useful Expressions。

Source inputs:

```text
anki/klose/source_reference/rj_start1-grade3-klose-expressions.csv  # 94 occurrences
anki/klose/source_reference/rj_start1-grade4-klose-expressions.csv  # 72 occurrences
```

Total Source Occurrences: **166**

本文件记录从 Source Fact 到 Pattern Candidate 的第一次统一整理，以及后续 Identity Review 的最终结果。

## Candidate baseline

```text
Source Occurrences         = 166
Curated Pattern Candidates = 64
core                       = 38
secondary                  = 26
pilot_candidate            = 19
```

Candidate 阶段按来源分为：

```text
Grade-4-related Candidates = 36  # SourceGrades=4 或 3|4
Grade-3-only Candidates     = 28
Total                       = 64
```

Candidate Registry：

```text
anki/klose/expressions/review/candidate_registry.csv
```

`ECxxxx` 只是 candidate review 编号，不是 Stable ExpressionID。

## Identity Review complete

64 个 Candidate 已全部完成 Identity Resolution，正式结果：

```text
Stable Expressions = 66
Grade-4 priority   = 37
Grade-3-only       = 29
LearningOrder      = 000001..000066
```

之所以从 64 Candidate 得到 66 Stable Expressions，是因为有两个 Candidate 在正式 Identity 层必须 split：

```text
EC0035
→ KE000020  It's time for [noun].
→ KE000021  It's time to [verb].

EC0058
→ KE000035  Excuse me?   # Grade 4: 没听清时请求重复
→ KE000062  Excuse me.   # Grade 3: 礼貌引起注意
```

这不是重复制卡，而是遵守：

```text
Expression Identity = CanonicalForm + CommunicativeFunction
```

另外有三处显式 identity adjustment：

```text
EC0009  What's this? / What's that?
→ What's [demonstrative]?

EC0014  Can I [verb phrase], please?
→ Can I [verb phrase]?   # please 为可选礼貌成分

EC0030  It's [weather adjective] [time/place].
→ It's [weather description] [time/place].
```

以及：

```text
EC0047 Candidate Type = fixed
→ formal ExpressionType = slot_frame
```

完整决策：

```text
anki/klose/expressions/review/identity_resolution.csv
```

## Learning order

正式学习顺序已冻结为：

```text
Grade 4 related first
→ Grade 3 only second
```

具体为：

```text
KE000001..KE000037  LearningOrder 000001..000037  Grade-4 priority
KE000038..KE000066  LearningOrder 000038..000066  Grade-3 only
```

凡同一 Pattern 同时在三、四年级出现，只学习一次，并放入 Grade-4 priority block。

## Curation rules

- 多个教材原句若表达同一 communicative function + canonical pattern，可合并为一个 Identity；
- 同一 surface form 若 communicative function 不同，必须 split；
- 同一 communicative function 若存在两个需要独立主动掌握的构式，可以 split；
- 问句和答句承担不同 production function 时保留为不同 Identity；
- 一次性叙述、纯课文事实、迁移价值低的完整句保留在 Source Reference，不机械制卡；
- 固定社交表达如 `Here you are.`、`You're welcome.` 可以成为 Expression，因为目标是主动调用；
- Source Occurrence 与 Stable Expression Identity 始终分离。

## Current presentation state

全部 66 个 Stable Expressions 已生成 Stage-A Learner Presentation：

```text
中文短场景 / communicative intent
+ English minimal cue
→ active English production
```

当前 review state：

```text
approved       = 9   # KE000001..KE000009
model-reviewed = 57  # KE000010..KE000066
```

完整卡片总览：

```text
anki/klose/expressions/review/full-baseline-review.md
```

`model-reviewed` 不等于用户 `approved`。在最终 batch approval 前，后 57 张不会进入 full Anki import artifact。
