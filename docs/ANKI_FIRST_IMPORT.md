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

> 重要：本文不是当前 release-readiness 状态页。当前是否允许 Klose 开始学习、是否存在 Source blocker，必须先读根目录 `NEXT.md`。历史上曾成功导入的 baseline，不代表后续发现 Source Fact 问题后仍然可以继续学习。

## 1. 唯一主 Deck

```text
Klose-English::Vocabulary
```

教材、年级、阶段通过 Tags / Source Occurrences / Suspend 控制，不拆成多套长期 Vocabulary Deck。

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

`NoteID` 必须是第一字段。`UserMemo` 是 Anki-local 字段，不从正式 CSV 更新。

## 3. Card Template

Front：

```html
<div class="word">{{Word}}</div>
```

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

其中：

- `study.csv`：generated Released Set 内部审计快照；
- `anki-import.csv`：generated 唯一正式 Anki artifact；
- 两者都禁止手工修改。

## 5. Import 设置

正式导入时：

```text
Note Type      = Klose Vocabulary
Deck           = Klose-English::Vocabulary
Existing notes = Update
Match scope    = Note Type
```

字段映射：

```text
NoteID             -> NoteID
CanonicalWord      -> CanonicalWord
Word               -> Word
British            -> British
American           -> American
MeaningPrimary     -> MeaningPrimary
ExampleSentence    -> ExampleSentence
ExampleTranslation -> ExampleTranslation
LearnerLevel       -> LearnerLevel
Sources            -> Sources
SourceBooks        -> SourceBooks
UserMemo           -> (Nothing)
Tags               -> Anki Tags
```

重新导入同一 NoteID 时应原地更新 Note，不创建第二套 FSRS history。

## 6. 学习阶段与 Suspend

Stage Tags 是 release 时生成的系统状态，不是固定教材分类。第一次导入后只对当前计划学习的 **New Cards** 开放，其余 New Cards 可以 Suspend。

原则：

```text
尚未学习的 New Card -> 可 Suspend / Unsuspend 控制准入
已经 Learning/Review -> 不因 source/stage 调整重新 Suspend
```

具体当前应开放哪些 stage，必须读 `NEXT.md` 和最新 release 数据，不能照抄历史 baseline。

## 7. Deck Options 基线

首次配置曾验证以下值适合当前 Klose Vocabulary 使用：

```text
New cards/day             = 8
Maximum reviews/day       = 9999
Learning steps            = 10m
Relearning steps          = 10m
Leech action              = Tag Only
New card gather order     = Ascending position
New card sort order       = Order gathered
New/review order          = Show after reviews
Interday learning/review  = Mix with reviews
Review sort order         = Due date, then random
FSRS                      = ON
Desired retention         = 90%
FSRS parameters           = default initially
Reschedule cards on change = OFF
```

这些是调度配置，不决定 source correctness。Source/release blocker 优先于“参数已经配置好”。

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

第一次导入后至少验证：

- Note 数 = Card 数；
- Note Type / Deck / Card Type 正确；
- `NoteID` 第一字段；
- Tags 正确；
- Suspend 数量符合当前 staging；
- Preview 正面只显示 Word；
- Back 可播放 Word TTS；
- IPA / Meaning / Example / Translation 正常；
- FSRS 配置正确；
- AnkiWeb 同步完成。

但最终“可以开始正式学习”的判定还必须满足：

```text
repo current source/release ready
+ release gate pass
+ NEXT.md 无 blocker
```

## 10. 历史首次导入

2026-09-05 曾完成第一轮 Desktop 导入与 AnkiWeb Upload。详细过程、当时的 `518 / 343 / 175` 等结果保存在：

```text
docs/ANKI_FIRST_IMPORT_GUIDE.md
```

这些数字是历史实操记录，不再作为永远有效的“当前正式基线”。若后续 Source Reconciliation 改变 released/staging 集合，应使用纠正后的 `anki-import.csv` 原地更新同一 Note Type。
