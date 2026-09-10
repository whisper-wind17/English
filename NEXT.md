# NEXT — Klose Learning

Last updated: 2026-09-10

## 1. Current task

当前主任务：**Grade 5–6 实际教材 SourceID / SourceEdition provenance resolution**。

启动顺序：

```text
AGENTS.md
→ NEXT.md
→ docs/GRADE5_6_ACTUAL_TEXTBOOK_INTAKE.md
→ docs/SOURCE_RECONCILIATION.md
→ docs/KLOSE_VOCABULARY_SYSTEM.md / docs/EXPRESSIONS_SYSTEM.md
→ anki/klose/source_reference/ Grade 5–6 actual source
→ anki/klose/review/grade5_6_reconciliation/ durable reconciliation truth
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
  provisional learning units                         = 504
  reuse-existing                                     = 148
  new-stable-identity proposals                      = 301 rows / 293 future identity groups
  morphology-only                                    = 45
  held                                               = 10
  pending review                                     = 0
  Stable NoteID allocation                           = 0

Grade 5–6 Expressions reconciliation                 = CLOSED / VALIDATED / CHECKPOINTED
  source occurrences reviewed                        = 153 / 153
  mapped                                             = 138
  source-only                                        = 15
  existing Stable KE groups reused                   = 8
  new-stable-identity proposal groups                = 110
  pending review                                     = 0
  Stable ExpressionID allocation                     = 0

Klose Publish / Anki update                          = NOT STARTED
```

Durable reconciliation truth:

```text
anki/klose/review/grade5_6_reconciliation/vocabulary_candidates.csv
anki/klose/review/grade5_6_reconciliation/vocabulary_decisions.csv
anki/klose/review/grade5_6_reconciliation/vocabulary_status.json
anki/klose/review/grade5_6_reconciliation/expression_source_candidates.csv
anki/klose/review/grade5_6_reconciliation/expression_source_decisions.csv
anki/klose/review/grade5_6_reconciliation/expression_identity_groups.csv
anki/klose/review/grade5_6_reconciliation/expression_status.json
```

Full reconciliation checkpoint evidence:

```text
last Expression durable data checkpoint = a50d9e9190861b85ad2f43f92686515e5e48d3c2
completion gate commit                   = 3a68371e92e95c3fd8413db6c279e01053e99d7c
completion workflow run                  = 34455387659 / PASS

independent Vocabulary result:
  candidates=504, decisions=504, pending=0
  stable_registry=901, transient_inbox=absent, stable_id_allocation=0

independent Expressions result:
  source=153, decisions=153, mapped=138, source_only=15
  new_groups=110, reused_stable_groups=8, pending=0
  stable_registry=66, transient_inbox=absent, stable_id_allocation=0
```

The 10 Vocabulary `held` rows and 15 Expression `source-only` rows are reviewed boundary/defer decisions, not unreviewed queue items.

## 3. Hard decisions

- Grade 5–6 实际教材不经过第三方词库；direct Klose reconciliation 已闭合。
- Vocabulary identity 继续按 target sense；morphology 本身不 mint Vocabulary NoteID。
- Useful Expressions 按 `CanonicalForm + CommunicativeFunction`；`1 source sentence != 1 Expression card`。
- Grade 5 Lower 6 条 Proverbs 继续作为独立 Proverb Source。
- `SourceID / SourceEdition` 未可靠确认时不得猜测，也不得进入 stable source-identity allocation。
- `new-proposal` 只是已审 proposal：293 Vocabulary future groups 和 110 Expression future groups目前都没有 Stable ID。
- Stable NoteID / ExpressionID 与已有 Anki FSRS / Review History 必须保持稳定。

## 4. Immediate next work

```text
1. Resolve Grade 5–6 actual textbook SourceID / SourceEdition from reliable evidence
2. Re-run Source / reconciliation fingerprints if provenance fields change
3. Confirm zero stale reconciliation decisions after provenance resolution
4. Only then design the Stable NoteID / ExpressionID allocation gate
5. Keep held / source-only decisions explicit; do not silently admit them
```

下一阶段仍不是 Publish / Anki 更新。

## 5. Mutation boundary

当前禁止：

```text
third-party merge/allocation
Grade 5–6 Stable NoteID / ExpressionID allocation before provenance resolution
silent reuse of stale reconciliation decisions
Klose Learner / Release mutation
publish regeneration for Grade 5–6
Anki update
```

## 6. Third-party corpus — hold

第三方词库继续独立冻结：Stage A/B CLOSED，`2820` Vocabulary identities / `2794` learner candidates；实际 merge/allocation 未启动，显式 content exclusion 仍仅 `a / an / the`。详细历史见 `docs/THIRD_PARTY_STAGE_B_RECONCILIATION.md`。
