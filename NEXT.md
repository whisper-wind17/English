# NEXT — Klose Learning

Last updated: 2026-09-05

启动顺序：

```text
AGENTS.md
→ NEXT.md
→ docs/ANKI_SYNC_WORKFLOW.md
→ docs/ANKI_PROMPTHINT_MIGRATION.md
→ anki/klose/anki/README.md
```

## Current status

**Grade-4 Vocabulary 已完成从真实教材到 Anki 的正式闭环，并已在现有 Desktop collection 中启用。**

```text
Source / Identity / Learner Presentation / Learning Admission
→ Content Review / Release Gate
→ PromptHint Note Type migration
→ NoteID-first in-place import
→ active-set reset
→ Desktop validation
```

当前四个执行状态：

```text
Build Valid        = yes
Content Releasable = yes
Anki Updated       = yes
Learning Admitted  = yes
```

Klose 当前 `LearnerLevel=4`。继续保持：

```text
Source Grade ≠ LearnerLevel ≠ Learning Admission
```

---

## 1. Current operational baseline

Repo：

```text
inventory Notes           = 901
released / study          = 638
actual Grade-4 allowed    = 221
held library              = 417
model-reviewed            = 638
review pending            = 0
unresolved review queues  = 0
Release Gate              = PASS
```

Anki Desktop 已实测：

```text
Deck              = Klose-English::Vocabulary
Note Type         = Klose Vocabulary
Card Type         = Recognition
Total Notes/Cards = 638
Unsuspended       = 221
Suspended         = 417
FSRS              = ON
Desired retention = 90%
New/day           = 8
```

正式导入结果：

```text
638 notes found in file
120 new notes imported
518 existing notes updated in place
```

因此原 518 Notes 没有复制成第二套 Cards；Stable NoteID / existing Card identity 得以保留。

当前 active set 唯一由：

```text
learning::klose::grade4
```

控制。

---

## 2. Actual Grade-4 source / identity — completed

权威 source：

```text
anki/klose/source_reference/rj_start1-grade4-klose-actual.csv
SourceID      = rj_start1
SourceEdition = klose-current
```

规模：

```text
221 textbook occurrences
219 unique surface strings
221 target learning units / Stable NoteIDs
```

教材 occurrence → NoteID：

```text
anki/klose/master/source_identity_extensions.csv
221 confirmed mappings
```

Identity summary：

```text
reuse existing = 122
new NoteID      = 99
unresolved      = 0
```

关键同词异义：

```text
KV000424  cook  厨师
KV000805  cook  烹饪；煮
KV000816  over  在……远端/对面
KV000863  over  结束（的）
```

Source reconciliation 上/下册均：

```text
reconciled / confirmed / confirmed / allowed
```

---

## 3. PromptHint migration — completed and validated

`PromptHint` 已成为 `Klose Vocabulary` Note Type 的长期可选字段，位置在 `Word` 后。

只有 4 个当前 active homograph Notes 非空：

```text
KV000424  cook  -> n.
KV000805  cook  -> v.
KV000816  over  -> 位置
KV000863  over  -> 结束
```

Desktop Preview 已实测：

```text
cook / n.       correct
cook / v.       correct
over / 位置      correct
over / 结束      correct
```

Recognition front：

```text
Word + optional PromptHint
```

Back：

```text
FrontSide
+ Word TTS
+ British / American IPA
+ Meaning
+ Example
+ Translation
```

Back Preview 的 Word TTS 已实测正常。

PromptHint 属于 Learner Presentation，不改变 Source / Identity / Stable NoteID / Card identity / FSRS。

正式 PromptHint approval：

```text
anki/klose/learner/review_approvals/grade4-prompthint-v1.csv
```

日常 CI 已移除一次性 auto-approval；后续任何 PromptHint / content 改动都会重新进入 `pending`。

---

## 4. Learning Admission — live in Anki

Repo 定义：

```text
allowed = 221 -> stage::grade4-current + learning::klose::grade4
held    = 417 -> stage::library, no learning::* tag
```

Desktop 已完成一次初始化 reset：

```text
Suspend all 638
→ Unsuspend tag:learning::klose::grade4
```

最终实测：

```text
Total        = 638
Unsuspended  = 221
Suspended    = 417
```

从现在起 Klose 进入真实 Review History 后，**不要因为 Source Grade / 教材 scope 的变化批量重新 Suspend 已经进入 Learning/Review 的 Cards**。FSRS / Due / Interval / Review History 由 Anki 持续维护。

---

## 5. Long-term sync contract

以后内容更新统一按：

```text
upstream source / identity / learner / admission changes
→ review fingerprint invalidation
→ explicit review / approval
→ Release Gate PASS
→ regenerate anki/klose/publish/anki-import.csv
→ import into same Klose Vocabulary Note Type
→ Existing Notes = Update by NoteID
```

正式 Anki artifact 永远是：

```text
anki/klose/publish/anki-import.csv
```

不要直接导入：

```text
publish/study.csv
publish/all.csv
```

也不要新建第二套长期 Vocabulary Note Type / Deck 来承载后续教材。

---

## 6. Next decision point

Grade-4 Vocabulary 数据工程与 Anki 启用阶段已经结束。下一阶段不要立即扩 schema，优先从真实学习反馈驱动。

建议顺序：

```text
1. Klose 开始真实 Grade-4 Vocabulary 学习
2. 观察首批真实 Review History / 易错词 / 例句理解情况
3. 再决定 learner presentation 是否需要微调
4. Vocabulary 稳定后继续四下 Useful Expressions
```

如果下一任务直接进入四下 Expressions，启动时读取：

```text
docs/EXPRESSIONS_SYSTEM.md
anki/klose/source_reference/rj_start1-grade4-lower-klose-expressions.csv
```

如果下一任务是复盘 Klose 的学习状态，以 **Anki 实际 FSRS / Review History** 为真源，不从 GitHub 推测学习表现。

---

## Deferred / technical debt

- 四下 Useful Expressions：Vocabulary Grade-4 已正式启用后可开始处理。
- 99 个 held legacy Notes 缺 British/American IPA：未来对应 Note 被 admission 前补齐并重新 review；当前 417 held 不阻塞学习。
- AnkiWeb / iPad 同步属于 Anki 设备状态；若尚未完成，在 Desktop 当前正确 collection 上执行同步后再让其他设备拉取，不通过 repo 重建学习状态。
