# Klose Vocabulary：长期 Anki 同步流程

本文定义 repo 与 Anki 之间长期、可重复执行的同步契约。具体某次 Release 的设备侧导入步骤，以对应 release-import SOP 为准；当前 2026-09-10 的 972-note Release 见：

```text
docs/ANKI_CURRENT_RELEASE_IMPORT.md
```

## 1. 发布文件与真源边界

```text
anki/klose/publish/study.csv
```

是 Released Set 的内部标准快照，用于构建、审计、diff、release 对账，不直接给 Anki 使用。

```text
anki/klose/publish/anki-import.csv
```

是面向 Anki 的唯一正式发布产物。它由 `study.csv` 自动生成，数据必须完全一致，只额外带 Anki `#...` file headers。

禁止手工编辑二者；任何问题必须回到 Source / Identity / Learner / Admission / Review / Release 上游处理。

职责边界：

```text
GitHub = Source / Identity / Learner Presentation / Learning Admission /
         LearningOrder / Review / Release

Anki   = Review History / FSRS memory state / Due / Interval /
         New Card Position / Card State
```

特别区分：

```text
LearningOrder     = GitHub curriculum/admission 真源
New Card Position = Anki 尚未学习 New Card 的物理排序状态
```

`LearningOrder` 固定使用 6 位十进制零填充字符串 `000001..999999`。一旦 Card 进入真实 Learning / Review，不使用 LearningOrder 重写其 FSRS / Due。

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

GitHub Release 完成与 Anki Updated 是两个独立状态。只有真实 Anki import/sync 被观察并验收后，才能记录 `Anki Updated=true`。

## 3. 什么变化会触发 review / sync

以下变化通过上游修改、重新构建、审校后导入最新版 `anki-import.csv`：

- 新教材或新来源；
- 新 learning unit / NoteID；
- provenance 更新；
- Word / IPA / Meaning 修正；
- LearnerLevel、ExampleSentence、ExampleTranslation 变化；
- 非空 `PromptHint` 新增/修改；
- Learning Admission / LearningOrder / system-managed Tags 变化；
- Release scope 变化。

`PromptHint` 属于 Learner Presentation；普通 Notes 留空，只有真实 target-sense 歧义时使用最小提示。

`LearningOrder` 属于 Admission metadata，不进入 learner-content fingerprint；调整学习顺序不触发内容 re-review，但必须通过 Admission / Release Gate。

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

当前 fingerprint 绑定 Word / Sense / IPA / Meaning / Example / Translation / LearnerLevel，以及非空 PromptHint。

内容变化后：

```text
sync review registry
→ changed Note = pending
→ explicit review / approval
→ pending = 0
```

空 `PromptHint` 不改变历史 v2 hash；非空 PromptHint 会使对应 Note 重新 pending。`LearningOrder` 不属于内容 fingerprint。

### Step 3：重新构建

正常 CI 包括：

```text
check persistent state
→ build vocabulary
→ actual-source overlays
→ materialize Release truth
→ build Learning Admission + LearningOrder
→ learner presentation overlays
→ PromptHint overlay
→ sync review registry
→ learner checks
→ release gate
```

最终必须通过：

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
allowed LearningOrder == exact curriculum order + fixed six-digit format
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

`NoteID` 必须为第一字段；`UserMemo` 只在 Anki 本地维护，不从 repo CSV 覆盖。

`PromptHint` / `LearningOrder` 都是在现有 Note Type 上原地增加，不新建第二套 Note Type、不删除/重建 Cards。一次性 schema migration 见：

```text
docs/ANKI_PROMPTHINT_MIGRATION.md
docs/ANKI_LEARNING_ORDER_MIGRATION.md
```

这些 migration 文档中的固定计数只描述它们创建时的历史 release snapshot，不能作为未来同步的当前计数真源。

### Step 6：导入 Anki

始终导入：

```text
anki/klose/publish/anki-import.csv
```

长期保持：

```text
Note Type       = Klose Vocabulary
Deck            = Klose-English::Vocabulary
Existing Notes  = Update
Match scope     = Note Type
Identity        = NoteID
Tags            = repo Tags
UserMemo        = 不映射
```

Stable NoteID 已存在时更新原 Note；新 NoteID 创建新 Note。已有 Card 的 FSRS / Review History / Due / Interval 不应因内容更新而重建。

### Step 7：Learning Admission → Card suspension

学习准入由 repo 中 `Learning Admission` 和 system-managed `learning::...` tags 表达，不由 FirstGrade / SourceGrade 决定。

必须区分两个生命周期：

```text
尚未产生任何真实 Review History的初始化窗口
vs.
已经开始真实学习的长期运行状态
```

仅在确认目标 Collection 尚未开始真实学习时，才允许把全部 Cards 的 suspension 一次性重置为当前 Admission truth。

一旦已经存在真实 Learning / Review：

```text
allowed + is:new  -> 可进入 New queue
held    + is:new  -> 保持 suspended
Learning / Review -> 不因 curriculum/source release 批量改 suspension / Due
```

也就是说，长期同步只 materialize **未来尚未学习 Cards 的准入**；已经形成的 Anki memory state 不由 GitHub 回滚。

当前具体 tags / counts 必须从最新 `learning_admission.csv`、`build_stats.csv` 和 release-import SOP 读取，不在长期 SOP 中写死历史数字。

### Step 8：LearningOrder → New Card Position

仅对仍为 `is:new`、当前 `allowed`、且未 suspended 的 Cards执行。

操作逻辑：

```text
按 LearningOrder 升序
→ Cards / Reposition
→ Start=1
→ Step=1
→ Randomize=OFF
→ Shift existing=ON
```

如果已有部分 current Cards 已进入 Learning / Review，则可 reposition 的 New Card 数量会小于 repo 的 total allowed count；这是正常状态。禁止为了匹配一个固定数字而重排已学习 Cards。

### Step 9：设备同步与验收

Desktop 导入后：

```text
Desktop -> Sync -> AnkiWeb
AnkiMobile/iPad -> Sync
```

至少抽查：

```text
旧 NoteID 原地更新
旧 Card Reviews / Due / Interval 保留
新 NoteID 正常新增
Note Type / Card Type 没有复制分叉
UserMemo 保留
当前 New Cards 的 admission/order 正确
```

CSV import 不应改变 deck 的 FSRS 参数或 daily new-card limit。

## 5. 典型场景

### 新增教材版本

```text
new source evidence
→ source identity matching
→ same sense reuse Stable NoteID
→ new sense/new unit append NoteID
→ learner presentation / admission / order / review
→ rebuild / release
→ import same Note Type
```

### 扩大 current learning scope

```text
new source / explicit admission
→ define LearningOrder
→ learner presentation at current LearnerLevel
→ review
→ release
→ import
→ only newly admitted is:new Cards enter future New queue
```

不要因为 Source Grade 更高就自动提高 LearnerLevel。

### 升级旧 Note 的 learner presentation

```text
NoteID 不变
→ Example / PromptHint / LearnerLevel 等变化
→ fingerprint 变化
→ explicit re-review
→ rebuild / release / import
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
Vocabulary Identity   -> Stable NoteID
Curriculum sequencing -> LearningOrder in GitHub
Anki memory state      -> FSRS / Due / New # / Review History in Anki
Anki 学习入口          -> 一个主 Deck
Anki Note Type         -> 同一个 Klose Vocabulary 原地演进
Anki 同步入口          -> anki-import.csv
```

核心原则：修改发生在上游；publish 是确定性生成物；GitHub 保存教学意图，Anki 保存真实记忆状态；Note Type schema migration 只做原地扩展，不重建 identity/card history。
