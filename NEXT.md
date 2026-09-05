# NEXT — Klose Learning

Last updated: 2026-09-05

启动顺序：

```text
AGENTS.md
→ NEXT.md
→ docs/ANKI_SYNC_WORKFLOW.md
→ anki/klose/anki/README.md
```

## Current status

Grade-4 Vocabulary 已完成从真实教材到 Anki 的完整闭环，包括 Source / Identity / Learner Presentation / Learning Admission / Review / Release / PromptHint / LearningOrder，以及 Desktop 端原地导入、准入切换和 New Card Position 初始化。

```text
Build Valid                 = yes
Content Releasable          = yes
Anki content updated        = yes
Learning Admitted           = yes
LearningOrder in repo       = yes
LearningOrder in Anki New # = yes
```

Klose 尚未开始真实 Review History；下一步可以直接开始 Grade-4 Vocabulary 学习。

---

## 1. Current repo baseline

```text
inventory Notes        = 901
released / study       = 638
Grade-4 allowed        = 221
held library           = 417
model-reviewed         = 638
review pending         = 0
PromptHint nonempty    = 4
LearningOrder          = 000001..000221
held LearningOrder     = blank
Release Gate           = PASS
held IPA debt          = 99
```

正式 generated release：

```text
ccfd1709  data: rebuild Klose vocabulary base
```

正式 Anki artifact：

```text
anki/klose/publish/anki-import.csv
```

禁止手工编辑 `study.csv` / `anki-import.csv`。

---

## 2. Current physical Anki baseline — validated

```text
Deck              = Klose-English::Vocabulary
Note Type         = Klose Vocabulary
Card Type         = Recognition
Total Notes/Cards = 638
Unsuspended       = 221
Suspended         = 417
New/day           = 8
FSRS              = ON
Desired retention = 90%
```

现有 Note Type 字段：

```text
1  NoteID
2  CanonicalWord
3  Word
4  PromptHint
5  British
6  American
7  MeaningPrimary
8  ExampleSentence
9  ExampleTranslation
10 LearnerLevel
11 LearningOrder
12 Sources
13 SourceBooks
14 UserMemo
```

PromptHint 已实测：

```text
cook / n.       correct
cook / v.       correct
over / 位置      correct
over / 结束      correct
Back TTS         correct
```

Learning Admission 已实测：

```text
Total        = 638
Unsuspended  = 221
Suspended    = 417
```

LearningOrder migration 已完成：

```text
tag:learning::klose::grade4 -is:suspended is:new = 221
```

221 张 active New Cards 已按 `LearningOrder` 升序 Reposition，当前 Browser 实测：

```text
000001 -> New #1 -> PE              -> KV000285
000002 -> New #2 -> job             -> KV000433
000003 -> New #3 -> doctor          -> KV000425
000004 -> New #4 -> farmer          -> KV000429
000005 -> New #5 -> nurse           -> KV000423
000006 -> New #6 -> office worker   -> KV000803
000007 -> New #7 -> factory worker  -> KV000804
000008 -> New #8 -> busy            -> KV000466
```

因此当前 `New/day=8` 下，Klose 第一天的新词顺序已经确定为：

```text
PE
job
doctor
farmer
nurse
office worker
factory worker
busy
```

---

## 3. LearningOrder contract — frozen

必须区分：

```text
LearningOrder
= GitHub 中的 curriculum / admission 真源

New Card Position / New # / Due
= Anki 中的物理学习状态
```

正式序列化契约：

```text
LearningOrder = fixed-width 6-digit decimal text
valid         = 000001..999999
held          = blank
```

当前 Grade-4 order 从真实教材 + confirmed source identity 自动推导：

```text
四年级上 Unit 1 → Unit 6
→ 四年级下 Unit 1 → Unit 6
→ 每个 Unit 内按教材 Order
```

`LearningOrder` 是 admission metadata，不进入 learner content fingerprint。调整尚未学习的新卡顺序不触发 Meaning / Example 内容 re-review，但必须通过 Admission / Release Gate。

---

## 4. Next operational phase — real learning

当前数据工程 / Anki migration 阶段结束。下一阶段优先让 Klose 开始真实学习，不继续为了架构完整性扩 schema。

建议运行顺序：

```text
1. Klose 按 New/day=8 开始 Grade-4 Vocabulary
2. 让 Anki FSRS 正常积累 Review History
3. 观察 Again 比例、易错词、读音错误、目标义项混淆、例句理解负担
4. 只对真实暴露的问题调整 Learner Presentation
5. Vocabulary 稳定后继续四下 Useful Expressions
```

如果后续分析学习表现，以 **Anki 实际 FSRS / Review History / Card State** 为真源，不从 GitHub 推测。

---

## 5. Long-term sync rules

以后内容更新统一：

```text
upstream source / identity / learner / admission changes
→ review fingerprint invalidation（仅内容字段）
→ explicit review / approval
→ Release Gate PASS
→ regenerate anki/klose/publish/anki-import.csv
→ import into same Klose Vocabulary Note Type
→ Existing Notes = Update by NoteID
```

长期不变量：

- Stable NoteID 不因教材顺序、重建或普通内容修正而变化；
- Meaning / IPA / Example / PromptHint 改动需要内容 review；
- LearningOrder 改动进入 Admission / Release Gate，不触发内容 review；
- LearningOrder 固定 6 位 `000001..999999`；
- 只有仍为 `is:new` 的 Cards 才允许按 LearningOrder 调整 New #；
- 一旦进入真实 Learning / Review，FSRS / Due / Interval / Review History 永远以 Anki 为真源，不由 repo 重排。

---

## Deferred

- 四下 Useful Expressions：可以在 Vocabulary 正式开始学习并稳定后处理。
- 99 个 held legacy Notes 缺 British/American IPA：未来对应 Note admission 前补齐并 re-review；当前 held 状态不阻塞学习。
