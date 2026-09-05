# NEXT — Klose Learning

Last updated: 2026-09-05

启动顺序：

```text
AGENTS.md
→ NEXT.md
→ docs/ANKI_LEARNING_ORDER_MIGRATION.md
→ docs/ANKI_SYNC_WORKFLOW.md
→ anki/klose/anki/README.md
```

## Current status

Grade-4 Vocabulary 的 Source / Identity / Learner Presentation / Learning Admission / Review / Release 已完成；Desktop 也已完成 PromptHint、638 Notes 原地导入与 `221 active / 417 held` 的准入切换。

本轮修复了 sequencing 缺口，并在真正迁移到 Anki 前进一步冻结长期序列化契约：**LearningOrder 固定使用 6 位十进制零填充字符串，不随词库规模改变位宽。**

Repo 已完成 deterministic `LearningOrder`；当前唯一未完成的是把它 materialize 到 Anki 的 New Card Position。

```text
Build Valid                 = yes
Content Releasable          = yes
Anki content updated        = yes
Learning Admitted           = yes
LearningOrder in repo       = yes
LearningOrder in Anki New # = pending one-time reposition
```

Klose 尚未正式开始本批次学习，因此当前仍是安全的 New Card 排序窗口。

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

正式 generated release commit：

```text
ccfd1709  data: rebuild Klose vocabulary base
```

正式 Anki artifact：

```text
anki/klose/publish/anki-import.csv
```

当前列：

```text
NoteID,CanonicalWord,Word,PromptHint,British,American,MeaningPrimary,
ExampleSentence,ExampleTranslation,LearnerLevel,LearningOrder,Sources,SourceBooks,Tags
```

禁止手工编辑 `study.csv` / `anki-import.csv`。

---

## 2. LearningOrder contract — implemented

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

固定 6 位避免未来扩展到数千/数万学习单元后再做 3 位 → 4 位 → 5 位迁移，并保证 Anki 文本排序与数值排序一致。

当前 Grade-4 order 从真实教材 + confirmed source identity 自动推导：

```text
四年级上 Unit 1 → Unit 6
→ 四年级下 Unit 1 → Unit 6
→ 每个 Unit 内按教材 Order
```

allowed 221 Notes：

```text
LearningOrder = 000001..000221
```

held 417 Notes：

```text
LearningOrder = blank
```

Release Gate 会重新从 `source_identity_extensions.csv` 计算教材顺序并校验 exact NoteID → LearningOrder 映射，同时校验固定 6 位格式。

前 8 个已在 CI / source identity 中确认：

```text
000001  PE              KV000285
000002  job             KV000433
000003  doctor          KV000425
000004  farmer          KV000429
000005  nurse           KV000423
000006  office worker   KV000803
000007  factory worker  KV000804
000008  busy            KV000466
```

`LearningOrder` 是 admission metadata，不进入 learner content fingerprint。本次六位化：

```text
review invalidated = 0
review pending     = 0
```

---

## 3. Current physical Anki state

Desktop 已完成此前正式导入与 PromptHint 验收：

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

PromptHint 已实测：

```text
cook / n.       correct
cook / v.       correct
over / 位置      correct
over / 结束      correct
Back TTS         correct
```

但当前 Anki `New #` 仍继承旧历史创建顺序；实测最前面是 `there / chair / ...`，尚未 materialize 最新 LearningOrder。

---

## 4. Immediate next action — Anki LearningOrder migration

严格按：

```text
docs/ANKI_LEARNING_ORDER_MIGRATION.md
```

### A. Update local repo

```text
git pull origin main
```

### B. Extend existing Note Type

在现有 `Klose Vocabulary` 中增加：

```text
LearningOrder
```

放在 `LearnerLevel` 后、`Sources` 前。

最终字段顺序：

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

不修改 Card Template，不创建第二套 Note Type / Card Type。

### C. Import latest release in place

```text
Import file      = anki/klose/publish/anki-import.csv
Note Type        = Klose Vocabulary
Existing Notes   = Update
Match scope      = Note Type
Identity         = NoteID
LearningOrder    -> LearningOrder
UserMemo         -> Nothing
```

预期总数仍为：

```text
638 Notes / 638 Cards
```

### D. Verify all target Cards are still New

搜索：

```text
tag:learning::klose::grade4 -is:suspended is:new
```

必须：

```text
221 Cards
```

如果不是 221，停止，不要 Reposition 已经进入真实 Learning/Review 的 Cards。

### E. Materialize LearningOrder → New #

显示 `LearningOrder` 列并升序排序，前 8 个必须是：

```text
000001 PE
000002 job
000003 doctor
000004 farmer
000005 nurse
000006 office worker
000007 factory worker
000008 busy
```

全选这 221 张：

```text
Cards → Reposition
Start position = 1
Step           = 1
Randomize      = OFF
Shift existing = ON
```

执行后按 `Due / New #` 升序，前 8 张必须仍是上述 8 个词，并对应 New #1..8。

最终数量仍必须：

```text
Total        = 638
Unsuspended  = 221
Suspended    = 417
```

完成后再 Sync 到 AnkiWeb / iPad。

---

## 5. Long-term rule

以后：

- Meaning / IPA / Example / PromptHint 改动 → fingerprint invalidation + explicit content review；
- LearningOrder 改动 → Admission / Release Gate 校验，不触发内容 review；
- LearningOrder 固定 6 位 `000001..999999`，不得因词库扩大改变位宽；
- 仅对尚未学习的 `is:new` Cards 可以按 LearningOrder 调整 New Card Position；
- 已进入真实 Learning / Review 的 Card，其 FSRS / Due / Interval / Review History 永远以 Anki 为真源，不由 repo 重排。

---

## Deferred

- 四下 Useful Expressions：LearningOrder migration 完成、Klose 正式开始 Vocabulary 后再处理。
- 99 个 held legacy Notes 缺 British/American IPA：未来对应 Note admission 前补齐并 re-review。
