# Klose Vocabulary：当前 Release 导入 Anki

本文用于把 **已经通过 GitHub Release Gate 的当前 Vocabulary Release** 安全同步到既有 Anki Collection。

它不是 Word-first → NoteID-first 迁移文档，也不负责重建 FSRS / Due / Review History。长期原则仍以 `docs/ANKI_SYNC_WORKFLOW.md` 为准。

## 1. 当前 Release snapshot

2026-09-10 checkpoint：

```text
Stable active Vocabulary Notes = 1189
Released Notes                 = 972
Current Learning allowed       = 627
Held library                   = 345
Allowed but unreleased         = 0
Review pending                 = 0
LearnerLevel                   = 4
LearningOrder                  = 000001..000627
```

正式导入文件只有：

```text
anki/klose/publish/anki-import.csv
```

当前 artifact：

```text
Note Type = Klose Vocabulary
Deck      = Klose-English::Vocabulary
Rows      = 972
Identity  = NoteID
```

`study.csv` 只用于 repo 审计，不直接导入 Anki。

## 2. 导入前：先确认 Note Type schema

现有 `Klose Vocabulary` 必须继续原地使用，不要新建第二套 Note Type，不要 Change Note Type，不要删除/recreate Cards。

字段契约：

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

如果 `PromptHint` 或 `LearningOrder` 尚不存在，只在现有 Note Type 中原地增加并 reposition：

```text
docs/ANKI_PROMPTHINT_MIGRATION.md
docs/ANKI_LEARNING_ORDER_MIGRATION.md
```

这两个文档中的 `638 / 221 / 417` 是当时 Grade-4 一次性迁移 snapshot；**不要把这些旧计数用于当前 972-note Release 的验收或 suspension reset**。

## 3. 备份

正式导入前先做 Anki Collection/Deck 备份。

重点不是担心内容 CSV 本身，而是保证任何误操作都不能破坏：

```text
Review History
FSRS memory state
Due / Interval
已有 Card identity
UserMemo
```

## 4. 导入 972-note 正式包

导入：

```text
anki/klose/publish/anki-import.csv
```

要求：

```text
Note Type       = Klose Vocabulary
Deck            = Klose-English::Vocabulary
Existing Notes  = Update
Match scope     = Note Type
第一字段 / Identity = NoteID
Tags            -> Anki Tags
UserMemo        -> Nothing / 不映射
```

字段映射至少确认：

```text
NoteID             -> NoteID
CanonicalWord      -> CanonicalWord
Word               -> Word
PromptHint         -> PromptHint
British            -> British
American           -> American
MeaningPrimary     -> MeaningPrimary
ExampleSentence    -> ExampleSentence
ExampleTranslation -> ExampleTranslation
LearnerLevel       -> LearnerLevel
LearningOrder      -> LearningOrder
Sources            -> Sources
SourceBooks        -> SourceBooks
Tags               -> Tags
```

不要选择“忽略已有 Notes”，也不要创建新的 `Klose Vocabulary (2)` 一类 Note Type。

导入完成后的稳定目标是：

```text
Klose Vocabulary Notes / Cards = 972 / 972
```

如果设备此前只同步到最初 518-note Release，本次会有更多新增；如果已经同步到 638-note Grade-4 Release，则主要新增当前 334-note Release delta。**不要用“新增了多少条”作为唯一正确性判断，最终 Stable NoteID universe 才是判断依据。**

## 5. 先验证旧 Card 没有被重建

至少抽查 3–5 张此前已经存在的 NoteID：

```text
Card Info -> Reviews 仍存在
Due / Interval 未被内容导入重置
NoteID 未变化
Card Type 仍只有 Recognition
```

如果任何已有 Card 的 Review History 被清零，停止后续操作，先从备份恢复并排查 Note Type / Identity mapping。

## 6. Learning Admission：只对 New Cards materialize

repo 当前 admission truth：

```text
allowed = 627
held    = 345
```

当前 allowed Notes 由 system-managed learning tags 标识：

```text
learning::klose::grade4
learning::klose::grade5-6
```

### 已经产生真实学习历史时

不要执行“全部 Suspend → 全部重置”的旧初始化流程。

只调整仍为 `is:new` 的 Cards：

```text
allowed + is:new  -> 应允许进入 New queue
held    + is:new  -> 应保持 suspended
Learning / Review -> 不因 curriculum release 批量改 suspension / Due
```

这保证 GitHub 只决定未来学习准入，不覆盖 Anki 已形成的记忆状态。

### Collection 尚未开始真实学习时

只有在确认所有目标 Cards 都仍是未学习 New Card、没有 Review History 的一次性初始化窗口，才可以按当前 627/345 admission 全量 materialize suspension。

不要再使用旧 Grade-4 snapshot 的 `221 / 417` 作为当前目标。

## 7. LearningOrder：只排序仍未学习的 allowed New Cards

`LearningOrder` 当前为：

```text
000001..000627
```

它是 GitHub curriculum order，不是 FSRS Due。

仅选择：

```text
current allowed
AND is:new
AND not suspended
```

按 `LearningOrder` 升序后执行：

```text
Cards -> Reposition
Start position = 1
Step           = 1
Randomize      = OFF
Shift existing = ON
```

如果已有部分 current Cards 已经进入 Learning / Review，那么本次可 reposition 的 New Card 数量自然会小于 627；这是正常状态，**不要为了凑到 627 去重排已学习 Cards**。

## 8. 导入后的检查

至少确认：

```text
Total Notes / Cards              = 972 / 972
Note Type                        = Klose Vocabulary
Card Type                        = Recognition only
Review pending in repo           = 0
PromptHint nonempty              = 4
LearningOrder maximum            = 000627
existing Review History          = preserved
existing Due / Interval          = preserved
new/day / FSRS deck options      = unchanged by CSV import
```

PromptHint 抽查：

```text
KV000424 cook -> n.
KV000805 cook -> v.
KV000816 over -> 位置
KV000863 over -> 结束
```

再抽查 Grade 5–6 新 Note，确认 Word / IPA / Meaning / Example / Translation / LearningOrder 均已出现。

## 9. Sync 到 iPad

Desktop 验收通过后：

```text
Anki Desktop -> Sync -> AnkiWeb
iPad AnkiMobile -> Sync
```

iPad 继续使用同一：

```text
Deck      = Klose-English::Vocabulary
Note Type = Klose Vocabulary
Card Type = Recognition
```

同步完成后，再抽查一张旧卡和一张 Grade 5–6 新卡。

## 10. 完成标准

只有同时满足以下条件，才把 repo 中 `Anki Updated` 记为 true：

```text
972-note anki-import.csv 已实际导入
已有 NoteID 原地更新，没有批量 duplicate Notes
旧 Card Review History / FSRS / Due 保留
新 release Notes 已创建
New Card admission/suspension 与当前 policy 一致
仍为 New 的 current Cards 按 LearningOrder 排序
Desktop 已同步到 AnkiWeb
iPad 已同步并抽查通过
```

GitHub Release 完成不等于 Anki Updated；二者必须独立 checkpoint。
