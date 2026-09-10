# NEXT — Klose Learning

Last updated: 2026-09-10

## 1. Current task

当前主任务：**Grade 5–6 current Vocabulary 的 GitHub Release 已完成并 CHECKPOINT；下一步是 Anki preflight / 正式导入确认。**

启动顺序：

```text
AGENTS.md
→ NEXT.md
→ docs/KLOSE_VOCABULARY_SYSTEM.md
→ docs/LEARNER_REVIEW_REGISTRY.md
→ docs/ANKI_MIGRATION.md
→ anki/klose/master/build_stats.csv
→ anki/klose/learner/learning_admission.csv
→ anki/klose/learner/presentation_review_registry.csv
→ anki/klose/publish/study.csv
→ anki/klose/publish/anki-import.csv
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

用户已显式接受四册 captured Grade 5–6 vocabulary 作为 Klose 当前学习范围：

```text
anki/klose/learner/grade5_6_learning_scope.json
DecisionBasis                             = explicit-user-current-learning-scope
ScopeStatus                               = accepted
SourceProvenanceAffectsLearningAdmission  = false
StableIdentityAllocationAuthorized        = true
Books                                     = 5上 / 5下 / 6上 / 6下 all Accepted
origin commit                             = 86610816dfe0d2658d0d16acd102e61b458a67c5
```

因此 SourceEdition 继续描述真实来源版本，但不阻塞该已接受 learning scope 的 Stable Identity / Learning Admission / Release。

## 3. Vocabulary current state — CHECKPOINTED

```text
Grade 5–6 source occurrences                        = 509
reconciled provisional learning units               = 504
mapped lexical source occurrences                   = 454
morphology-only / held occurrences                  = 45 / 10

Stable Vocabulary active Notes                      = 1189
persistent registry rows incl. merged identities    = 1194
Grade 5–6 current new Stable Notes                  = 288
Grade 5–6 current reused Stable Notes               = 144
Grade 5–6 current unique Notes                      = 432

Klose LearnerLevel                                  = 4
Learning Admission allowed                         = 627
Learning Admission held                            = 345
allowed but unreleased                              = 0
LearningOrder count / max                          = 627 / 627

released Vocabulary Notes                           = 972
learner review scope (released ∪ allowed)           = 972
model-reviewed                                      = 972
human-reviewed                                      = 0
pending                                             = 0

publish/study.csv                                   = 972 Notes
publish/anki-import.csv                             = 972 Notes
GitHub Vocabulary Release                           = IMPLEMENTED / VALIDATED / CHECKPOINTED
Anki Updated                                        = false / NOT YET CONFIRMED
```

Grade 5–6 new learner presentation / lexical facts 已完成；288 个新 Notes 已进行全量 model semantic review。审校中发现并修正 `grandparent / then / judge / run / off` 五条 learner presentation 问题。

正式 review approval：

```text
approval manifest = anki/klose/learner/review_approvals/grade5-6-current-v1-model-reviewed.csv
approval status   = model-reviewed
review scope      = 972
pending           = 0
approval merge    = 4e74a910951fd4ed1fe8fc158eeb0632e8145f2c
```

正式 Vocabulary Release：

```text
PR #13                           = merged
release merge                    = 738343e7e03118cf0bcf5b76a14780db3d55a822
release delta                    = 334 Notes
release_registry legacy          = 518
release_registry_extensions      = 454 = prior 120 + appended 334
release total                    = 972
release history                  = byte-exact append-only
post-merge generated commit      = 33b2e983efec50a8116bef151848775549ee6f98
```

Release registry 是长期发布真源；`study.csv` / `anki-import.csv` 由正常 Build 从 Release truth 生成，不允许手工维护。

## 4. Validation evidence

PR #13 与 main post-merge 均完成独立验证：

```text
PR #13 Build Klose Vocabulary                    = 34494566746 / PASS
PR #13 Grade 5–6 Current Merge                   = 34494566640 / PASS

main Build Klose Vocabulary                      = 34494909929 / PASS
main Grade 5–6 Current Merge                     = 34494909931 / PASS
main Grade 5–6 Reconciliation Completion         = 34494909937 / PASS
```

main Build 的关键 state-transition evidence：

```text
Persistent state:
  legacy_registry                                = 802
  identity_extensions                            = 392
  total_registry                                 = 1194
  legacy_released                                = 518
  release_extensions                             = 454
  total_released                                 = 972

Release history:
  extension_before                               = 120
  appended                                       = 334
  extension_now                                  = 454
  total                                           = 972
  historical byte prefix                         = exact

Release materialization:
  before                                          = 638
  after                                           = 972
  newly_visible                                   = 334

Learning Admission:
  current                                         = 627
  grade4                                          = 221
  grade5_6                                        = 432
  grade5_6_only                                   = 406
  current_unreleased                              = 0
  library_held                                    = 345
  LearningOrder                                   = 000001..000627

Review:
  required                                        = 972
  model-reviewed                                  = 972
  pending                                         = 0
  invalidated                                     = 0

Release-ready:
  released                                        = 972
  current_learning                                = 627
  held                                            = 345
  study                                           = 972
  anki_import                                     = 972
  unresolved_reports                              = 0
  pending_reviews                                 = 0
```

90 个 held legacy Notes 仍缺 British/American IPA；这些 Notes 不在当前 admitted learning set，因此是 library debt，不阻塞本次 current Vocabulary Release。

post-merge generated diff 只修改 derived Master / Publish / build_stats；`study.csv` 与 `anki-import.csv` 均只新增 334 条 release-visible Notes，没有 Source / Stable Identity / Learning Admission 再分配。

## 5. Immediate next work

```text
1. Anki preflight
   - use only anki/klose/publish/anki-import.csv
   - confirm Note Type = Klose Vocabulary
   - confirm deck = Klose-English::Vocabulary
   - import as Update Existing Notes, not a new Note Type/deck migration
   - verify NoteID remains the stable match/update key
   - do not reset scheduling / FSRS / review history

2. Formal Anki update
   - perform the actual Anki Desktop import/sync only through the established migration/import procedure
   - after import, verify existing reviewed cards retained scheduling/history
   - verify newly released Notes entered the intended learning deck/state
   - only after observed evidence may `Anki Updated` change to true

3. Checkpoint Anki state
   - record import/sync result and any exception in NEXT.md
   - GitHub Release and Anki FSRS state remain separate truth domains

4. After Vocabulary Anki update is closed
   - continue Grade 5–6 Expressions as an independent identity/release lane
```

## 6. Mutation boundary

当前允许：

```text
Anki preflight / formal import verification
NEXT.md checkpoint of observed Anki state
Vocabulary bug fixes only if validation finds a concrete defect
```

当前禁止：

```text
manual edit of generated publish files
renumber/reuse of Stable NoteIDs
rewrite/removal of historical Release rows
silent deletion/rewrite of Grade 5 Lower / Grade 6 Lower provenance evidence
third-party merge/allocation
ExpressionID allocation mixed into Vocabulary Anki update
claiming Anki Updated before an actual import/sync is observed
changing FSRS/review history from GitHub-side content operations
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
