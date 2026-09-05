# NEXT — Klose Learning

Last updated: 2026-09-05

启动顺序：

```text
AGENTS.md
→ NEXT.md
→ anki/klose/source_reference/README.md
→ anki/klose/source_reference/rj_start1-grade4-klose-actual.csv
```

## Current objective

真实 Grade 4 Vocabulary 的 Source / Identity / Learner Presentation / Learning Admission / Review / Release 已完成。

当前主任务已经切换为：

```text
final released anki-import.csv
→ 必要的 homograph PromptHint migration
→ Anki 原地 Update Existing Notes
→ 全部 library Suspend
→ 仅 Unsuspend learning::klose::grade4
→ Klose 正式开始学习
```

`Source Grade ≠ LearnerLevel ≠ Learning Admission`。Klose 当前仍为 `LearnerLevel=4`。

---

## 1. Scope numbers — fixed definitions

当前 Anki 设备中实际已导入：

```text
518 Cards / Notes
```

仓库当前正式 long-lived study release：

```text
638 Notes
```

关系：

```text
518  existing released baseline
+120 actual-Grade4 release additions
=638 long-lived study Notes
```

真实 Grade 4 当前学习范围：

```text
221 textbook occurrences
219 unique surface strings
221 target learning units / Stable NoteIDs
```

221 个当前学习 Note 与原 518 的关系：

```text
101  already in the original 518 release
120  newly added to released study
---
221  actual Grade-4 current learning set
```

120 个 release additions：

```text
99  new Stable NoteIDs
21  existing Master identities not previously released
---
120
```

正式导入后的预期 Anki 状态：

```text
Total Notes / Cards      = 638
Current Grade-4 allowed  = 221  -> Unsuspend
Held library             = 417  -> Suspend
```

当前学习 Tag：

```text
learning::klose::grade4
```

---

## 2. Actual Grade 4 source — confirmed

权威教材输入：

```text
anki/klose/source_reference/rj_start1-grade4-klose-actual.csv
SourceID      = rj_start1
SourceEdition = klose-current
221 occurrence rows
219 unique surface strings
```

用户已确认该文件。

---

## 3. Identity — completed

全部 221 个教材 occurrence 已有 confirmed Stable NoteID：

```text
reuse existing identity = 122
new Stable NoteID       = 99
  new learning unit     = 90
  distinct sense        = 9
```

关键同词异义：

```text
cook
  noun 厨师       -> KV000424
  verb 烹饪；煮   -> KV000805

over
  在……远端/对面   -> KV000816
  结束（的）      -> KV000863

fan
  legacy hand-fan sense 保留旧 identity
  风扇             -> KV000900

speak
  legacy language sense 保留旧 identity
  说话；发言        -> KV000901
```

单复数 / morphology 不额外制造 identity：

```text
child / children
sock / socks
glove / gloves
shoe / shoes
chopstick / chopsticks
```

教材 occurrence → NoteID 真源：

```text
anki/klose/master/source_identity_extensions.csv
221 confirmed mappings
```

CI：

```text
tools/check_klose_actual_grade4_identity.py
tools/audit_klose_actual_grade4_reuse.py
```

当前 reuse audit：

```text
unresolved = 0
```

---

## 4. Learning Admission — completed

当前显式 admission：

```text
released_notes              = 638
learning_admission_allowed  = 221
learning_admission_held     = 417
stage::grade4-current       = 221
stage::library              = 417
```

Source-level reconciliation：

```text
4年级上: reconciled / confirmed / confirmed / allowed
4年级下: reconciled / confirmed / confirmed / allowed
```

真实 Grade 4 的 221 Notes 必须且只允许带：

```text
learning::klose::grade4
stage::grade4-current
```

417 held Notes：

```text
stage::library
无 learning::* tag
```

---

## 5. Content review / fingerprint v2 — completed

review scope 最终为 638 released Notes。

处理过程：

```text
511  unchanged baseline fingerprints -> explicit v2 re-validation
127  changed / new / high-risk fingerprints -> explicit model review
```

127 条审校中修正了 7 个内容问题，包括：

