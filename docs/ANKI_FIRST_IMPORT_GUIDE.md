# Klose Vocabulary：Anki 第一次正式导入实操指南

> 本文记录 2026-09-05 实际完成的第一次正式导入全过程，目标是让未来重新初始化设备、迁移环境或复查配置时，可以按同一流程复现。
>
> 架构规则以 `docs/ANKI_FIRST_IMPORT.md` 为准；本文是对应的 **逐步操作版 / 实操复盘版**。

## 0. 最终目标

第一次正式导入完成后，系统应满足：

```text
Deck              = Klose-English::Vocabulary
Note Type         = Klose Vocabulary
Card Type         = Recognition
1 Note            = 1 Card
Released Notes    = 518
Suspended         = 343
Unsuspended       = 175
New cards/day     = 8
FSRS              = ON
Desired retention = 90%
AnkiWeb            = 已由 Desktop Upload
```

当前 518 张卡的学习阶段：

```text
stage::grade4-new            175   Unsuspended
stage::grade4-review          26   Suspended
stage::lower-grade-backfill  317   Suspended
```

正式导入文件始终是：

```text
anki/klose/publish/anki-import.csv
```

不要直接导入 `study.csv`。

---

## 1. 创建唯一主 Deck

Anki Desktop：

```text
Decks
→ Create Deck
```

创建：

```text
Klose-English::Vocabulary
```

Anki 会把 `::` 显示为层级：

```text
Klose-English
└── Vocabulary
```

不要另外创建 Grade 4、人教版、四上、四下等长期 Deck。教材、年级和学习阶段全部由 Tags 管理。

**验收：** 首页能看到 `Klose-English > Vocabulary`。

**截图位：** `01-create-main-deck.png`

---

## 2. 创建 `Klose Vocabulary` Note Type

进入：

```text
Tools
→ Manage Note Types
→ Add
```

基于 `Basic` 创建，不要使用 `Basic (and reversed card)`。

名称：

```text
Klose Vocabulary
```

字段顺序固定为：

```text
1.  NoteID
2.  CanonicalWord
3.  Word
4.  British
5.  American
6.  MeaningPrimary
7.  ExampleSentence
8.  ExampleTranslation
9.  LearnerLevel
10. Sources
11. SourceBooks
12. UserMemo
```

其中：

- `NoteID` 必须是第一字段；
- `UserMemo` 是 Anki-local 字段，不从 CSV 更新；
- CSV 的 Tags 映射到 Anki 原生 Tags，不创建普通 `Tags` 字段。

**验收：** 共 12 个字段，顺序与上面完全一致。

**截图位：** `02-note-type-fields.png`

---

## 3. 配置唯一 Recognition Card

进入：

```text
Tools
→ Manage Note Types
→ Klose Vocabulary
→ Cards...
```

只保留一个 Card Type，命名为：

```text
Recognition
```

不要建立 Reverse Card。

### 3.1 Front Template

```html
<div class="word">{{Word}}</div>
```

正面只显示 `Word`。不要提前显示音标或释义，让 Klose 先主动回忆：

```text
Word → pronunciation
Word → core meaning
```

**截图位：** `03-card-front-template.png`

### 3.2 Back Template

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

答案面揭示后自动播放单词 TTS。TTS 放在答案面，避免问题面泄露读音。

当前 **不自动朗读 ExampleSentence**。例句优先让 Klose 自己读；以后若有需要，优先做“按需播放”，而不是揭示答案后自动连续朗读。

**截图位：** `04-card-back-template.png`

### 3.3 Styling

```css
.card {
  font-family: Arial, "PingFang SC", "Microsoft YaHei", sans-serif;
  font-size: 22px;
  text-align: center;
  color: #222;
  background: #fff;
  padding: 18px;
}

.word {
  font-size: 34px;
  font-weight: 700;
  margin-bottom: 10px;
}

.phonetic {
  font-size: 17px;
  color: #666;
  margin: 2px 0;
}

#answer {
  margin: 18px 0;
}

.meaning {
  font-size: 26px;
  font-weight: 600;
  margin-bottom: 16px;
}

.example {
  font-size: 22px;
  line-height: 1.45;
  margin-top: 12px;
}

.translation {
  font-size: 18px;
  line-height: 1.45;
  color: #666;
  margin-top: 8px;
}
```

**验收：**

```text
1 Note = 1 Recognition Card
Front  = Word only
Back   = Word + TTS + IPA + Meaning + Example + Translation
```

---

## 4. 导入 `anki-import.csv`

进入：

```text
File
→ Import
```

选择：

```text
anki/klose/publish/anki-import.csv
```

不要选 `study.csv`。

### 4.1 顶部导入选项

确认：

