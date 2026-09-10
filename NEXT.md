# NEXT — Klose Learning

Last updated: 2026-09-10

## 1. Current task

当前主任务：**完成 Grade 5–6 current Vocabulary 的正式 Release，并生成可导入 Anki 的最终 Vocabulary artifact。**

启动顺序：

```text
AGENTS.md
→ NEXT.md
→ docs/KLOSE_VOCABULARY_SYSTEM.md
→ docs/LEARNER_REVIEW_REGISTRY.md
→ docs/GRADE5_6_ACTUAL_TEXTBOOK_INTAKE.md
→ docs/SOURCE_RECONCILIATION.md
→ anki/klose/learner/grade5_6_learning_scope.json
→ anki/klose/master/build_stats.csv
→ anki/klose/master/release_registry*.csv
→ tools/check_klose_release_ready.py
```

## 2. Decision reconciliation

Grade 5–6 Source provenance 与 Klose Learning Scope 必须分开理解。

Source provenance 仍保持：

```text
Grade 5 Upper  = 2024-revision / verified-current-revision
Grade 5 Lower  = pre-2024-revision / verified-legacy-source-current-revision-mismatch
Grade 6 Upper  = 2024-revision / verified-current-revision
Grade 6 Lower  = pre-2024-revision / verified-legacy-source-hold-for-klose-future-edition
```

这些状态继续作为 Source Fact / audit truth，不得静默改写或删除。

但在旧 provenance checkpoint 之后，用户已显式接受四册 captured Grade 5–6 vocabulary 作为 Klose 当前学习范围：

```text
anki/klose/learner/grade5_6_learning_scope.json
DecisionBasis                         = explicit-user-current-learning-scope
ScopeStatus                           = accepted
SourceProvenanceAffectsLearningAdmission = false
StableIdentityAllocationAuthorized    = true
Books                                 = 5上 / 5下 / 6上 / 6下 all Accepted
origin commit                         = 86610816dfe0d2658d0d16acd102e61b458a67c5
```

因此旧 NEXT 中“5下/6下 provenance blocker 阻止 Learning Admission / Stable allocation”的策略已被后续显式学习范围决策覆盖。SourceEdition 仍是真实来源属性，但不再作为这个已接受 learning scope 的 admission blocker。

## 3. Vocabulary current state

```text
Grade 5–6 source occurrences                        = 509
reconciled provisional learning units               = 504
mapped lexical source occurrences                   = 454
morphology-only / held occurrences                  = 45 / 10

Stable Vocabulary registry                          = 1189 active Notes
Grade 5–6 current new Stable Notes                  = 288
Grade 5–6 current reused Stable Notes               = 144
Grade 5–6 current unique Notes                      = 432

Klose LearnerLevel                                  = 4
Learning Admission allowed                         = 627
Learning Admission held                            = 345
allowed but unreleased                              = 334
LearningOrder count / max                          = 627 / 627

existing released Notes                             = 638
learner review scope (released ∪ allowed)           = 972
model-reviewed                                      = 972
human-reviewed                                      = 0
pending                                             = 0
```

Grade 5–6 new learner presentation / lexical facts 已完成；288 个新 Notes 已进行全量 model semantic review。审校中发现并修正 `grandparent / then / judge / run / off` 五条 learner presentation 问题，修正后通过完整 Vocabulary Build、Grade 5–6 current merge checker 与 learner-content gate。

正式 review approval 已完成：

```text
approval manifest = anki/klose/learner/review_approvals/grade5-6-current-v1-model-reviewed.csv
approval status   = model-reviewed
review scope      = 972
pending           = 0
approval merge    = 4e74a910951fd4ed1fe8fc158eeb0632e8145f2c
post-merge rebuild= 4d403d174867888872204da3f710dcdf43aaf973
```

`Build Valid` / `Content Releasable` 已验证；**334 个 current allowed-but-unreleased Notes 尚未写入 Release registry，因此完整 Grade 5–6 current Vocabulary Release 仍未完成。**

## 4. Validation evidence

最近关键验证：

```text
PR #10  pre-release learner guardrails              = PASS / merged
PR #11  semantic review fixes                       = PASS / merged
PR #12  343 pending review approval                 = PASS / merged
main Build after approval                           = 34488523042 / PASS
Grade 5–6 Reconciliation Completion after approval = 34488523006 / PASS

current durable review state:
  learner_review_registry_current = 972
  learner_model_reviewed_current  = 972
  learner_review_pending_current  = 0
```

当前 `tools/check_klose_grade5_6_current_merge.py` 与 `grade5_6_learning_scope.json` 一致：Source provenance 是 audit metadata，不作为已显式接受 learning scope 的 Learning Admission gate。

## 5. Immediate next work

```text
1. Derive exact Vocabulary release delta
   target = Learning Admission allowed ∩ unreleased
   expected = 334 Notes
   - derive from durable registries; do not hard-code identity guesses
   - require current fingerprint approval for every target Note
   - preserve all existing ReleaseOrder / NoteID history

2. Execute scoped Release allocation
   - append only the missing allowed Notes to release_registry_extensions.csv
   - never duplicate/reorder the existing 638 released Notes
   - use a guarded durable tool/checker rather than hand-edit generated publish files
   - no Source / Identity mutation

3. Validate and merge
   - full Vocabulary Build
   - persistent-state check
   - Grade 5–6 current merge checker
   - release-ready checker
   - diff-scope / release-order regression

4. After main rebuild
   - expect released universe = 972 only if checker-derived delta confirms 334
   - verify study.csv / anki-import.csv are generated from Release truth
   - perform Anki preflight; Anki itself remains unchanged until explicit import/sync action

5. Only after Vocabulary Release is CHECKPOINTED
   - continue Grade 5–6 Expressions as an independent identity/release lane
```

## 6. Mutation boundary

当前允许：

```text
Vocabulary Release registry extension for checker-derived allowed ∩ unreleased Notes
Release tooling/checker changes needed for this transition
regenerated derived Master/Learner/Publish produced by the normal Build
NEXT.md checkpoints
```

当前禁止：

```text
manual edit of generated publish files
renumber/reuse of Stable NoteIDs
rewriting existing 638 ReleaseOrder/history
silent deletion/rewrite of Grade 5 Lower / Grade 6 Lower provenance evidence
third-party merge/allocation
ExpressionID allocation mixed into the Vocabulary release change
claiming Anki Updated before an actual Anki import/sync occurs
```

## 7. Expressions / third-party hold

Grade 5–6 Expressions reconciliation remains independently CLOSED / VALIDATED / CHECKPOINTED:

```text
source occurrences reviewed              = 153 / 153
mapped                                   = 138
source-only                              = 15
existing Stable KE groups reused         = 8
new stable proposal groups               = 110
pending / stale                          = 0 / 0
Stable ExpressionID allocation           = not yet executed in current release lane
```

第三方词库继续独立冻结：Stage A/B CLOSED，`2820` Vocabulary identities / `2794` learner candidates；实际 merge/allocation 未启动，显式 content exclusion 仍仅 `a / an / the`。详细历史见 `docs/THIRD_PARTY_STAGE_B_RECONCILIATION.md`。
