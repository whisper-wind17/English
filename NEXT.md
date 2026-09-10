# NEXT — Klose Learning

Last updated: 2026-09-11

## 1. Current task

当前主任务：**Grade 5–6 current Vocabulary 的 GitHub Release 与 Anki preflight 已完成并 CHECKPOINT；等待在既有 Anki Desktop Collection 中执行正式 972-note import / sync，并回写实际设备状态。**

启动顺序：

```text
AGENTS.md
→ NEXT.md
→ docs/ANKI_CURRENT_RELEASE_IMPORT.md
→ docs/ANKI_SYNC_WORKFLOW.md
→ docs/KLOSE_VOCABULARY_SYSTEM.md
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
Anki preflight                                      = PASS / CHECKPOINTED
Anki Updated                                        = false / DEVICE IMPORT NOT YET OBSERVED
```

Grade 5–6 new learner presentation / lexical facts 已完成；288 个新 Notes 已进行全量 model semantic review。审校中发现并修正 `grandparent / then / judge / run / off` 五条 learner presentation 问题。

### 3.1 Grade 5–6 Learner Presentation policy — FROZEN FOR CURRENT RELEASE

Grade 5 / 6 是 **Source Grade**；Klose 当前学习这些词时仍使用：

```text
LearnerProfile = klose
LearnerLevel   = 4
```

因此：

```text
Source Grade 5/6 ≠ LearnerLevel 5/6
```

五、六年级来源词汇的 learner presentation 必须按 Klose 当前四年级理解能力生成；目标词本身可以高于四年级，但释义和例句的 surrounding language 应尽量保持在 LearnerLevel 4。

本次 288 个 Grade 5–6 新 Stable Notes 的 learner-content gate 已验证：

```text
active new Notes             = 288
bilingual examples           = 288 / 288
unique English examples      = 288 / 288
maximum example length       = 14 tokens
high-risk sense cues checked = 24
later auxiliary vocabulary   = 0
```

其中 target lexical item 本身不作为“later auxiliary vocabulary”违规项；检查重点是避免为了学习一个 Grade 5/6 目标词，又在例句中额外引入 Klose 尚未掌握的 Grade 5/6 实词。

Grade 5–6 reused Notes 进入 current learning scope 后同样按 `LearnerLevel=4` 处理；此前已有 11 条 reused learner examples 因辅助词难度过高而被降阶。未来如果提高 LearnerLevel，只升级 Learner Presentation 并重新 review；不得因为 Source Grade 更高而自动提高 LearnerLevel，也不得改变 Stable NoteID / Anki Review History。

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

## 5. Anki preflight — PASS / CHECKPOINTED

正式 artifact 已验证：

```text
file                     = anki/klose/publish/anki-import.csv
encoding                 = UTF-8 without BOM
#separator               = Comma
#notetype                = Klose Vocabulary
#deck                    = Klose-English::Vocabulary
#tags column             = 14
first data field         = NoteID
rows                     = 972
study data equality      = exact / release gate PASS
LearningOrder max        = 000627
PromptHint nonempty      = 4
```

Anki Note Type 长期契约：

```text
NoteID
CanonicalWord
Word
PromptHint
British
American
MeaningPrimary
ExampleSentence
ExampleTranslation
LearnerLevel
LearningOrder
Sources
SourceBooks
UserMemo
```

当前 release-specific SOP 已建立并合入：

```text
docs/ANKI_CURRENT_RELEASE_IMPORT.md
PR #14 merge = 14c88ad3b4fb93f07d40cde4eed9e03c191f8c5f
```

同步 SOP 已从历史固定 `638 / 221 / 417` reset 模式修正为 state-aware 模式：进入真实学习后，只对 current allowed `is:new` Cards materialize admission / New Card Position；不得批量覆盖 Learning/Review Cards 的 suspension / Due / FSRS state。

已知最后一次明确设备侧 checkpoint：最初 `518 Notes / 518 Cards` 的 NoteID-first `Klose Vocabulary` 导入已完成。后续是否已经在设备上执行过 638-note Grade-4 Release、PromptHint schema migration、LearningOrder schema migration，当前 repo 没有足够的 observed device evidence，因此正式 972-note import 前必须先检查现有 Note Type fields，而不能假定或重跑迁移。

当前执行环境没有可直接操作 Anki Desktop/AnkiWeb 的连接能力；插件目录也没有 Anki 集成。因此 `Anki Updated` 必须保持 false，直到实际 Desktop import / sync 被用户执行并观察验收。

## 6. Immediate next work

```text
1. On Anki Desktop, inspect existing Klose Vocabulary Note Type
   - NoteID must remain field #1
   - verify PromptHint exists at #4
   - verify LearningOrder exists after LearnerLevel
   - if missing, add/reposition in the existing Note Type only
   - do not create a second Note Type / Card Type

2. Back up Collection / Deck

3. Import the formal 972-note artifact
   - only anki/klose/publish/anki-import.csv
   - Note Type = Klose Vocabulary
   - Deck = Klose-English::Vocabulary
   - Existing Notes = Update
   - Match scope = Note Type
   - Identity = NoteID
   - Tags -> Tags
   - UserMemo -> Nothing / do not map

4. Validate existing memory state
   - sample 3–5 existing NoteIDs
   - Reviews / Due / Interval preserved
   - no duplicate Note Type / Cards
   - final stable Notes/Cards target = 972 / 972

5. Materialize only future New-card admission/order
   - current allowed tags = learning::klose::grade4 OR learning::klose::grade5-6
   - allowed + is:new -> future New queue
   - held + is:new -> suspended
   - Learning/Review Cards -> do not bulk reset suspension or Due
   - sort remaining allowed New Cards by LearningOrder and Reposition

6. Desktop -> AnkiWeb -> iPad sync and spot-check

7. After observed success
   - update NEXT.md: Anki Updated = true
   - record actual post-import counts / exceptions
   - then continue Grade 5–6 Expressions as an independent lane
```

## 7. Mutation boundary

当前允许：

```text
Anki Desktop schema inspection
one-time in-place PromptHint / LearningOrder field addition if actually missing
formal 972-note import using existing Klose Vocabulary Note Type
state-aware New-card suspension / Reposition
Desktop / AnkiWeb / iPad sync
NEXT.md checkpoint of observed Anki state
```

当前禁止：

```text
manual edit of generated publish files
renumber/reuse of Stable NoteIDs
rewrite/removal of historical Release rows
new/duplicate Klose Vocabulary Note Type or Card Type
bulk resetting Learning/Review Cards to match repo curriculum
changing FSRS / Review History / Due from GitHub-side content operations
silent deletion/rewrite of Grade 5 Lower / Grade 6 Lower provenance evidence
third-party merge/allocation
ExpressionID allocation mixed into Vocabulary Anki update
claiming Anki Updated before actual import/sync is observed
```

## 8. Expressions / third-party hold

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