```text
Field separator   = Comma
Allow HTML        = Off
Note Type         = Klose Vocabulary
Deck              = Klose-English::Vocabulary
Existing notes    = Update
Match scope       = Note Type
Tag all notes     = 空
Tag updated notes = 空
```

**截图位：** `05-import-options.png`

### 4.2 字段映射

```text
1   NoteID              → NoteID
2   CanonicalWord       → CanonicalWord
3   Word                → Word
4   British             → British
5   American            → American
6   MeaningPrimary      → MeaningPrimary
7   ExampleSentence     → ExampleSentence
8   ExampleTranslation  → ExampleTranslation
9   LearnerLevel        → LearnerLevel
10  Sources             → Sources
11  SourceBooks         → SourceBooks
12  Tags                → Anki Tags

UserMemo                → (Nothing)
```

`UserMemo = (Nothing)` 是长期设计的一部分，确保 repo 更新不会覆盖 Anki 本地个人备注。

**截图位：**

```text
06-import-field-mapping-1.png
07-import-field-mapping-2.png
```

### 4.3 预览第一条真实数据

把预览横向滚动到最左，必须看到：

```text
KV000001 | book | book
KV000002 | ruler | ruler
KV000003 | pencil | pencil
```

不能出现：

```text
NoteID | CanonicalWord | Word
```

作为第一张数据卡。

**截图位：** `08-import-preview-first-rows.png`

### 4.4 正式 Import

点击 `Import` 后，本次基线实际结果：

```text
518 notes found in file
518 new notes imported
```

无 skipped / duplicate / failed。

**截图位：** `09-import-result-518.png`

---

## 5. 第一次只开放四年级新词

导入后 **不要立即 Study**。

进入：

```text
Browse
```

### 5.1 Suspend `grade4-review`

搜索：

```text
tag:stage::grade4-review
```

本次结果：

```text
26 cards
```

执行：

```text
Ctrl + A
→ Cards
→ Toggle Suspend
```

**截图位：** `10-grade4-review-26.png`

### 5.2 Suspend `lower-grade-backfill`

搜索：

```text
tag:stage::lower-grade-backfill
```

本次结果：

```text
317 cards
```

同样 Suspend。

**截图位：** `11-lower-grade-backfill-317.png`

### 5.3 总数验收

依次搜索：

```text
deck:"Klose-English::Vocabulary"
deck:"Klose-English::Vocabulary" is:suspended
deck:"Klose-English::Vocabulary" -is:suspended
```

必须得到：

```text
518
343
175
```

只有 `518 / 343 / 175` 同时正确，才进入调度配置。

---

## 6. 为 Vocabulary 建独立 Preset

不要直接修改共享的“系统默认” Preset。

第一次检查时，父 Deck `Klose-English` 的 Options 显示：

```text
系统默认 (used by 3 decks)
```

这意味着直接修改会影响其他 Deck。

正确操作：

```text
Klose-English::Vocabulary
→ Options
→ Preset 下拉
→ Clone
```

命名：

```text
Klose Vocabulary
```

验收：

```text
Klose Vocabulary (used by 1 deck)
```

**截图位：**

```text
12-wrong-parent-options.png
13-vocabulary-options.png
```

---

## 7. Daily Limits / New Cards / Display Order

最终实际配置：

### Daily Limits

```text
New cards/day                 = 8
Maximum reviews/day           = 9999
New cards ignore review limit = Off
Limits start from top         = Off
```

原则：控制“新词进入速度”，不要人为截断已经到期的 Review。

### New Cards

```text
Learning steps      = 10m
Insertion order     = Sequential (oldest cards first)
Graduating interval = 1     # 保持默认，FSRS 开启后不再是核心参数
Easy interval       = 4     # 保持默认，FSRS 开启后不再是核心参数
```

### Lapses

```text
Relearning steps = 10m
Minimum interval = 1
Leech threshold  = 8
Leech action     = Tag Only
```

### Display Order

```text
New card gather order      = Ascending position
New card sort order        = Order gathered
New/review order           = Show after reviews
Interday learning/review   = Mix with reviews
Review sort order          = Due date, then random
```

这样保证：

```text
先完成到期 Review
→ 再学习当天 New
```

并尽量维持教材 / Card Position 顺序，而不是随机打乱四上、四下。

**截图位：** `14-daily-limits-display-order.png`

---

## 8. 开启 FSRS

FSRS 是全局调度器开关；`Desired retention` 等参数按 Preset 管理。

本次最终配置：

```text
FSRS                         = ON
Desired retention            = 90%
FSRS parameters              = Default
Reschedule cards on change   = OFF
Check health when optimizing = ON
```

当前没有真实 Review History，因此：

```text
不要 Optimize Current Preset
不要 Optimize All Presets
```

先使用默认 FSRS 参数。积累真实学习记录后再考虑 Optimize。

**截图位：** `15-fsrs-settings.png`

---

