# NEXT — Klose Learning

Last updated: 2026-09-05

## 启动顺序

所有 Klose 任务先读取：

```text
AGENTS.md
→ NEXT.md
```

下一阶段按任务继续读取：

```text
Grade 1–3 实际教材词表核对：
→ docs/SOURCE_RECONCILIATION.md
→ docs/KLOSE_VOCABULARY_SYSTEM.md

Expressions：
→ docs/EXPRESSIONS_SYSTEM.md
```

不要仅凭聊天历史推测当前状态。

---

## 1. Current status — Grade-4 Vocabulary closed loop complete

Grade-4 Vocabulary 已完成从真实教材到 Anki Desktop 的完整闭环：

```text
Source / Edition / Occurrence
→ Sense-aware Identity / Stable NoteID
→ Learner Presentation
→ Learning Admission + LearningOrder
→ Review / Approval
→ Release Gate
→ anki-import.csv
→ existing Note Type in-place update
→ Suspend / Unsuspend admission
→ LearningOrder → New Card Position
```

当前执行状态：

```text
Build Valid                 = yes
Content Releasable          = yes
Anki content updated        = yes
Learning Admitted           = yes
LearningOrder in repo       = yes
LearningOrder in Anki New # = yes
```

Repo baseline：

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

Anki Desktop 已实测：

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

LearningOrder 已 materialize 到 New #：

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

Klose 开始真实学习后，FSRS / Due / Interval / Review History / Card State 以 Anki 为唯一真源；已进入 Learning / Review 的 Cards 不再由 repo 重排。

---

## 2. Next Phase A — reconcile Klose actual Grade 1–3 textbooks

用户下一轮会提供 Klose 实际使用的一年级、二年级、三年级教材单词。

这一步的首要目标是 **Source Reconciliation**，不是自动扩大学习队列。

处理链：

```text
Klose actual Grade 1/2/3 textbook vocabulary
→ capture SourceID / SourceEdition / Book / Unit / Order
→ reconcile against existing source occurrences
→ sense-aware mapping to Stable NoteID
→ classify discrepancies
```

至少输出以下类别：

```text
1. actual textbook occurrence already correct
2. grade / semester / unit / order mismatch
3. actual textbook has item missing from current source truth
4. same surface form but different target sense / identity issue
5. third-party source has item not present in Klose actual edition
6. morphology / duplicate occurrence requiring explicit reconciliation
```

核心规则：

```text
Actual Textbook Evidence > third-party organized data
Source Grade ≠ LearnerLevel ≠ Learning Admission
```

因此：

- Grade 1–3 核对首先修正 source truth / provenance；
- 不因“曾在低年级教材出现”就自动 Unsuspend 或加入当前学习；
- 已有 Stable NoteID 不因教材顺序或来源修正而重编号；
- 如发现真正缺学的低年级基础词，再单独形成 lower-grade backfill candidates，并通过 explicit admission 决定是否学习；
- 不用 Source Grade 直接替代当前 learning scope。

完成 Grade 1–3 reconciliation 后，再决定是否需要补充/修正 held library、IPA debt 或 backfill admission。

---

## 3. Next Phase B — build formal Expressions release system

Vocabulary 与 Expressions 继续严格分离：

```text
Vocabulary = word / phrase / target sense
Expressions = communicative function / reusable structure
```

现有 Expressions 状态仍只是：

```text
Raw Expression
→ Pattern Candidate
```

尚未形成正式 release system，不能直接把教材 Useful Expressions 批量导入 Anki。

目标长期链路：

```text
Raw Expression / textbook evidence
→ Pattern Candidate
→ Expression Identity / Stable ExpressionID
→ Learner Presentation
→ Learning Admission + LearningOrder
→ Review / Approval
→ Expression Release Gate
→ generated Anki import artifact
→ Anki
```

必须坚持：

```text
一条教材原句 ≠ 一张 Anki Card
```

只有 communicative intent 清晰、可迁移、值得主动掌握、适合当前 LearnerLevel 的 expression / pattern 才 release。

### Planned Anki architecture

Expressions 使用独立 Note Type 和独立 Deck：

```text
Klose-English::Vocabulary
Klose-English::Expressions
```

目标 Card 训练方向是 **active production**，而不是 Vocabulary 的 recognition。例如：

```text
Front:
中文交际意图 / 场景 / slot cue

Back:
目标英文表达
+ TTS
+ reusable pattern
+ 必要的 slot/example
```

具体 Expression Note fields、Stable ExpressionID、fingerprint、LearningOrder、Release Gate 和 Card Contract 在正式设计时冻结。

**当前不要先在 Anki 手工创建 Expressions Deck / Note Type。**

先完成 repo 侧 Expression identity / release contract / sample validation，再一次性创建正式 Anki schema，避免重复迁移。

Expressions 的 `New/day` 暂不冻结；等 Klose 开始 Vocabulary 后，根据真实每日复习负担决定。

---

## 4. Real-learning feedback loop

在上述数据工作并行推进时，Klose 可以正常开始 Grade-4 Vocabulary：

```text
New/day = 8
```

后续重点观察：

```text
Again ratio
pronunciation errors
meaning / target-sense confusion
PromptHint effectiveness
example comprehension burden
actual daily review load
```

只有真实学习反馈暴露问题时，再调整 Learner Presentation；不要为了架构完整性继续扩 Vocabulary schema。

如果分析学习表现，必须读取 Anki 实际 FSRS / Review History / Card State，不从 GitHub 推测。

---

## 5. Frozen long-term rules

- Stable NoteID 不因教材顺序、来源修正或普通内容修改而变化；
- actual textbook evidence 优先于第三方来源，冲突先 reconciliation；
- Source Grade、LearnerLevel、Learning Admission 三者独立；
- Meaning / IPA / Example / PromptHint 改动需要内容 review；
- LearningOrder 属于 admission metadata，不进入内容 fingerprint；
- Vocabulary LearningOrder 固定 6 位 `000001..999999`；
- 只有仍为 `is:new` 的 Cards 才允许按 LearningOrder调整 New #；
- generated `study.csv` / `anki-import.csv` 禁止手工修改；
- Vocabulary 与 Expressions 不共用 Learning Object identity / Note Type；
- Anki 保存真实 FSRS / Review History，GitHub 不重建学习历史。

---

## Deferred / technical debt

- 99 个 held legacy Vocabulary Notes 缺 British/American IPA：未来对应 Note admission 前补齐并 re-review；当前 held 不阻塞学习。
- Grade 5/6 actual source reconciliation：Grade 1–3 与 Expressions 稳定后再处理。
