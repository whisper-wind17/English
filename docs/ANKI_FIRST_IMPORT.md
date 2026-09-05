# Klose Vocabulary：第一次正式导入 Anki

本文只描述 **NoteID-first 新系统的第一次正式导入**。第一次导入完成后的长期重复同步，统一按 `docs/ANKI_SYNC_WORKFLOW.md` 执行。

如果设备里已经导入过旧版 Word-first 人教版 CSV，先按 `docs/ANKI_MIGRATION.md` 做迁移，不要直接重复导入。

## 1. 当前正式基线

Grade-4 Baseline v1：

```text
Released Notes            = 518
model-reviewed            = 518
pending                    = 0
identity review            = 0
learner review             = 0
future-vocabulary review   = 0
```

当前学习阶段：

```text
stage::grade4-new            = 175
stage::grade4-review         = 26
stage::lower-grade-backfill  = 317
```

内部 released snapshot：

```text
anki/klose/publish/study.csv
```

真正给 Anki 导入的发布文件：

```text
anki/klose/publish/anki-import.csv
```

不要直接导入 `study.csv`。`study.csv` 用于 repo 构建、审计、diff 和 release 对账；`anki-import.csv` 使用 Anki `#...` file headers、UTF-8 无 BOM，没有普通数据表头行。

`study.csv` 和 `anki-import.csv` 都是 generated output，均不得手工修改。

---

## 2. 创建唯一主 Deck

长期主 Deck：

```text
Klose-English::Vocabulary
```

不要按教材、年级或学习阶段拆长期 Deck。Klose 日常只进入这一个学习入口。

---

## 3. 创建唯一 Note Type

Note Type：

```text
Klose Vocabulary
```

从 `Basic` 创建/复制，不要使用 `Basic (and reversed card)`。

字段顺序固定：

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

规则：

- `NoteID` 永久保持第一字段；
- `UserMemo` 只在 Anki 本地维护，不映射 CSV；
- CSV 的 `Tags` 映射到 Anki 自带 Tags；
- 只保留一个 Card Type：`Recognition`；
- `1 Note = 1 Card`，因此首次导入后必须满足 `518 Notes = 518 Cards`。

Card Template 使用：

```text
anki/klose/anki/card_front.html
anki/klose/anki/card_back.html
anki/klose/anki/styling.css
```

### Recognition 学习交互

正面只显示：

```text
Word
```

Klose 在揭示答案前先主动回忆读音和核心意思。

答案面显示并执行：

```text
Word
→ 自动播放 {{tts en_US:Word}}
→ UK / US phonetics
→ MeaningPrimary
→ ExampleSentence
→ ExampleTranslation
```

TTS 只在答案面播放，避免正面提前泄露 pronunciation cue。当前不自动朗读 `ExampleSentence`，例句优先由 Klose 自己朗读；后续若需要，优先增加按需播放，而不是自动连续朗读。

---

## 4. 导入正式发布文件

导入：

```text
anki/klose/publish/anki-import.csv
```

文件自带：

```text
#separator:Comma
#html:false
#notetype:Klose Vocabulary
#deck:Klose-English::Vocabulary
#tags column:12
#columns:...
```

Import Preview 必须核对：

```text
Note Type      = Klose Vocabulary
Deck           = Klose-English::Vocabulary
Existing notes = Update
Match scope    = Note Type
```

字段：

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
UserMemo            → (Nothing)
Tags                → Anki Tags
```

第一条真实数据应从：

```text
KV000001 | book | book
```

开始。如果预览把 `NoteID / Word / ...` 本身当成第一条数据，立即停止导入。

首次导入成功结果：

```text
518 notes found in file
518 new notes imported
```

---

## 5. 第一次只开放四年级新词

导入完成后先不要开始 Study。

保持正常：

```text
tag:stage::grade4-new
```

175 Cards。

Suspend：

```text
tag:stage::grade4-review
```

26 Cards。

再 Suspend：

```text
tag:stage::lower-grade-backfill
```

317 Cards。

最终验收：

```text
deck:"Klose-English::Vocabulary"                     = 518
deck:"Klose-English::Vocabulary" is:suspended        = 343
deck:"Klose-English::Vocabulary" -is:suspended       = 175
```

只有 `518 / 343 / 175` 全部正确后才继续。

Suspend 只用于尚未学习的 New Cards。已经进入 Learning/Review 的旧卡，以后不得因为切换教材、年级或 active scope 而重新 Suspend，避免中断 FSRS 复习链。

---

## 6. 独立 Deck Preset

不要直接修改共享的系统默认 Preset。为：

```text
Klose-English::Vocabulary
```

Clone 独立 Preset：

```text
Klose Vocabulary
```

并确认类似：

```text
Klose Vocabulary (used by 1 deck)
```

---

## 7. 当前正式调度基线

当前第一次上线配置：

```text
Daily Limits
New cards/day                = 8
Maximum reviews/day          = 9999
New cards ignore review limit = OFF
Limits start from top          = OFF

