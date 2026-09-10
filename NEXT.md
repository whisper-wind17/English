# NEXT — Klose Learning

Last updated: 2026-09-10

## 1. Current task

当前主任务：**Grade 5–6 Klose 实际教材 → Klose Stable Identity reconciliation**。

启动顺序：

```text
AGENTS.md
→ NEXT.md
→ docs/GRADE5_6_ACTUAL_TEXTBOOK_INTAKE.md
→ docs/KLOSE_VOCABULARY_SYSTEM.md / docs/EXPRESSIONS_SYSTEM.md
→ anki/klose/source_reference/ actual Grade 5–6 source
→ anki/klose/master/ current stable identity truth
```

## 2. Current state

```text
Grade 5–6 actual-textbook Source materialization     = CLOSED / VALIDATED
Vocabulary source occurrences                        = 509
Useful Expressions source occurrences                = 153
Grade 5 Lower Proverbs                               = 6
Morphology source occurrences                        = 58
SourceID / SourceEdition                             = PENDING CONFIRMATION

Grade 5–6 → Klose Stable Identity reconciliation    = CURRENT / NOT STARTED
Grade 5–6 NoteID / ExpressionID allocation          = NOT STARTED
Klose Publish / Anki update                         = NOT STARTED
```

Source Completion evidence:

```text
source-completion workflow PASS
existing Klose build workflow PASS
existing build result: No generated changes
```

Source artifacts are under `anki/klose/source_reference/`. Morphology is occurrence-level and source-traceable; the obsolete pending-trace morphology table has been retired.

## 3. Hard decisions

- Grade 5–6 真实教材 **不先与第三方词库匹配**；固定路径是 `actual textbook → directly reconcile with Klose existing stable identities`。
- Vocabulary 按明确 target sense 建 identity；同词异义不可字符串合并。
- Useful Expressions 原句是 Source Fact，`1 source sentence != 1 Expression card`；后续按 `CanonicalForm + CommunicativeFunction` resolution。
- Grade 5 Lower 的 6 条 Proverbs 单独作为 Proverb Source。
- Grade 6 过去式、比较级、显式 `-ing` / plural morphology 单独保存在 Morphology Registry；词形变化本身不 mint Vocabulary NoteID。
- `SourceID / SourceEdition` 未确认时不得猜测；可做 reconciliation review，但 stable source-identity allocation 前必须保持该 provenance blocker 显式可见。
- Stable NoteID / ExpressionID 与已有 Anki FSRS / Review History 必须保持稳定。

详细 schema、边界、Completion Gate 与 reconciliation SOP：`docs/GRADE5_6_ACTUAL_TEXTBOOK_INTAKE.md`。

## 4. Immediate next work

```text
1. Build Grade 5–6 Vocabulary reconciliation candidates against current Klose Stable NoteIDs
2. Build Grade 5–6 Expression candidates against current Stable ExpressionIDs
3. Review same-surface / same-function / homograph / morphology edge cases
4. Close all reconciliation decisions as reuse / new-proposal / held
5. Run independent reconciliation Completion Recheck
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
