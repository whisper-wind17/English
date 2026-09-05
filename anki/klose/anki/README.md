# Anki Note / Card Contract

本目录冻结 Klose Vocabulary 在 Anki 中的长期显示契约。

## Note Type

```text
Klose Vocabulary
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

`NoteID` 必须保持第一字段；`UserMemo` 只在 Anki 本地维护，不从 repo CSV 更新。

## Card Type

只保留 **1 个** Card Type，建议命名：

```text
Recognition
```

不要使用 `Basic (and reversed card)`，也不要额外创建反向卡。当前学习/统计设计基于：

```text
1 Note = 1 Card
```

因此 Grade-4 Baseline v1：

```text
518 Notes = 518 Cards
```

Card Template：

```text
card_front.html
card_back.html
styling.css
```

## Recognition 交互契约

正面只显示：

```text
Word
```

不在正面显示音标或释义。目标是让学习者在揭示答案前主动回忆：

```text
Word → pronunciation
Word → core meaning
```

答案面显示：

```text
Word
UK / US phonetics
MeaningPrimary
ExampleSentence
ExampleTranslation
```

这保留了检索练习的 recall boundary，同时仍维持 `1 Note = 1 Card`，不额外建立 pronunciation/reverse cards。

`NoteID`、Sources、SourceBooks、LearnerLevel 等管理字段不展示给 Klose。

## iPad / AnkiMobile 作为主要学习端

Klose 日常主要使用 iPad AnkiMobile。默认交互不依赖键盘：

```text
看到 Word
→ 先口头回忆读音和意思
→ 轻点卡片任意位置 Show Answer
→ 核对音标、释义和例句
→ Again / Good 为主要反馈
```

AnkiMobile 默认在问题面点击卡片任意区域即可显示答案；答案面可以直接点击底部评分按钮。初期不要求 Klose 熟练使用 Hard / Easy，优先形成一致的自评规则：

```text
忘记 / 读错 / 核心意思错 → Again
能较顺畅回忆             → Good
```

桌面版负责首次建库、Note Type / Template 管理和批量导入；同步到 AnkiWeb 后，iPad 继续使用同一 Note Type、Card Template、Deck 与 FSRS 学习历史。

## Deck

长期主 Deck：

```text
Klose-English::Vocabulary
```

教材、年级、学习阶段由 system-managed Tags 表达，不拆成长期子 Deck。
