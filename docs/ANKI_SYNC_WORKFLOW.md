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
→ Learning Admission
→ Learner Review / Approval
→ Release Registry
→ study.csv
→ anki-import.csv
→ Release Gate
→ Anki
```

GitHub 负责 Source / Identity / Learner Presentation / Review / Release；Anki 负责：

```text
Review History
FSRS memory state
Due / Interval
Card State
```

这些 Anki 状态不得由 repo 重建。

## 3. 什么变化会触发 review / sync

以下变化通过上游修改、重新构建、审校后导入最新版 `anki-import.csv`：

- 新教材或新来源；
- 新 learning unit / NoteID；
- provenance 更新；
- Word / IPA / Meaning 修正；
- LearnerLevel、ExampleSentence、ExampleTranslation 变化；
- 非空 `PromptHint` 新增/修改；
- Learning Admission / system-managed Tags 变化；
- release scope 变化。

`PromptHint` 属于 Learner Presentation，不属于 Source 或 Identity。普通 Notes 留空；只有正面存在真实 target-sense 歧义时使用最小提示。

## 4. 固定同步 SOP

### Step 1：只修改上游

根据变更类型修改：

```text
Raw Source / Source Adapter
Identity Registry / Source Identity Map
Vocabulary facts
Learner presentation / overrides / PromptHint
Learning Admission
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

### Step 3：重新构建

正常 CI 顺序包括：

```text
check persistent state
→ build vocabulary
→ actual-source overlays
→ build learning admission
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
Sources
SourceBooks
UserMemo
```

`UserMemo` 只在 Anki 本地维护，不映射 repo CSV。

如果 repo 的 Note Type contract 新增字段，例如首次引入 `PromptHint`，必须先在 **现有同一个 Note Type** 中增加字段并更新 Card Template；不要创建第二套 Note Type，也不要删除/重建 Cards。

PromptHint 一次性迁移 SOP：

```text
docs/ANKI_PROMPTHINT_MIGRATION.md
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

## 5. 典型场景

### 新增教材版本

```text
new source evidence
→ source identity matching
→ same sense reuse Stable NoteID
→ new sense/new unit append NoteID
→ learner presentation / admission / review
→ rebuild
→ import same Note Type
```

### 提前开放 Grade 5

```text
Grade-5 actual source / admission
→ learner presentation at appropriate LearnerLevel
→ review
→ rebuild
→ import
→ only newly admitted New Cards are unsuspended
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

## 6. 长期不变量

```text
Vocabulary Identity  → Stable NoteID
Anki 学习入口         → 一个主 Deck
Anki Note Type        → 同一个 Klose Vocabulary 原地演进
Anki 同步入口         → anki-import.csv
```

核心原则：

> 修改发生在上游；publish 是确定性生成物；Anki 保留长期记忆状态；Note Type schema migration 只做原地扩展，不重建 identity/card history。
