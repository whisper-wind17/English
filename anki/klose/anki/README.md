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

前面显示 Word + 英/美音标；答案面显示核心释义、例句和中文译文。`NoteID`、Sources、SourceBooks 等管理字段不展示给 Klose。

## Deck

长期主 Deck：

```text
Klose-English::Vocabulary
```

教材、年级、学习阶段由 system-managed Tags 表达，不拆成长期子 Deck。
