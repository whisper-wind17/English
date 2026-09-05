# Klose Vocabulary：长期 Anki 同步流程

本文定义 repo 与 Anki 之间长期、重复执行的同步契约。

## 1. 两个发布文件

```text
anki/klose/publish/study.csv
```

是 **Released Set 的内部标准快照**，用于构建、审计、diff、release 对账，不直接给 Anki 使用。

```text
anki/klose/publish/anki-import.csv
```

是 **面向 Anki 的唯一正式发布产物**。它由 `study.csv` 自动生成，数据必须完全一致，只额外带 Anki `#...` file headers。

二者都是 generated output：

```text
禁止手工编辑 study.csv
禁止手工编辑 anki-import.csv
```

## 2. 长期数据流

```text
Raw Source / Curation
→ Identity + Source Occurrences
→ Vocabulary Master
→ Learner Presentation
→ Learning Admission + LearningOrder
→ Learner Review / Approval
→ Release Registry
→ study.csv
→ anki-import.csv
→ Release Gate
→ Anki
```

GitHub 负责：

```text
Source / Identity / Learner Presentation / Learning Admission / LearningOrder / Review / Release
```

Anki 负责：

```text
Review History
FSRS memory state
Due / Interval
New Card Position
Card State
```

这些 Anki 状态不得由 repo 重建。

特别区分：

```text
LearningOrder     = GitHub 中的 curriculum / admission 真源
New Card Position = Anki 中尚未学习新卡的物理排序状态
```

`LearningOrder` 的正式序列化固定为 6 位十进制零填充字符串 `000001..999999`。当前 Grade-4 为 `000001..000221`；固定宽度用于保证未来扩展到数千/数万学习单元时不需要再次迁移，并保证文本排序稳定。一旦 Card 进入真实 Learning / Review，不用 LearningOrder 重写其 FSRS / Due。

## 3. 什么变化会触发 review / sync

以下变化通过上游修改、重新构建、审校后导入最新版 `anki-import.csv`：

- 新教材或新来源；
- 新 learning unit / NoteID；
- provenance 更新；
- Word / IPA / Meaning 修正；
- LearnerLevel、ExampleSentence、ExampleTranslation 变化；
- 非空 `PromptHint` 新增/修改；
- Learning Admission / LearningOrder / system-managed Tags 变化；
- release scope 变化。

`PromptHint` 属于 Learner Presentation，不属于 Source 或 Identity。普通 Notes 留空；只有正面存在真实 target-sense 歧义时使用最小提示。

`LearningOrder` 属于 Learning Admission metadata，不进入 learner content fingerprint。调整学习顺序不要求重新审校 Meaning / Example，但必须通过 Admission / Release Gate。

## 4. 固定同步 SOP

### Step 1：只修改上游

根据变更类型修改：

```text
Raw Source / Source Adapter
Identity Registry / Source Identity Map
Vocabulary facts
Learner presentation / overrides / PromptHint
Learning Admission / LearningOrder
Release Registry
```

不要通过编辑 `publish/*.csv` 修最终结果。

### Step 2：完成审校

当前 fingerprint 绑定 Word / Sense / IPA / Meaning / Example / LearnerLevel，以及非空 PromptHint。

内容变化后：

```text
sync review registry
→ changed Note = pending
→ explicit review / approval
→ pending = 0
```

空 `PromptHint` 不改变历史 v2 hash；非空 PromptHint 会使对应 Note 重新 pending。

`LearningOrder` 不属于内容 fingerprint；只改变它不会使 learner review pending。

### Step 3：重新构建

正常 CI 顺序包括：

```text
check persistent state
→ build vocabulary
→ actual-source overlays
→ build learning admission + LearningOrder
→ learner presentation overlays
→ PromptHint overlay
→ sync review registry
→ learner checks
→ release gate
```

本地排查时使用对应 `tools/` 脚本，不要跳过最终：

```text
tools/check_klose_release_ready.py
```

### Step 4：Release Gate

至少确认：

