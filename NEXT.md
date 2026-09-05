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

以 Klose 实际四年级上 + 下教材作为当前 Grade 4 权威学习范围，并在不破坏现有 Anki NoteID / FSRS 状态的前提下完成正式发布：

```text
Actual Grade 4 source
→ Stable NoteID
→ long-lived study
→ explicit Learning Admission
→ learning::klose::grade4
→ Anki only unsuspends this learning set
```

`Source Grade ≠ LearnerLevel ≠ Learning Admission`。Klose 当前仍为 `LearnerLevel=4`。

---

## 1. Current numbers — do not confuse these scopes

当前 Anki 设备中实际已经导入：

```text
518 Cards / Notes
```

仓库中合并真实四年级之后，下一版长期 study 目标为：

```text
638 Notes
```

`638` 不是“真实四年级单词数”，而是长期 Vocabulary study library：

```text
518  existing released baseline
+120 actual-Grade4 release additions
=638 long-lived study Notes
```

真实四年级当前学习范围本身是：

```text
221 textbook occurrences
219 unique surface strings
221 target learning units / Stable NoteIDs
```

之所以 `219 surface strings -> 221 learning units`，是因为：

```text
cook  有 noun / verb 两个 target sense
over  有 location / finished 两个 target sense
```

221 个真实四年级 NoteID 与当前 518 baseline 的关系：

```text
101  already included in the existing 518 released baseline
120  need to be added to the released study set
---
221  actual Grade-4 current learning set
```

这 120 个新增到 study 的 Note 包括：

```text
99  genuinely new Stable NoteIDs
21  existing Master identities that were not previously released
---
120 release additions
```

因此下一次正式 Anki 原地导入之后，预期是：

```text
Anki total Cards / Notes = 638
Current Grade-4 learning = 221  -> Unsuspend
Held library             = 417  -> Suspend
```

当前学习 Tag 固定：

```text
learning::klose::grade4
```

---

## 2. Actual Grade 4 source — confirmed

权威合并表：

```text
anki/klose/source_reference/rj_start1-grade4-klose-actual.csv
SourceID      = rj_start1
SourceEdition = klose-current
221 occurrence rows
219 unique surface strings
```

用户已确认该文件内容。

---

## 3. Grade 4 identity — completed

221 条教材 occurrence 已全部得到 confirmed Stable NoteID：

```text
221 occurrences
221 target learning units / NoteIDs

reuse existing identity = 122
new NoteID              = 99
  new learning unit     = 90
  distinct sense        = 9
```

已明确拆分的同词异义包括：

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

其他 distinct-sense actual Grade-4 identity 包括：

```text
kind = 友好的       -> KV000810
free = 免费的       -> KV000876
can  = 金属罐       -> KV000885
milk = 挤奶         -> KV000890
```

单复数 / 词形差异不制造额外 identity：

```text
child / children
sock / socks
glove / gloves
shoe / shoes
chopstick / chopsticks
```

这些复用同一 Stable NoteID，但 Klose 当前 learner presentation 按真实教材词形呈现。

为保护已有 identity，不重写 legacy `note_registry.csv`；新增身份保存在：

```text
anki/klose/master/note_registry_extensions.csv
```

教材 occurrence → NoteID 真源：

```text
anki/klose/master/source_identity_extensions.csv
221 confirmed mappings
```

CI identity / reuse checks：

```text
tools/check_klose_actual_grade4_identity.py
tools/audit_klose_actual_grade4_reuse.py
```

---

## 4. Long-lived study + Learning Admission — structure completed

旧 released baseline 保留 518 Notes，不删除、不重编号。

真实 Grade 4 增加：

```text
21  existing Master Notes not previously released
99  new Stable NoteIDs
---
120 release extensions
```

持久化在：

```text
anki/klose/master/release_registry_extensions.csv
```

当前 build state：

```text
inventory_notes             = 901
released_notes              = 638
actual_grade4_notes         = 221
actual_grade4_new_notes     = 99
actual_grade4_release_ext   = 120

learning_admission_mode     = explicit
learning_admission_allowed  = 221
learning_admission_held     = 417
stage::grade4-current       = 221
stage::library              = 417
```

因此：

```text
study.csv = 638 long-lived Notes
current learning set = 221 Notes
```

`study != current learning set`。

真实教材通过薄 overlay 叠加，不重写第三方 adapter：

```text
tools/build_klose_vocabulary.py
→ tools/apply_klose_actual_grade4.py
→ reused fact / learner presentation overlays
→ tools/build_klose_learning_admission.py
→ tools/apply_klose_learner_overrides.py
```

---

## 5. Current blocker — fingerprint-v2 explicit review

Source / Evidence / Identity 已完成；per-Note Learning Admission 也已经显式建立为 `221 allowed / 417 held`。

当前真正 blocker 是 Review Registry：

```text
learner_review_registry_current = 638
learner_model_reviewed_current  = 0
learner_human_reviewed_current  = 0
learner_review_pending_current  = 638
```

当前普通 review queues 已为空：

```text
identity_review_items       = 0
learner_review_suggestions  = 0
```

638 pending 的原因不是“638 个词都需要重新生成”，而是 fingerprint v2 绑定了当前 release-visible Word / Sense / IPA / Meaning / Example / Translation / LearnerLevel；旧 baseline approval 不能静默继承。

Source-level reconciliation registry 当前仍保持最终 release switch：

```text
ReconciliationStatus = reconciled
EvidenceStatus        = confirmed
IdentityStatus        = confirmed
LearningAdmission     = blocked
```

在 fingerprint-v2 review 完成前，不把该 source-level switch 改为 `allowed`。

---

## 6. Next work order

1. 对 638 released Notes 做 fingerprint-v2 分层审校，而不是重新生成全部内容：

```text
High-risk review:
- 99 actual Grade-4 new NoteIDs
- actual Grade-4 reused presentation overrides
- cook / over / fan / speak 等 sense-sensitive items

Baseline re-validation:
- 原 518 baseline 中未发生内容变化的 Notes
- 检查新增 fingerprint 字段后重新确认，不无意义重写稳定内容
```

2. 目标 review state：

```text
learner_review_registry_current = 638
learner_model_reviewed_current  = 638
learner_review_pending_current  = 0
```

3. 使用显式审批工具生成新的不可覆盖 approval manifest：

```text
tools/approve_klose_learner_review.py
```

不得手工把 pending 改成 model-reviewed。

4. Review 全部 current 后，将：

```text
anki/klose/master/source_reconciliation_registry.csv
LearningAdmission = allowed
```

5. 跑完整 release gate，要求至少满足：

```text
inventory             = 901
study                  = 638
actual Grade-4 allowed = 221
held                   = 417
pending review         = 0
release gate           = PASS
```

6. 单独完成 homograph PromptHint Note Type migration，再正式让 Klose 开始学习：

```text
cook [n.] / cook [v.]
over [位置] / over [结束]
```

该 migration 不改变 Stable NoteID / Card / FSRS history。

7. Anki 正式原地导入：

```text
Import publish/anki-import.csv
Update Existing Notes using NoteID
Total expected cards = 638
Suspend all baseline/library cards
Unsuspend only tag:learning::klose::grade4
Expected unsuspended current learning set = 221
```

---

## 7. Current Anki state

当前设备上仍然是旧 baseline，尚未导入 120 个 Grade-4 release additions：

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

Klose 尚未产生真实 Review History，因此当前仍是调整 learning set 的低风险窗口。

---

## Deferred

四下 Useful Expressions 暂不处理，先完成 Vocabulary Grade-4 learning set 的 review / release / Anki migration。
