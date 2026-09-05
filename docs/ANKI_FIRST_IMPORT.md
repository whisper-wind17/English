# Klose Vocabulary：第一次正式导入 Anki

本文定义 **NoteID-first 新系统第一次导入的操作契约**。逐步实操记录见：

```text
docs/ANKI_FIRST_IMPORT_GUIDE.md
```

第一次导入完成后的长期同步统一按：

```text
docs/ANKI_SYNC_WORKFLOW.md
```

如果设备里已有旧 Word-first 数据，先按 `docs/ANKI_MIGRATION.md` 迁移。

> 当前是否允许 Klose 开始学习，以根目录 `NEXT.md` 和 Release Gate 为准；历史上曾成功导入的 baseline 不代表后续 source/release 状态永远有效。

## 1. 唯一主 Deck

```text
Klose-English::Vocabulary
```

教材、年级、学习范围通过 Source / Tags / Learning Admission / Suspend 控制，不拆成多套长期 Vocabulary Deck。

## 2. Note Type

```text
Klose Vocabulary
```

只创建一个 Card Type：

```text
Recognition
```

即：

```text
1 Note = 1 Card
```

字段顺序：

```text
NoteID
CanonicalWord
Word
PromptHint
British
American
MeaningPrimary
ExampleSentence
ExampleTranslation
LearnerLevel
LearningOrder
Sources
SourceBooks
UserMemo
```

`NoteID` 必须是第一字段。`PromptHint` 是可选 Learner Presentation，普通 Notes 留空；`LearningOrder` 是 curriculum/admission metadata；`UserMemo` 是 Anki-local 字段，不从正式 CSV 更新。

## 3. Card Template

Front：

```html
<div class="word">{{Word}}</div>
{{#PromptHint}}
<div class="prompt-hint">{{PromptHint}}</div>
{{/PromptHint}}
```

普通词仍只显示 Word；同形异义 active Note 可显示最小消歧提示。`LearningOrder` 不展示在卡片正反面。

Back：

```html
{{FrontSide}}

{{tts en_US:Word}}

{{#British}}
<div class="phonetic">UK {{British}}</div>
{{/British}}

{{#American}}
<div class="phonetic">US {{American}}</div>
{{/American}}

<hr id="answer">

<div class="meaning">{{MeaningPrimary}}</div>

{{#ExampleSentence}}
<div class="example">{{ExampleSentence}}</div>
{{/ExampleSentence}}

{{#ExampleTranslation}}
<div class="translation">{{ExampleTranslation}}</div>
{{/ExampleTranslation}}
```

正式模板以：

```text
anki/klose/anki/
```

为准。当前只自动朗读单词，例句不自动朗读。

## 4. 唯一正式导入文件

```text
anki/klose/publish/anki-import.csv
```

不要直接导入：

```text
publish/study.csv
publish/all.csv
publish/onboarding/*
publish/by-source/*
```

`study.csv` 是 generated Released Set 内部审计快照；`anki-import.csv` 是 generated 唯一正式 Anki artifact。二者都禁止手工修改。

## 5. Import 设置

```text
Note Type       = Klose Vocabulary
Deck            = Klose-English::Vocabulary
Existing notes  = Update
Match scope     = Note Type
```

字段映射：

```text
NoteID              -> NoteID
CanonicalWord       -> CanonicalWord
Word                -> Word
PromptHint          -> PromptHint
British             -> British
American            -> American
MeaningPrimary      -> MeaningPrimary
ExampleSentence     -> ExampleSentence
ExampleTranslation  -> ExampleTranslation
LearnerLevel        -> LearnerLevel
LearningOrder       -> LearningOrder
Sources             -> Sources
SourceBooks         -> SourceBooks
UserMemo            -> (Nothing)
Tags                -> Anki Tags
```

重新导入同一 NoteID 时应原地更新 Note，不创建第二套 FSRS history。

## 6. Learning Admission、Suspend 与 New Card 顺序

当前学习集合由 explicit Learning Admission 和 `learning::*` tag 表达，不由 Source Grade 自动决定。

初次建库时，可对尚未开始真实学习的 New Cards 根据当前 release 状态做 Suspend / Unsuspend。进入真实 Learning/Review 后，不因普通 source/stage 调整重建 Card 或清空 FSRS。

若当前 admission 定义了 `LearningOrder`，对仍为 `is:new` 的目标 Cards 按：

```text
docs/ANKI_LEARNING_ORDER_MIGRATION.md
```

将 curriculum order 一次性 materialize 为 Anki New Card Position。

具体当前应开放哪些 Notes、是否需要 Reposition，必须读 `NEXT.md`，不能照抄历史 baseline。

## 7. Deck Options 基线

```text
New cards/day              = 8
Maximum reviews/day        = 9999
Learning steps             = 10m
Relearning steps           = 10m
Leech action               = Tag Only
New card gather order      = Ascending position
New card sort order        = Order gathered
New/review order           = Show after reviews
Interday learning/review   = Mix with reviews
Review sort order          = Due date, then random
FSRS                       = ON
Desired retention          = 90%
FSRS parameters            = default initially
Reschedule cards on change = OFF
```

这些是调度配置，不决定 source correctness。

## 8. 第一次同步

若 Desktop 是唯一有完整 collection 的端、AnkiWeb 为空：

```text
Desktop -> Sync -> Upload to AnkiWeb
```

随后空的 iPad AnkiMobile：

```text
登录同一 AnkiWeb
-> Sync
-> Download from AnkiWeb
```

若 AnkiWeb / iPad 已有其他 collection 数据，不要盲目单向覆盖，先确认同步方向。

## 9. 验收

至少验证：

- Note 数 = Card 数；
- Note Type / Deck / Card Type 正确；
- `NoteID` 第一字段；
- `PromptHint` 字段存在，普通 Note 可为空；
- current allowed Notes 的 `LearningOrder` 与 curriculum contract 一致；held 为 blank；
- Tags 正确；
- Suspend 数量符合当前 Learning Admission；
- 尚未学习的新卡在需要时已按 LearningOrder Reposition；
- Preview 正面显示 Word + optional PromptHint；
- Back 可播放 Word TTS；
- IPA / Meaning / Example / Translation 正常；
- FSRS 配置正确；
- AnkiWeb 同步完成。

最终“可以开始正式学习”还必须满足：

```text
repo current source/release ready
+ release gate pass
+ NEXT.md 无 blocker
```

## 10. 历史首次导入

2026-09-05 曾完成第一轮 Desktop 导入与 AnkiWeb Upload。详细过程和当时 `518 / 343 / 175` 的历史结果保存在：

```text
docs/ANKI_FIRST_IMPORT_GUIDE.md
```

这些数字不是永久基线。后续 Source Reconciliation / Learning Admission 变化后，应使用最新 `anki-import.csv` 原地更新同一 Note Type。