## 9. Desktop 无污染 Preview 验收

在 Browse 中搜索：

```text
tag:stage::grade4-new
```

任选一张，点击 `Preview`。

预期问题面：

```text
house
```

只显示 Word。

揭示答案后：

```text
house
→ 自动播放标准 TTS
→ UK / US IPA
→ 中文核心释义
→ ExampleSentence
→ ExampleTranslation
```

Preview 底部出现：

```text
Replay Audio | Back Side Only | < | >
```

这一行是 **Anki Preview 工具栏，不是 Card Template 内容**。

`Replay Audio` 也帮助我们发现：最初模板只有 IPA、没有真正音频；因此最终在 Back Template 中增加了：

```html
{{tts en_US:Word}}
```

当前不自动播放 ExampleSentence。

**截图位：** `16-preview-replay-audio.png`

---

## 10. 同步到 AnkiWeb

本次 AnkiWeb 账号原本没有 Cards，因此第一次同步：

```text
Desktop
→ Sync
→ 登录 AnkiWeb
→ Upload to AnkiWeb
```

`Upload` 方向正确，因为：

```text
Desktop = 完整、已验证 Collection
AnkiWeb = 空
```

同步后，AnkiWeb 保存当前 Collection，包括：

```text
518 Notes / Cards
Klose Vocabulary Note Type
Recognition Card Template
Deck / Tags
Suspend 状态
FSRS / Preset 配置
Review History（当前尚未正式开始）
```

TTS 使用模板 `{{tts en_US:Word}}`，不是 518 个 mp3 媒体文件。

---

## 11. iPad 首次同步（下一阶段）

在 iPad 安装官方 `AnkiMobile Flashcards`，使用与 Desktop 相同的 AnkiWeb 账号。

因为 iPad 是空 Collection、AnkiWeb 已经是正确基线，所以首次同步方向应为：

```text
iPad
→ Synchronize
→ Download from AnkiWeb
```

不要反向 Upload 空 Collection。

iPad 同步后先不要正式学习，先核对：

```text
Deck = Klose-English::Vocabulary
New today = 8
Card Front = Word only
Reveal Answer = 自动播放 Word TTS
343 cards 仍 Suspended
175 cards 可学习
FSRS / Preset 正常
```

Klose 的第一条真正 Review History 应由 Klose 自己在 iPad 上产生，而不是 Desktop 试跑时随便点击 Again / Good。

---

## 12. Klose 日常操作规则

主要学习端：iPad AnkiMobile。

推荐交互：

```text
看到 Word
→ 先自己说出读音和核心意思
→ 轻点屏幕揭示答案
→ 听标准单词发音
→ 核对 IPA / Meaning
→ 自己朗读 ExampleSentence
→ 理解 ExampleTranslation
→ 评分
```

初期评分简化为：

```text
忘记 / 读错 / 核心意思错 → Again
能够顺畅回忆             → Good
```

暂时不要求 Klose 精细区分 Hard / Easy。

---

## 13. 第一次导入最终验收表

```text
[✓] Main Deck = Klose-English::Vocabulary
[✓] Note Type = Klose Vocabulary
[✓] 12 fields，NoteID 第一字段
[✓] 1 Note = 1 Recognition Card
[✓] Front = Word only
[✓] Back = Word TTS + IPA + Meaning + Example + Translation
[✓] Import source = publish/anki-import.csv
[✓] 518 new notes imported
[✓] grade4-review = 26 Suspended
[✓] lower-grade-backfill = 317 Suspended
[✓] Total / Suspended / Active = 518 / 343 / 175
[✓] Preset = Klose Vocabulary (used by 1 deck)
[✓] New cards/day = 8
[✓] Reviews before new
[✓] FSRS = ON
[✓] Desired retention = 90%
[✓] FSRS Parameters = Default
[✓] Reschedule cards on change = OFF
[✓] Desktop Preview 正确
[✓] Word TTS 正确
[✓] Desktop → AnkiWeb 使用 Upload 完成
[ ] iPad AnkiMobile 首次 Download 与最终验收
```

---

## 14. 截图归档约定

本文对应的实操截图统一放在：

```text
docs/images/anki-first-import/
```

建议文件名：

```text
01-create-main-deck.png
02-note-type-fields.png
03-card-front-template.png
04-card-back-template.png
05-import-options.png
06-import-field-mapping-1.png
07-import-field-mapping-2.png
08-import-preview-first-rows.png
09-import-result-518.png
10-grade4-review-26.png
11-lower-grade-backfill-317.png
12-wrong-parent-options.png
13-vocabulary-options.png
14-daily-limits-display-order.png
15-fsrs-settings.png
16-preview-replay-audio.png
```

后续若 UI 版本变化，优先保留“规则 + 验收条件”，截图只是当前版本 Anki Desktop 的视觉参考。
