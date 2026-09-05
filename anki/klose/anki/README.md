# Anki Note / Card Contract

本目录冻结 Klose Vocabulary 在 Anki 中的长期显示与管理契约。

## Note Type

```text
Klose Vocabulary
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

`NoteID` 必须保持第一字段；`UserMemo` 只在 Anki 本地维护，不从 repo CSV 更新。

`LearningOrder` 属于 Learning Admission / curriculum metadata，不属于 Vocabulary Identity，也不是 FSRS state。正式序列化固定为 **6 位十进制零填充字符串**：

```text
000001 .. 999999
```

当前 Grade-4 allowed Notes 使用 `000001..000221`；417 个 held Notes 的 `LearningOrder` 必须为空。固定 6 位是长期存储/发布契约，避免词库扩大后从 3 位迁移到 4/5 位；同时保证 Anki 按文本排序与数值排序得到相同次序。

它用于在 Anki 中把尚未学习的 New Cards 按真实教材顺序一次性 Reposition；实际 `New # / Due / Review History` 仍由 Anki 管理。

`LearningOrder` 不展示给 Klose，也不进入 learner content fingerprint；调整学习顺序不需要重新审校释义/例句，但必须通过 Learning Admission / Release Gate 校验。

`PromptHint` 属于 Learner Presentation，只用于正面存在真实 target-sense 歧义时做最小消歧。普通 Note 必须留空，不把释义提前泄露到问题面。

当前 Grade-4 active set 使用：

```text
KV000424  cook  -> n.
KV000805  cook  -> v.
KV000816  over  -> 位置
KV000863  over  -> 结束
```

`PromptHint` 不改变 Stable NoteID / Card identity / FSRS history；非空值属于 release-visible presentation，变更后必须重新 review。

## Card Type

只保留 **1 个** Card Type，建议命名：

```text
Recognition
```

不要使用 `Basic (and reversed card)`，也不要额外创建反向卡。当前学习/统计设计基于：

```text
1 Note = 1 Card
```

Card Template：

```text
card_front.html
card_back.html
styling.css
```

## Recognition 交互契约

正面显示：

```text
Word
PromptHint（仅非空时）
```

不在正面显示音标、TTS、LearningOrder 或核心释义。目标是在揭示答案前主动回忆：

```text
Word + minimal disambiguation cue
→ pronunciation
→ target core meaning
```

普通词没有 `PromptHint`，体验仍然等同于只看到 `Word`。

答案面显示：

```text
Word + optional PromptHint（通过 FrontSide）
标准单词 TTS（en_US）
UK / US phonetics
MeaningPrimary
ExampleSentence
ExampleTranslation
```

`card_back.html` 使用：

```html
{{tts en_US:Word}}
```

因此揭示答案后自动播放单词标准发音，用于核对学习者刚才的主动发音回忆。TTS 放在答案面而不是问题面，避免提前泄露 pronunciation cue。

当前**不自动朗读 ExampleSentence**。例句首先由 Klose 自己朗读，用于语境理解与完整句子阅读训练；若以后需要例句朗读，优先设计按需播放，而不是答案揭示后自动连续朗读。

这保留了检索练习的 recall boundary，同时仍维持 `1 Note = 1 Card`，不额外建立 pronunciation/reverse cards，也不需要维护逐词 mp3 字段。

`NoteID`、Sources、SourceBooks、LearnerLevel、LearningOrder 等管理字段不展示给 Klose。

## iPad / AnkiMobile 作为主要学习端

Klose 日常主要使用 iPad AnkiMobile。默认交互不依赖键盘：

```text
看到 Word（必要时附最小 PromptHint）
→ 先口头回忆读音和目标意思
→ 轻点卡片显示答案
→ 自动听 Word 标准 TTS
→ 核对音标、释义
→ 自己朗读 ExampleSentence
→ Again / Good 为主要反馈
```

AnkiMobile 的 TTS 使用设备可用的系统语音；repo 不保存对应音频媒体文件。

初期不要求 Klose 熟练使用 Hard / Easy，优先形成一致的自评规则：

```text
忘记 / 读错 / 核心意思错 → Again
能较顺畅回忆             → Good
```

桌面版负责首次建库、Note Type / Template 管理和批量导入；同步到 AnkiWeb 后，iPad 使用同一 Note Type、Card Template、Deck 与 FSRS 学习历史。

## Deck

长期主 Deck：

```text
Klose-English::Vocabulary
```

教材、年级、学习阶段由 system-managed Tags 表达，不拆成长期子 Deck。
