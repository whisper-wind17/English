# Klose Vocabulary：第一次正式导入 Anki

本文只描述 **NoteID-first 新系统的第一次正式导入**。如果设备里已经导入过旧版 Word-first 人教版 CSV，先看 `docs/ANKI_MIGRATION.md`，不要直接重复导入。

## 1. 当前可发布基线

当前正式发布入口：

```text
anki/klose/publish/study.csv
```

Grade-4 Baseline v1：

```text
Released Notes            = 518
model-reviewed            = 518
pending                    = 0
identity review            = 0
learner review             = 0
future-vocabulary review   = 0
```

学习阶段：

```text
stage::grade4-new            = 175
stage::grade4-review         = 26
stage::lower-grade-backfill  = 317
```

`study.csv` 的 518 Notes 全部可以进入同一个 Anki Collection，但第一次只让 `grade4-new` 进入正常 New Card 队列。

---

## 2. 只有一个主 Deck

创建并长期保留：

```text
Klose-English::Vocabulary
```

不要创建：

```text
Grade4 New
Grade4 Review
Lower Grade
人教版一年级
人教版四年级
北京版
新概念
```

这些分类都由 Tags / Source metadata 表达，不形成长期独立牌组。

Klose 每天只需要进入：

```text
Klose-English::Vocabulary
```

---

## 3. Note Type

长期 Note Type：

```text
Klose Vocabulary
```

建议字段按以下顺序建立：

```text
NoteID
CanonicalWord
Word
British
American
MeaningPrimary
ExampleSentence
ExampleTranslation
LearnerLevel
Sources
SourceBooks
UserMemo
```

说明：

- `NoteID` 必须长期稳定，并保持第一个字段；
- `UserMemo` 是 Anki 本地个人备注，不从 CSV 更新；
- CSV 中的 `Tags` 映射到 Anki 自带 Tags，不需要另建普通 `Tags` 字段。

第一次建立 Note Type 后，未来不要因为升年级或加入新教材而重新创建 Note Type。

---

## 4. 第一次导入 `study.csv`

导入：

```text
anki/klose/publish/study.csv
```

目标 Deck：

```text
Klose-English::Vocabulary
```

字段映射：

```text
NoteID              → NoteID
CanonicalWord       → CanonicalWord
Word                → Word
British             → British
American            → American
MeaningPrimary      → MeaningPrimary
ExampleSentence     → ExampleSentence
ExampleTranslation  → ExampleTranslation
LearnerLevel        → LearnerLevel
Sources             → Sources
SourceBooks         → SourceBooks
Tags                → Anki Tags
```

不要把 `publish/onboarding/*.csv` 再额外导入一次。它们只是同一批 Notes 的便利视图；第一次正式同步入口只有 `study.csv`。

---

## 5. 第一次只开放四年级新词

全部 518 Notes 导入后，在 Browser 中按 Tags 控制学习阶段。

保持正常：

```text
tag:stage::grade4-new
```

共 175 Notes。

将以下两组暂时 Suspend：

```text
tag:stage::grade4-review
```

26 Notes。

```text
tag:stage::lower-grade-backfill
```

317 Notes。

最终状态：

```text
Klose-English::Vocabulary
├── grade4-new            175   Unsuspended
├── grade4-review          26   Suspended
└── lower-grade-backfill  317   Suspended
```

这仍然是 **一个 Deck**。Suspend 只是控制哪些 Card 当前能进入 New/Review 队列。

---

## 6. 日常学习

Klose 不需要管理 Tags 或 CSV，只需要：

```text
打开 Anki
→ Klose-English::Vocabulary
→ Study Now
```

建议继续使用 FSRS。新词数量先按实际负担控制；当前系统设计不依赖固定 5 或 10 个/天，后续可以在不改数据结构的情况下调整。

已经学过的 Card 会一直由 FSRS 决定何时复习；新增词不会重置旧词的 Review History。

---

## 7. 后续开放旧词查漏

四年级新词进入稳定学习后，可以逐批 Unsuspend：

```text
stage::grade4-review
```

再根据需要开放：

```text
stage::lower-grade-backfill
```

不需要重新建 Deck，也不需要 Klose 手动切换牌组。

---

## 8. 以后加入五年级 / 北京版 / 新概念

repo 继续扩展 Vocabulary Master，并生成新的最新版：

```text
publish/study.csv
```

以后重新导入这个最新版，仍然指定：

```text
Note Type = Klose Vocabulary
Deck      = Klose-English::Vocabulary
```

导入逻辑：

```text
已存在 NoteID
→ Update Existing Note
→ 内容可以更新
→ 原 Card / FSRS / Review History 保留

新 NoteID
→ Create New Note
→ 加入同一个主 Deck
→ 从 New 状态开始自己的 FSRS 生命周期
```

所以几年后的结构仍然可以保持：

```text
一个 Vocabulary Master
一个 Klose Vocabulary Note Type
一个 Klose-English::Vocabulary 主 Deck
一套连续积累的 FSRS 学习历史
```

---

## 9. 导入前的 release gate

任何时候准备把 repo 的新版本同步到 Anki，先要求：

```bash
python tools/check_klose_release_ready.py
```

必须通过后，才能把当前 `study.csv` 描述为正式 release。

该检查会验证：

- `study.csv` 与 Released Set 一致；
- identity / learner / future-vocabulary review 均为空；
- 所有 released Note 都已经 model-reviewed 或 human-reviewed；
- ContentFingerprint 与当前 Meaning / Example / Translation 完全一致。

当前 Grade-4 Baseline v1 已通过该 gate。