```text
study.csv == Released Set
anki-import.csv data == study.csv
NoteID unique
review pending == 0
ContentFingerprint stale == 0
review queues == 0
Learning Admission valid
allowed LearningOrder == exact textbook order + fixed six-digit format
held LearningOrder == blank
Anki headers / columns valid
UTF-8 without BOM
```

Gate 未通过不得导入 Anki。

### Step 5：确认 Anki Note Type contract

长期 Note Type：

```text
Klose Vocabulary
```

当前字段顺序：

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

`UserMemo` 只在 Anki 本地维护，不映射 repo CSV。

`PromptHint` 与 `LearningOrder` 都通过现有 Note Type 原地增加字段，不创建第二套 Note Type、不删除/重建 Cards。

一次性 schema migration SOP：

```text
docs/ANKI_PROMPTHINT_MIGRATION.md
docs/ANKI_LEARNING_ORDER_MIGRATION.md
```

### Step 6：导入 Anki

始终导入：

```text
anki/klose/publish/anki-import.csv
```

长期保持：

```text
Note Type       = Klose Vocabulary
Deck            = Klose-English::Vocabulary
Existing notes  = Update
Match scope     = Note Type
Identity        = NoteID
```

Stable NoteID 已存在时更新原 Note；新 NoteID 创建新 Note。已有 Card 的 FSRS / Review History / Due / Interval 不应因内容更新而重建。

### Step 7：Learning Admission → Suspend / Unsuspend

当前学习范围由 system-managed learning tag 决定，不由 FirstGrade 决定。

对于尚未进入真实 Review History 的初始迁移窗口，可以按当前 admission 重置：

```text
Suspend 全部当前 Klose Vocabulary Cards
→ Unsuspend tag:learning::klose::grade4
```

预期当前 Grade-4：

```text
Total = 638
Unsuspended current = 221
Held suspended = 417
```

进入真实学习后，长期原则是：不要仅因来源/教材 scope 改变而批量 Suspend 已经处于 Learning/Review 的旧卡；FSRS 状态由 Anki 持续维护。

### Step 8：尚未学习的新卡按 LearningOrder 初始化 New #

仅在目标 Cards 仍为 `is:new` 时执行。

当前 Grade-4 一次性操作见：

```text
docs/ANKI_LEARNING_ORDER_MIGRATION.md
```

核心逻辑：

```text
tag:learning::klose::grade4 -is:suspended is:new
→ 必须 = 221
→ 按 LearningOrder 000001..000221 升序
→ Reposition: Start=1, Step=1, Randomize=OFF, Shift existing=ON
```

这只 materialize 尚未学习新卡的初始顺序，不把 GitHub 变成 FSRS / Due 真源。

## 5. 典型场景

### 新增教材版本

```text
new source evidence
→ source identity matching
→ same sense reuse Stable NoteID
→ new sense/new unit append NoteID
→ learner presentation / admission / order / review
→ rebuild
→ import same Note Type
```

### 提前开放 Grade 5

```text
Grade-5 actual source / admission
→ define current LearningOrder for newly admitted New Cards
→ learner presentation at appropriate LearnerLevel
→ review
→ rebuild
→ import
→ only newly admitted New Cards are unsuspended / sequenced
```

### 升级旧 Note 的 learner presentation

```text
NoteID 不变
→ Example / PromptHint / LearnerLevel 等变化
→ fingerprint 变化
→ explicit re-review
→ rebuild / import
→ original Card + FSRS history continue
```

### 调整尚未学习的新词顺序

```text
NoteID / content 不变
→ LearningOrder 变化
→ no content re-review
→ Release Gate validates order
→ import same Note Type
→ only affected is:new Cards may be Repositioned
```

## 6. 长期不变量

```text
Vocabulary Identity   → Stable NoteID
Curriculum sequencing → LearningOrder in GitHub, fixed six-digit serialization
Anki memory state      → FSRS / Due / New # in Anki
Anki 学习入口          → 一个主 Deck
Anki Note Type         → 同一个 Klose Vocabulary 原地演进
Anki 同步入口          → anki-import.csv
```

核心原则：

> 修改发生在上游；publish 是确定性生成物；GitHub 保存教学意图，Anki 保存真实记忆状态；Note Type schema migration 只做原地扩展，不重建 identity/card history。
