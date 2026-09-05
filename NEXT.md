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

以 Klose 实际四年级上 + 下教材作为当前 Grade 4 权威学习范围：

```text
Actual Grade 4 source
→ Stable NoteID
→ long-lived study
→ learning::klose::grade4
→ Anki only unsuspends this learning set
```

`Source Grade ≠ LearnerLevel ≠ Learning Admission`。Klose 当前仍为 `LearnerLevel=4`。

## Actual Grade 4 source — confirmed

权威合并表：

```text
anki/klose/source_reference/rj_start1-grade4-klose-actual.csv
SourceID      = rj_start1
SourceEdition = klose-current
221 occurrence rows
219 unique surface strings
```

用户已确认该文件内容。

## Grade 4 identity — completed

221 条教材 occurrence 已全部得到 confirmed Stable NoteID：

```text
221 occurrences
221 target learning units / NoteIDs

reuse existing identity        = 124
new NoteID                     = 97
  new learning unit            = 90
  distinct sense               = 7
```

两个教材内重复 surface 已按义项拆分：

```text
cook
  noun 厨师     -> KV000424
  verb 烹饪；煮 -> KV000805

over
  在……远端/对面 -> KV000816
  结束（的）    -> KV000863
```

其他明确 distinct-sense 新 identity：

```text
kind = 友好的       -> KV000810
free = 免费的       -> KV000876
can  = 金属罐       -> KV000885
milk = 挤奶         -> KV000890
```

为保护已有 identity，不重写旧 `note_registry.csv`：

```text
anki/klose/master/note_registry_extensions.csv
KV000803 ... KV000899   # 97 appended NoteIDs
```

教材 occurrence → NoteID 真源：

```text
anki/klose/master/source_identity_extensions.csv
221 confirmed mappings
```

CI 检查：

```text
tools/check_klose_actual_grade4_identity.py
```

会验证真实 Grade 4 每个 occurrence 恰好有一个 confirmed NoteID，且 NoteID 存在。

## Long-lived study merge — structure completed, content pending

旧 released baseline 保留 518 Notes，不删除、不重编号。

真实 Grade 4 需要额外 release：

```text
23  existing Master Notes not previously released
97  new NoteIDs
---
120 release extensions
```

持久化在：

```text
anki/klose/master/release_registry_extensions.csv
```

因此构建完成后的目标长期 study 为：

```text
518 old released Notes
+120 actual-Grade4 extensions
=638 study Notes
```

实际 Grade 4 当前学习集合仍只有 221 Notes；`study != current learning set`。

真实教材通过薄 overlay 叠加，不重写第三方 adapter：

```text
tools/build_klose_vocabulary.py        # legacy inventory
→ tools/apply_klose_actual_grade4.py   # klose-current overlay
```

该 overlay 会：

- 为 reused Notes 增加实际教材 Edition / Book / Unit provenance；
- append 97 个新 Note 到 generated Master / Learner；
- 将 120 个 release extension 并入 released set；
- 将 221 条真实教材 occurrence 写入 source occurrences；
- 对 97 个新 Note 保持 learner content pending，不伪造模板例句。

## Current blocker: learner content

当前 Source / Identity reconciliation 已完成：

```text
ReconciliationStatus = reconciled
EvidenceStatus       = confirmed
IdentityStatus       = confirmed
LearningAdmission    = blocked
```

现在 blocker 已从“教材/identity 不确定”缩小为：

```text
97 new Notes:
- IPA / pronunciation fact 尚未补齐
- LearnerLevel=4 Meaning / Example / Translation 尚未正式生成与审校

reused Notes:
- 需要检查实际教材 target meaning 与当前 learner presentation 是否一致
```

在这些内容审校完成前，不解除 LearningAdmission，不让 Klose 正式学习。

## Next work order

1. 为 97 个新 Note 补齐可靠的 Word / IPA / Meaning facts。
2. 为 97 个新 Note 生成 LearnerLevel=4 的 Example / Translation。
3. 检查 124 个 reused Notes：实际教材 target meaning 与当前呈现不一致时，仅修 Learner Presentation，不改 Stable NoteID。
4. fingerprint v2 sync；完成真实 model/human review，直到 current pending=0。
5. 建立实际 Grade 4 的显式 Learning Admission：221 Notes。
6. 当前学习 Tag 固定为：

```text
learning::klose::grade4
```

7. 非 Grade-4-current 的 released Notes 保留在 study，但不 admission；Anki 中保持 Suspend。
8. 将 `source_reconciliation_registry.csv` 的 `LearningAdmission` 改为 `allowed`。
9. release gate 通过后生成最终 `anki-import.csv`。
10. Anki 原地导入：全部 baseline Suspend，只 Unsuspend `tag:learning::klose::grade4`。

## Current Anki state

历史状态：

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

Klose 尚未产生真实 Review History，因此当前仍是修正学习集合的低风险窗口。

## Deferred

同形异义正面消歧（如 `cook n.` / `cook v.`）仍需单独 Note Type migration，引入 `PromptHint`；不要在本轮偷偷改变现有 Anki Note Type。

四下 Useful Expressions 暂不处理，先完成 Vocabulary Grade-4 learning set。
