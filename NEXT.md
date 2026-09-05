# NEXT — Klose Learning

Last updated: 2026-09-05

启动顺序：

```text
AGENTS.md
→ NEXT.md
→ docs/ANKI_PROMPTHINT_MIGRATION.md
→ docs/ANKI_SYNC_WORKFLOW.md
→ anki/klose/anki/README.md
```

## Current objective

真实 Grade-4 Vocabulary 的 Source / Identity / Learner Presentation / Learning Admission / Content Review / Release 已完成。

当前唯一主任务：

```text
PromptHint schema migration
→ latest anki-import.csv
→ existing Klose Vocabulary Note Type in-place update
→ total 638 Cards
→ only learning::klose::grade4 unsuspended (221)
→ Klose starts formal study
```

`Source Grade ≠ LearnerLevel ≠ Learning Admission`；Klose 当前 `LearnerLevel=4`。

---

## 1. Fixed scope numbers

仓库正式 long-lived release：

```text
inventory Notes           = 901
released / study          = 638
actual Grade-4 allowed    = 221
held library              = 417
```

真实 Grade-4：

```text
221 textbook occurrences
219 unique surface strings
221 target learning units / Stable NoteIDs
```

`219 surface -> 221 learning units` 来自同词异义：

```text
cook  noun / verb
over  location / finished
```

221 current Notes 与原 518 baseline：

```text
101 already in old 518 release
120 release additions
  99 new Stable NoteIDs
  21 existing Master identities newly released
```

当前学习 Tag：

```text
learning::klose::grade4
```

---

## 2. Grade-4 source / identity / admission — completed

权威 source：

```text
anki/klose/source_reference/rj_start1-grade4-klose-actual.csv
SourceID      = rj_start1
SourceEdition = klose-current
```

教材 occurrence → Stable NoteID：

```text
anki/klose/master/source_identity_extensions.csv
221 confirmed mappings
```

Identity：

```text
reuse existing = 122
new NoteID      = 99
unresolved      = 0
```

关键同词异义：

```text
KV000424 cook  厨师
KV000805 cook  烹饪；煮
KV000816 over  在……远端/对面
KV000863 over  结束（的）
```

Learning Admission：

```text
allowed = 221 -> stage::grade4-current + learning::klose::grade4
held    = 417 -> stage::library, no learning::* tag
```

Source reconciliation upper/lower 均为：

```text
reconciled / confirmed / confirmed / allowed
```

---

## 3. Content review / release — completed

最终 Grade-4 release review：

```text
review scope      = 638
model-reviewed    = 638
pending           = 0
unresolved queues = 0
```

主要 approval manifests：

```text
grade4-baseline-v2-revalidated.csv
grade4-current-v2-model-reviewed.csv
grade4-current-v2-model-reviewed-r2.csv
```

正式 release 在 PromptHint migration 前已经通过：

```text
study.csv       = 638
anki-import.csv = 638
Release Gate    = PASS
```

CI release commit：

```text
fbcf3b2  data: rebuild Klose vocabulary base
```

Held technical debt：

```text
99 held Notes missing British/American IPA
```

它们当前不 admission；未来任何一个被开放学习前必须先补 IPA + re-review。

---

## 4. PromptHint migration — implementation validated

原因：Recognition front 原先只有 `Word`，active set 中 `cook / over` 无法唯一确定 target sense。

最小提示：

```text
KV000424 cook  -> n.
KV000805 cook  -> v.
KV000816 over  -> 位置
KV000863 over  -> 结束
```

其他 Notes：

```text
PromptHint = blank
```

实现层级：

```text
Learner Presentation
```

不修改 Source / Identity / Stable NoteID / Card identity / FSRS。

主要文件：

```text
anki/klose/learner/prompt_hint_overrides.csv
tools/apply_klose_prompt_hints.py
tools/klose_review_fingerprint.py
anki/klose/anki/card_front.html
anki/klose/anki/styling.css
```

Note Type 新字段顺序见：

```text
anki/klose/anki/README.md
```

当前 PR：

```text
#3  Klose: add PromptHint homograph migration
branch = klose-prompthint-migration-20260905
```

PR CI run 68 已完整 PASS，关键实测：

```text
PromptHint nonempty       = 4
review invalidated        = 4
review pending after sync = 4
explicit approval         -> pending 0
current learning          = 221
held                      = 417
study                     = 638
anki-import               = 638
Release Gate              = PASS
```

Fingerprint compatibility：

```text
PromptHint blank    -> existing v2 hash unchanged
PromptHint nonempty -> extends fingerprint; only changed Notes re-review
```

一次性 migration approval batch 名称：

```text
grade4-prompthint-v1.csv
```

该 manifest 会在合并到 main 后由 release build 持久化；随后必须把一次性自动 approval step 从日常 CI 移除。

---

## 5. Next work order

### Step 1 — merge PromptHint PR and materialize main release

```text
merge PR #3
→ main CI
→ PromptHint overlay
→ exactly 4 fingerprint invalidations
→ explicit migration approval
→ Release Gate PASS
→ commit updated learner/publish + grade4-prompthint-v1.csv
```

然后删除日常 CI 中的一次性 PromptHint auto-approval step，并再次验证正常 CI 独立 PASS。

### Step 2 — Anki Desktop Note Type in-place migration

严格按：

```text
docs/ANKI_PROMPTHINT_MIGRATION.md
```

在现有 `Klose Vocabulary` Note Type 中：

```text
add PromptHint field after Word
update Recognition front template
update Styling
keep Back / Card Type / NoteID / FSRS identity
```

不得创建第二套 Note Type 或 Cards。

### Step 3 — import latest release

```text
Import: anki/klose/publish/anki-import.csv
Existing Notes = Update
Identity = NoteID
Expected total = 638
```

### Step 4 — reset current active learning set

Klose 尚无真实 Review History，因此本次可做一次初始 reset：

```text
Suspend all 638
→ search tag:learning::klose::grade4
→ must equal 221
→ Unsuspend those 221
```

最终：

```text
Unsuspended current = 221
Suspended held      = 417
```

---

## 6. Current physical Anki state — not updated yet

设备目前仍是旧 release：

```text
Deck              = Klose-English::Vocabulary
Note Type         = Klose Vocabulary
Card Type         = Recognition
Cards             = 518
Suspended         = 343
Unsuspended       = 175
New/day           = 8
FSRS              = ON
Desired retention = 90%
```

仓库升级完成 ≠ Anki 已更新。只有 Desktop 实际完成 Note Type migration + import + 221/417 Suspend 校验后，才进入 `Anki Updated`。

---

## Deferred

- 四下 Useful Expressions：Vocabulary Grade-4 正式启用后再处理。
- 99 个 held legacy IPA debt：对应 Note 未来 admission 前补齐并 re-review。
