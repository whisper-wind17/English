# NEXT — Klose Learning

Last updated: 2026-09-10

## 1. Current task

当前主任务：**Grade 5 Lower / Grade 6 Lower revised-textbook source blocker resolution**。

启动顺序：

```text
AGENTS.md
→ NEXT.md
→ docs/GRADE5_6_ACTUAL_TEXTBOOK_INTAKE.md
→ docs/SOURCE_RECONCILIATION.md
→ docs/KLOSE_VOCABULARY_SYSTEM.md / docs/EXPRESSIONS_SYSTEM.md
→ anki/klose/source_reference/grade5_6_source_provenance.json
→ anki/klose/source_reference/grade5_6_actual_textbook_manifest.csv
→ anki/klose/review/grade5_6_reconciliation/ durable reconciliation truth
```

## 2. Current state

```text
Grade 5–6 actual-textbook Source materialization     = CLOSED / VALIDATED
Vocabulary source occurrences                        = 509
Useful Expressions source occurrences                = 153
Grade 5 Lower Proverbs                               = 6
Morphology source occurrences                        = 58

Grade 5–6 SourceID provenance                        = CLOSED / VALIDATED / CHECKPOINTED
Canonical SourceID                                   = renjiao_start3
SourceIdentityPending                                = false
Source provenance rows                               = 726
Source provenance fingerprint                        = 5e4a90e6d8d46769c71ded160ea2310f5e655a8de926a96724366e975d621df4

Book-level SourceEdition:
  Grade 5 Upper                                      = 2024-revision / verified-current-revision
  Grade 5 Lower                                      = pre-2024-revision / allocation-held
  Grade 6 Upper                                      = 2024-revision / verified-current-revision
  Grade 6 Lower                                      = pre-2024-revision / allocation-held

Grade 5–6 Vocabulary reconciliation                  = CLOSED / VALIDATED / CHECKPOINTED
  provisional learning units                         = 504
  reuse-existing                                     = 148
  new-stable-identity proposals                      = 301 rows / 293 future identity groups
  morphology-only                                    = 45
  held                                               = 10
  pending review                                     = 0
  stale decisions after provenance resolution        = 0
  Stable NoteID allocation                           = 0

Grade 5–6 Expressions reconciliation                 = CLOSED / VALIDATED / CHECKPOINTED
  source occurrences reviewed                        = 153 / 153
  mapped                                             = 138
  source-only                                        = 15
  existing Stable KE groups reused                   = 8
  new-stable-identity proposal groups                = 110
  pending review                                     = 0
  stale decisions after provenance resolution        = 0
  Stable ExpressionID allocation                     = 0

StableIDAllocationAllowed                            = false
Klose Publish / Anki update                          = NOT STARTED
```

`2024-revision` / `pre-2024-revision` 表示 revision lineage，不表示具体物理印刷年份。

Grade 3–4 既有 `rj_start1 / klose-current` 保持 historical legacy alias；当前不原地改写其 stable source mapping，统一命名若未来需要必须单独做 source-identity migration。

## 3. Provenance blockers

当前两个 blocker 都已结构化进入 Source provenance state：

```text
Grade 5 Lower:
  captured source = pre-2024 revision
  current revised PEP lower volume differs from captured source
  → preserve captured source, but do not allocate Stable IDs from it

Grade 6 Lower:
  captured source = pre-2024 revision
  Klose future revised lower-volume source is not yet confirmed
  → preserve captured source, allocation held
```

因此 provenance identity 已经解决，但 **Grade 5–6 全集的 Stable-ID allocation gate 尚未打开**。

## 4. Validation evidence

```text
provenance resolver initial run       = 34458225677 / PASS
provenance sanitation run             = 34458793594 / PASS
Vocabulary reconciliation rebind      = 34458460099 / PASS
Expression reconciliation rebind      = 34458480619 / PASS
final integrated completion           = 34458855247 / PASS
final actual-source gate              = 34458855268 / PASS

independent Vocabulary result:
  candidates=504, decisions=504, pending=0, stale=0
  stable_registry=901, stable_id_allocation=0

independent Expressions result:
  source=153, decisions=153, mapped=138, source_only=15, stale=0
  new_groups=110, reused_stable_groups=8
  stable_registry=66, stable_id_allocation=0
```

Source provenance 与 semantic CandidateFingerprint 已分离：provenance change 会独立生成 `SourceProvenanceFingerprint` 并进入 completion gate，不会把单纯 provenance 修正误判为 target-sense / communicative-function 变化。

本轮最终 diff scope 已独立确认：只修改 Source、Grade 5–6 reconciliation status、相关 tools/workflows/docs；未修改 Klose Master / Learner / Release / Publish / Anki state。

## 5. Immediate next work

```text
1. Resolve Grade 5 Lower revised actual-textbook evidence
   - do not silently replace the captured legacy source
   - materialize revised source as a distinct revision lineage
   - reconcile only the affected Grade 5 Lower source/candidates

2. Keep Grade 6 Lower legacy source held
   - wait for reliable evidence of the actual revised lower volume Klose will use
   - do not mint Stable IDs from the current legacy capture

3. After lower-volume source scope is closed
   - recompute provenance fingerprint
   - re-run Vocabulary / Expressions reconciliation closure
   - confirm stale=0
   - then design/execute Stable NoteID / ExpressionID allocation gate
```

下一阶段仍不是 Publish / Anki 更新。

## 6. Mutation boundary

当前禁止：

```text
third-party merge/allocation
Stable ID allocation from Grade 5 Lower / Grade 6 Lower legacy captured source
silent overwrite/delete of legacy source evidence
Klose Learner / Release mutation
publish regeneration for Grade 5–6
Anki update
```

已确认的 Grade 5 Upper / Grade 6 Upper provenance 可继续作为未来 allocation input，但在全集 allocation gate 设计完成前仍不单独 mint Stable IDs。

## 7. Third-party corpus — hold

第三方词库继续独立冻结：Stage A/B CLOSED，`2820` Vocabulary identities / `2794` learner candidates；实际 merge/allocation 未启动，显式 content exclusion 仍仅 `a / an / the`。详细历史见 `docs/THIRD_PARTY_STAGE_B_RECONCILIATION.md`。
