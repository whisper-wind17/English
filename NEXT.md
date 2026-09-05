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

repo 侧 Grade-4 Vocabulary 已全部完成。当前唯一主任务是 **在现有 Anki Desktop collection 中原地完成 Note Type / release / active-set 迁移**：

```text
add PromptHint to existing Klose Vocabulary Note Type
→ update Recognition template/styling
→ import latest anki-import.csv by NoteID
→ total 638 Cards
→ Suspend all
→ Unsuspend only learning::klose::grade4 (221)
→ Klose starts formal study
```

不要创建第二套 Note Type / Card Type，不删除现有 Notes，不改变 Stable NoteID，不重建 FSRS state。

---

## 1. Repo release — completed

当前正式状态：

```text
inventory Notes           = 901
released / study          = 638
actual Grade-4 allowed    = 221
held library              = 417
LearnerLevel              = 4
review model-reviewed     = 638
review pending            = 0
unresolved review queues  = 0
Release Gate              = PASS
```

真实 Grade-4：

```text
221 textbook occurrences
219 unique surface strings
221 Stable NoteIDs
```

当前 learning tag：

```text
learning::klose::grade4
```

221 allowed Notes 必须带：

```text
stage::grade4-current
learning::klose::grade4
```

417 held Notes：

```text
stage::library
no learning::* tag
```

正式 Anki artifact：

```text
anki/klose/publish/anki-import.csv
```

当前 header：

```text
NoteID,CanonicalWord,Word,PromptHint,British,American,MeaningPrimary,
ExampleSentence,ExampleTranslation,LearnerLevel,Sources,SourceBooks,Tags
```

不要直接导入 `study.csv`。

---

## 2. PromptHint migration — completed in repo

PromptHint 是 Learner Presentation，不属于 Source / Identity。

只有 4 个 active homograph Notes 非空：

```text
KV000424  cook  -> n.
KV000805  cook  -> v.
KV000816  over  -> 位置
KV000863  over  -> 结束
```

其他 Notes：

```text
PromptHint = blank
```

实现：

```text
anki/klose/learner/prompt_hint_overrides.csv
tools/apply_klose_prompt_hints.py
tools/klose_review_fingerprint.py
anki/klose/anki/card_front.html
anki/klose/anki/styling.css
```

Review compatibility：

```text
blank PromptHint    -> old fingerprint-v2 hash unchanged
non-empty PromptHint -> fingerprint extended, requires re-review
```

本次实测：

```text
PromptHint nonempty = 4
review invalidated  = 4
explicitly reviewed = 4 changed Notes
final pending       = 0
```

最终 immutable approval：

```text
anki/klose/learner/review_approvals/grade4-prompthint-v1.csv
```

PR #3 已合并：

```text
2372d4f  Klose: add PromptHint homograph migration
```

正式 PromptHint release：

```text
6e6041e  data: rebuild Klose vocabulary base
```

一次性 auto-approval 已从日常 CI 删除：

```text
f4cff202  ci: remove one-time PromptHint approval
```

清理后的正常 CI run 77 独立验证：

```text
review registry = 638 model / 0 pending
prompt_hints    = 4
study           = 638
anki_import     = 638
Release Gate    = PASS
no generated changes
```

因此后续任何 PromptHint / content 变化都会重新 pending，不会被 CI 自动批准。

---

## 3. Stable identity / source state — completed

权威 Grade-4 source：

```text
anki/klose/source_reference/rj_start1-grade4-klose-actual.csv
SourceID      = rj_start1
SourceEdition = klose-current
```

221 occurrence → NoteID mappings：

```text
anki/klose/master/source_identity_extensions.csv
status = confirmed
```

Identity：

```text
reuse existing = 122
new NoteID      = 99
unresolved      = 0
```

Source reconciliation 上/下册均：

```text
reconciled / confirmed / confirmed / allowed
```

---

## 4. Next action — Anki Desktop

严格按：

```text
docs/ANKI_PROMPTHINT_MIGRATION.md
```

### A. Existing Note Type schema

在现有 `Klose Vocabulary` 中增加 `PromptHint`，放在 Word 后：

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
11 Sources
12 SourceBooks
13 UserMemo
```

Card Type 仍只有：

```text
Recognition
```

更新 Front / Styling 使用：

```text
anki/klose/anki/card_front.html
anki/klose/anki/styling.css
```

Back 不新增 Card Type。

### B. Import latest release

```text
Import file     = anki/klose/publish/anki-import.csv
Note Type       = Klose Vocabulary
Existing Notes  = Update
Identity        = NoteID
Expected total  = 638 Notes / 638 Cards
```

原 518 Notes 应原地更新；120 个新 released NoteID 新增。

### C. Verify PromptHint

```text
KV000424 = n.
KV000805 = v.
KV000816 = 位置
KV000863 = 结束
```

普通 Note 的 PromptHint 应为空。

### D. Reset active set

Klose 尚未产生真实 Review History，因此本次可以做一次初始化 reset：

```text
Suspend all 638
→ search tag:learning::klose::grade4
→ result MUST = 221
→ Unsuspend these 221
```

验收：

```text
Total        = 638
Unsuspended  = 221
Suspended    = 417
```

如果 tag 搜索不是 221，停止学习并排查 import / Tags，不要手工凑数量。

---

## 5. Current physical Anki state — still old

设备尚未执行上述操作，目前仍是：

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

repo 完成 ≠ Anki Updated。完成 Desktop migration + import + `221 / 417` 校验后，才允许 Klose 正式开始学习。

---

## Deferred

- 四下 Useful Expressions：Vocabulary Grade-4 正式启用后再处理。
- 99 个 held legacy Notes 缺 British/American IPA：未来 admission 前补齐并重新 review。
