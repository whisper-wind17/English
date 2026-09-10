# Anki 一次性迁移：LearningOrder → New Card Position

> **Historical migration scope.** 本文中的 `638 / 221 / 417` 是 Grade-4 初始迁移时的 snapshot，不是当前 Release 真源。2026-09-10 及之后的同步先读 `docs/ANKI_CURRENT_RELEASE_IMPORT.md`。如果这里只是补 `LearningOrder` 字段，只执行 schema migration；进入真实学习后，只对仍为 `is:new` 的 current allowed Cards 做 Reposition，不要求固定 221 张。

本 SOP 处理当时 Grade-4 Vocabulary 的学习顺序迁移。

目标不是修改 Stable NoteID，也不是让 GitHub 接管 Anki 的 Due / FSRS，而是把 repo 中明确的 curriculum order materialize 为 Anki 的 New Card Position。

## 1. 两种“顺序”必须区分

```text
LearningOrder
= GitHub 中的教学顺序意图
= Learning Admission metadata

New Card Position / New #
= Anki 中当前 New Card 的物理位置
= Anki state
```

`LearningOrder` 的正式序列化固定为 6 位十进制零填充字符串：

```text
000001 .. 999999
```

本文创建时的 Grade-4 snapshot：

```text
allowed Notes  = 221
LearningOrder  = 000001..000221
held Notes     = 417
LearningOrder  = blank
```

这些计数仅用于历史 migration 回放；当前值以 `anki/klose/learner/learning_admission.csv`、`build_stats.csv` 和当前 release-import SOP 为准。

## 2. 为什么不能只保留当前 New #

历史 release 由多次来源演进而来。即使 active Cards 范围正确，原 New # 仍可能继承 Note 创建顺序，而不是教材 curriculum order。

仅在 Anki 手工 Reposition 可以解决一次，但 repo 无法解释或重建教学顺序。因此需要显式 `LearningOrder`。

## 3. Note Type schema migration

在现有：

```text
Klose Vocabulary
```

中增加字段：

```text
LearningOrder
```

放在 `LearnerLevel` 后、`Sources` 前。

最终字段顺序：

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

不要新建 Note Type / Card Type，不修改模板显示，不删除 Notes。

## 4. 导入最新 release

先确认 repo Release Gate PASS，再导入：

```text
anki/klose/publish/anki-import.csv
```

导入：

```text
Note Type       = Klose Vocabulary
Existing Notes  = Update
Match scope     = Note Type
Identity        = NoteID
LearningOrder   -> LearningOrder
UserMemo        -> Nothing / 不映射
```

这次导入只更新 Note 字段，不应改变 Card identity / FSRS / Review History。

当前 Release 的 expected total 和 LearningOrder range 不从本文历史数字推导，必须读取 `docs/ANKI_CURRENT_RELEASE_IMPORT.md`。

## 5. Reposition 前置条件

只对当前仍未进入真实 Review History 的 current allowed New Cards执行排序。

目标集合必须满足：

```text
current Learning Admission = allowed
AND is:new
AND not suspended
```

如果某些 current Cards 已经进入 Learning / Review，它们不再属于本次 Reposition scope；因此目标数量可以小于 repo 的 total allowed count。

禁止为了匹配旧 snapshot 的固定数量而重排已学习 Cards。

## 6. 按 LearningOrder 排序

在 Browser 中显示 `LearningOrder` 列并按升序排序。

由于值固定为 6 位零填充：

```text
000001, 000002, ... 000009, 000010, ...
```

文本排序与数值排序一致。

排序应与当前 repo curriculum truth 相符；不要用 NoteID、SourceGrade 或创建时间代替 LearningOrder。

## 7. Materialize 到 New #

保持目标 New Cards 按 `LearningOrder` 升序显示，全选：

```text
Ctrl+A
-> Cards
-> Reposition
```

设置：

```text
Start position = 1
Step           = 1
Randomize      = OFF
Shift existing = ON
```

这一步只调整 New Card Position。未被选择的 held New Cards 可留在后续位置并保持 suspended；Learning/Review Cards 不受影响。

## 8. 验收

验收不再依赖历史固定 `221` 数量，而验证以下 invariants：

```text
目标集合全部仍为 is:new
目标集合全部属于 current allowed
LearningOrder 非空且严格递增
New # 顺序与 LearningOrder 一致
held New Cards 不进入 current New queue
已有 Learning / Review Cards 的 Due / Interval / Reviews 不变
```

当前 release 的总 Notes/Cards、allowed/held 数量和 LearningOrder max，以最新 `docs/ANKI_CURRENT_RELEASE_IMPORT.md` 为准。

## 9. 长期规则

- 修改词义 / IPA / Example / PromptHint → 需要内容 re-review；
- 修改 LearningOrder → 不需要内容 re-review，但必须通过 Admission / Release Gate；
- LearningOrder 固定为 6 位 `000001..999999`，不得随词库规模改变位宽；
- 已进入真实 Learning / Review 的 Card，不因 curriculum order 变化而重排 FSRS / Due；
- LearningOrder 主要用于尚未学习新卡的 admission 与 sequencing；
- GitHub 保存 curriculum intent，Anki 保存真实 memory state。
