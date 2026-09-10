# NEXT — Klose Learning

Last updated: 2026-09-10

## 1. Current task

当前主任务：**Grade 5–6 Klose 实际教材 → Klose Stable Expressions reconciliation**。

启动顺序：

```text
AGENTS.md
→ NEXT.md
→ docs/GRADE5_6_ACTUAL_TEXTBOOK_INTAKE.md
→ docs/EXPRESSIONS_SYSTEM.md / docs/KLOSE_VOCABULARY_SYSTEM.md
→ anki/klose/source_reference/ actual Grade 5–6 source
→ anki/klose/expressions/master/ current Stable Expression identity truth
```

## 2. Current state

```text
Grade 5–6 actual-textbook Source materialization     = CLOSED / VALIDATED
Vocabulary source occurrences                        = 509
Useful Expressions source occurrences                = 153
Grade 5 Lower Proverbs                               = 6
Morphology source occurrences                        = 58
SourceID / SourceEdition                             = PENDING CONFIRMATION

Grade 5–6 Vocabulary reconciliation                  = CLOSED / VALIDATED / CHECKPOINTED
Vocabulary provisional learning units                = 504
  reuse-existing                                     = 148
  new-stable-identity proposals                      = 301 rows / 293 future identity groups
  morphology-only                                    = 45
  held                                               = 10
Vocabulary pending review                            = 0
Vocabulary Stable NoteID allocation                  = 0

Grade 5–6 Expressions reconciliation                 = CURRENT / NOT STARTED
Grade 5–6 ExpressionID allocation                    = NOT STARTED
Klose Publish / Anki update                          = NOT STARTED
```

Vocabulary durable reconciliation truth:

```text
anki/klose/review/grade5_6_reconciliation/vocabulary_candidates.csv
anki/klose/review/grade5_6_reconciliation/vocabulary_decisions.csv
anki/klose/review/grade5_6_reconciliation/vocabulary_status.json
```

Vocabulary checkpoint evidence:

```text
last durable data checkpoint  = 4d5df1860b28fc624b77918b5cdd0a8b3dfc71dc
completion recheck commit      = 8a48ad6b76c14e6a954bb0a574ae30a37119a418
completion workflow run        = 34449587619 / PASS
independent result             = candidates=504, decisions=504, pending=0
                                stable_registry=901, transient_inbox=absent,
                                stable_id_allocation=0
```

The 10 `held` rows are explicit reviewed defer/boundary decisions, not unreviewed blockers. Examples include mixed target-sense rows (`glass`, `heat`) and items routed toward Expressions review (`good job`, `for example`, `have ... class`).

## 3. Hard decisions

- Grade 5–6 真实教材 **不先与第三方词库匹配**；固定路径是 `actual textbook → directly reconcile with Klose existing stable identities`。
- Vocabulary 按明确 target sense 建 identity；同词异义不可字符串合并。
- Useful Expressions 原句是 Source Fact，`1 source sentence != 1 Expression card`；按 `CanonicalForm + CommunicativeFunction` resolution。
- Grade 5 Lower 的 6 条 Proverbs 单独作为 Proverb Source。
- 过去式、比较级、显式 `-ing` / plural morphology 单独保存在 Morphology Registry；词形变化本身不 mint Vocabulary NoteID。
- `SourceID / SourceEdition` 未确认时不得猜测；可做 reconciliation review，但 stable source-identity allocation 前必须保持该 provenance blocker 显式可见。
- Stable NoteID / ExpressionID 与已有 Anki FSRS / Review History 必须保持稳定。
- Vocabulary reconciliation 已闭合，但 **new-proposal 仍不是 NoteID allocation**；不得把 293 future groups 当作已创建 Notes。

详细 schema、边界、Completion Gate 与 reconciliation SOP：`docs/GRADE5_6_ACTUAL_TEXTBOOK_INTAKE.md`。

## 4. Immediate next work

```text
1. Build 153 Grade 5–6 Useful Expression source occurrences into function-aware reconciliation candidates
2. Compare candidates with current Stable ExpressionIDs using CanonicalForm + CommunicativeFunction
3. Review same-function / different-function / slot-frame / fixed-chunk / low-transfer edge cases
4. Close every Expression candidate as reuse / new-proposal / held
5. Run independent Expressions reconciliation Completion Recheck
6. Checkpoint full Grade 5–6 Vocabulary + Expressions reconciliation closure
```

本阶段只产生 reconciliation truth / proposal，不分配新 Stable NoteID / ExpressionID。

## 5. Mutation boundary

当前阶段禁止：

```text
third-party merge/allocation
Grade 5–6 Stable NoteID / ExpressionID allocation
Klose Master / Learner / Release mutation
publish regeneration for Grade 5–6
Anki update
```

当前 DoD 是 **Grade 5–6 Vocabulary / Expressions direct Klose reconciliation closure**，不是合入或发布。

## 6. Third-party corpus — hold

第三方词库保持独立冻结：Stage A/B CLOSED，`2820` Vocabulary identities / `2794` learner candidates，实际 merge/allocation 未启动；当前显式 content exclusion 仅 `a / an / the`。详细历史见 `docs/THIRD_PARTY_STAGE_B_RECONCILIATION.md`。