```text
make the bed / a lot of      missing IPA
fly                           target-sense example
hard                          translation precision
pair                          example aligned to textbook sense
any                           example aligned to 任一/任何
food                          simpler aligned example/translation
```

随后 release completeness 又发现 3 个当前 Grade-4 reused phrases 缺 IPA，并已补齐：

```text
KV000192  go to school
KV000194  go home
KV000196  go to bed
```

这 3 个 fingerprint 变化后再次显式 model review，最终 approval manifest：

```text
anki/klose/learner/review_approvals/grade4-current-v2-model-reviewed-r2.csv
```

最终状态：

```text
learner_review_registry_current = 638
learner_model_reviewed_current  = 638
learner_human_reviewed_current  = 0
learner_review_pending_current  = 0

identity_review.csv      = 0
learner_review.csv       = 0
future_vocab_review.csv  = 0
```

正常 CI 不自动执行 approval；未来任何 fingerprint 变化应重新进入 pending，必须再次显式 review。

---

## 6. Release — PASS

最终 Release Gate 已通过，CI run 66 / release commit：

```text
fbcf3b2  data: rebuild Klose vocabulary base
```

验收值：

```text
inventory                = 901
released / study         = 638
current learning         = 221
held                     = 417
study.csv                = 638
anki-import.csv          = 638
allowed missing fields  = 0
pending reviews          = 0
unresolved reports       = 0
Release Gate             = PASS
```

正式 Anki 导入文件：

```text
anki/klose/publish/anki-import.csv
```

不要直接导入 `study.csv`。

### Held-library technical debt

旧 baseline 中仍有：

```text
99 held Notes missing British / American IPA
```

这些 Notes 当前全部属于 `held / stage::library`，不会让 Klose 学习，因此不阻塞当前 Grade-4 release。

Gate 规则：

```text
allowed Notes -> 所有 release-visible 字段必须完整
held Notes    -> 结构 / Word / Meaning / Example / Translation 等仍必须完整；
                 legacy British/American IPA 可暂缺
```

未来任何 held Note 被 admission 前，必须先补齐 IPA 并重新 review。

---

## 7. Next work order

### Step 1 — decide / perform PromptHint migration

当前 Grade-4 active set 中真正需要正面消歧的是：

```text
cook [n.] / cook [v.]
over [位置] / over [结束]
```

目前 Anki Note Type `Klose Vocabulary` 的 Recognition front 只有 `{{Word}}`，因此这 4 张卡存在 prompt ambiguity。

建议在正式让 Klose 学习前做一次独立 Note Type migration：

```text
add PromptHint field
→ ordinary Notes: blank
→ homographs: minimal cue
→ front renders Word + optional PromptHint
```

不得改变 Stable NoteID / existing Card / FSRS history。

`fan / speak` 的另一旧义项当前属于 held，因此当前 Grade-4 active set 不形成同时激活的正面歧义；未来若旧义项 admission，再补 PromptHint。

### Step 2 — Anki in-place import

完成 PromptHint 决策后：

```text
Import: anki/klose/publish/anki-import.csv
Note Type: Klose Vocabulary
Update Existing Notes using NoteID
Expected total after import = 638
```

不要删除已有 Notes，不建立第二套 Note Type，不破坏原 Card / FSRS 状态。

### Step 3 — reset active learning set

导入完成后：

```text
1. Suspend 全部 638 Cards
2. 搜索 tag:learning::klose::grade4
3. 应恰好得到 221 Cards
4. Unsuspend 这 221 Cards
5. 417 held library 保持 Suspend
```

然后再让 Klose 正式开始学习。

---

## 8. Current physical Anki state

仓库 release 已经是 638，但设备尚未执行这次正式导入，因此设备当前仍为旧状态：

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

Klose 尚未产生真实 Review History，因此当前仍是完成 Note Type / active-set 调整的低风险窗口。

---

## Deferred

- 四下 Useful Expressions：Vocabulary Grade-4 正式启用后再处理。
- 99 个 held legacy Notes 的 IPA debt：对应 Note 未来 admission 前补齐并重新 review。