New Cards
Learning steps               = 10m
Insertion order              = Sequential (oldest cards first)

Lapses
Relearning steps             = 10m
Minimum interval             = 1
Leech threshold              = 8
Leech action                 = Tag Only

Display Order
New card gather order        = Ascending position
New card sort order          = Order gathered
New/review order             = Show after reviews
Interday learning/review     = Mix with reviews
Review sort order            = Due date, then random
```

`Graduating interval / Easy interval` 属于旧调度器参数；启用 FSRS 后不作为当前长期调度基线维护。

8 个新词/天是当前起点，不是永久常量。运行约 7–10 天后根据真实负担调整：学习时间稳定、无积压可升至 10/day；若日常负担明显过高可降到 5–6/day。不要通过压低 `Maximum reviews/day` 来隐藏到期复习。

---

## 8. FSRS

当前正式基线：

```text
FSRS                        = ON
Desired retention           = 90%
FSRS parameters             = Default
Reschedule cards on change  = OFF
Check health when optimizing = ON
```

首次没有 Klose 自己的 Review History，因此暂时不要执行：

```text
Optimize Current Preset
Optimize All Presets
```

积累真实学习历史后再评估是否优化参数或提高 Desired Retention。

---

## 9. Desktop 无污染 Preview

第一次正式学习前可以在 Browser 中：

```text
tag:stage::grade4-new
```

任选一张 `Preview`，只检查显示，不在正常 Study 中点击 Again/Good。

预期：

```text
Front
→ only Word

Back
→ Word
→ 自动 Word TTS
→ UK / US phonetics
→ MeaningPrimary
→ ExampleSentence
→ ExampleTranslation
```

Preview 工具栏里的 Replay Audio / Back Side Only / 左右箭头属于 Desktop Preview UI，不是 Card Template 内容。

---

## 10. 同步到 AnkiWeb 与 iPad

Desktop 基线完成后先同步到 AnkiWeb。

如果 AnkiWeb 账号为空，首次同步选择：

```text
Upload to AnkiWeb
```

然后在 iPad 安装当前版 AnkiMobile，登录同一 AnkiWeb 账号，执行首次 Sync。

iPad 端验收：

```text
Deck = Klose-English::Vocabulary
Cards = 518
Suspended = 343
Unsuspended = 175
Preset / FSRS settings 同步正常
Recognition 模板正常
答案面 Word TTS 可播放
```

Klose 日常主要使用 iPad。建议交互：

```text
看到 Word
→ 先口头说出读音和核心意思
→ 轻点显示答案
→ 听标准 Word TTS
→ 核对 IPA / Meaning
→ 自己朗读 ExampleSentence
→ 忘记/读错/意思错：Again
→ 顺畅回忆：Good
```

初期不要求熟练使用 Hard / Easy。

---

## 11. Tags 的所有权

repo 导入的：

```text
source::...
stage::...
learner::...
```

统一视为 system-managed Tags。长期重新导入可能更新这些 Tags，不要把永久个人信息混入其中。

个人信息使用：

```text
UserMemo
```

或 Card Flag。

---

## 12. 第一次导入以后

以后新增 Grade 5、北京版、新概念、升级例句等，统一执行：

```text
修改上游数据
→ rebuild study.csv
→ generate anki-import.csv
→ release gate
→ 重新导入最新版 anki-import.csv
```

详细 SOP：

```text
docs/ANKI_SYNC_WORKFLOW.md
```

已有 NoteID 使用 Update Existing，原 Card / FSRS / Review History 保留；新 NoteID 在同一个主 Deck 中创建 New Card。

---

## 13. Release Gate

正式同步 Anki 前：

```bash
python tools/check_klose_release_ready.py
```

必须通过。它验证：

- `study.csv` 与 Released Set 一致；
- `anki-import.csv` 为 UTF-8 无 BOM；
- `anki-import.csv` headers 正确，数据与 `study.csv` 完全一致；
- 每个 released Note 恰好一个 `stage::` Tag；
- 必填字段完整；
- identity / learner / future-vocabulary review 均为空；
- released Notes 全部 model-reviewed 或 human-reviewed；
- ContentFingerprint 与当前 Meaning / Example / Translation 一致。

CI 必须先通过该 Gate，之后才允许提交 generated release。
