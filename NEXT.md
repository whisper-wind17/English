# NEXT — Klose Learning

Last updated: 2026-09-11

## 1. Current checkpoint

Grade 5–6 Vocabulary、Grade 5–6 Expressions 与第三方 Vocabulary sense-aware Stage-B reconciliation 均已完成当前阶段，并已 **CHECKPOINTED**。

```text
Vocabulary GitHub Release       = IMPLEMENTED / VALIDATED / CHECKPOINTED
Vocabulary Anki Updated         = true / DEVICE IMPORT + SYNC USER-CONFIRMED

Expressions GitHub Release      = IMPLEMENTED / VALIDATED / CHECKPOINTED
Expressions Release Gate        = PASS
Expressions Anki Updated        = true / DEVICE IMPORT + SYNC USER-CONFIRMED

Third-party Stage-B             = IMPLEMENTED / VALIDATED / CHECKPOINTED
Third-party reconciliation      = 2820 / 2820
Third-party merge/allocation    = NOT AUTHORIZED / NOT STARTED
```

第三方 Stage-B 已重新针对当前 **1189 个 active Stable Vocabulary NoteIDs** 完成 reconciliation。下一主任务只能是 **third-party allocation / migration plan**：先定义 903 个 reuse、1821 个 future-new proposal 与 96 个 held 的后续处理和 mutation gate；在用户明确授权实际 merge/allocation 之前，不写 Klose Stable Registry、不改变 972-note 当前 release、不修改 Anki。

启动顺序：

```text
AGENTS.md
→ NEXT.md
→ docs/THIRD_PARTY_STAGE_B_RECONCILIATION.md
→ docs/KLOSE_VOCABULARY_SYSTEM.md
→ current Stable Vocabulary registries
→ closed third-party Stage A/B reconciliation truth
```

---

## 2. Decision reconciliation

Grade 5–6 Source provenance 与 Klose Learning Scope 必须分开理解。

Source provenance 继续保持：

```text
Grade 5 Upper  = 2024-revision / verified-current-revision
Grade 5 Lower  = pre-2024-revision / verified-legacy-source-current-revision-mismatch
Grade 6 Upper  = 2024-revision / verified-current-revision
Grade 6 Lower  = pre-2024-revision / verified-legacy-source-hold-for-klose-future-edition
```

这些状态继续作为 Source Fact / audit truth，不得静默改写或删除。

用户已显式接受 captured Grade 5–6 学习范围。Vocabulary 与 Expressions 均允许在独立 learning-scope contract 下进入当前学习，但 SourceEdition 仍只描述真实来源版本，不因 Learning Admission 而改写。

```text
Vocabulary scope:
anki/klose/learner/grade5_6_learning_scope.json

Expressions scope:
anki/klose/expressions/learner/grade5_6_learning_scope.json

LearnerProfile                           = klose
LearnerLevel                             = 4
ScopeStatus                              = accepted
SourceProvenanceAffectsLearningAdmission = false
StableIdentityAllocationAuthorized       = true
```

继续坚持：

```text
Source Grade 5/6 ≠ LearnerLevel 5/6
Klose current LearnerLevel = 4
```

---

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
learner review scope                                = 972
model-reviewed                                      = 972
human-reviewed                                      = 0
pending                                             = 0

publish/study.csv                                   = 972 Notes
publish/anki-import.csv                             = 972 Notes
```

Grade 5–6 learner presentation 已按 `LearnerLevel=4` 审校。288 个新 Notes 全量 model semantic review；曾修正 `grandparent / then / judge / run / off` 五条问题。Grade 5–6 reused Notes 中另有 11 条 example 因辅助词难度过高而降阶。

Vocabulary release checkpoint：

```text
approval manifest      = anki/klose/learner/review_approvals/grade5-6-current-v1-model-reviewed.csv
approval merge         = 4e74a910951fd4ed1fe8fc158eeb0632e8145f2c
PR #13 release merge   = 738343e7e03118cf0bcf5b76a14780db3d55a822
release delta          = 334 Notes
release total          = 972
post-merge generated   = 33b2e983efec50a8116bef151848775549ee6f98
```

### Vocabulary Anki device checkpoint

正式导入：

```text
notes found in file            = 972
new notes imported             = 335
already present / unchanged    = 539
existing notes updated         = 98
final Notes / Cards            = 972 / 972
```

设备最终状态：

```text
25 already Learning / Review
602 current New unsuspended
345 held New suspended
LearningOrder materialized only for current is:new Cards
Desktop -> AnkiWeb sync = completed
Device sync              = completed
Anki Updated             = true
```

没有用 GitHub curriculum 重置已进入 Learning / Review 的 Cards；FSRS / Review History / Due 仍以 Anki 为真源。

---

## 4. Expressions release — CHECKPOINTED

Grade 5–6 Expressions reconciliation / identity / learner / review / release 已完成：

```text
source occurrences reviewed              = 153 / 153
mapped                                   = 138
source-only                              = 15
existing Stable KE groups reused         = 8
new Stable Expressions allocated         = 110
new ExpressionID range                   = KE000067..KE000176
Stable Expression registry total         = 176
pending / stale reconciliation           = 0 / 0
```

110 个新 Expressions 均为 append-only allocation；原有 `KE000001..KE000066` 未重编号、未复用、未删除。

Learner Presentation：

```text
LearnerProfile             = klose
LearnerLevel               = 4
Front policy               = Stage A intent/situation + English minimal cue
new learner rows           = 110
concrete textbook Targets  = 110 / 110
unresolved target slots    = 0
learner-facing meta jargon = 0
```

第二遍独立内容审查曾发现自动 presentation 的 slot 截取和教学元语言问题，包括称呼语进入 slot、小数身高被截断等；修复后重新执行完整 release gate并通过。

正式生成文件：

```text
anki/klose/expressions/publish/study.csv        = 176 Expressions
anki/klose/expressions/publish/anki-import.csv = 176 Expressions
```

禁止手工编辑 generated publish 文件。

### GitHub validation evidence

```text
PR #15 merge commit                             = b3c8037d1fa9a85eb1454407fba743d4deed2a4e
branch release validation                       = 34568735308 / PASS
PR #15 pull-request release validation          = 34568924344 / PASS
PR #15 pull-request Vocabulary regression       = 34568924302 / PASS
main Grade 5–6 Reconciliation Completion        = 34568969377 / PASS
```

PR #15 后旧 Expression reconciliation workflow 曾因固定假定 registry=66 而在 run `34568969362` 失败；这是 lifecycle transition 缺陷，不是 release data failure。已由 PR #16 修复：

```text
PR #16 validation                            = 34574349941 / PASS
PR #16 merge                                 = 0524d76751152693818ea4c67629c38d28b5bd72
main post-hotfix lifecycle validation         = 34574396182 / PASS
phase                                         = release
pre-allocation planner / mutation steps       = skipped
final Expression Release Gate                 = PASS
```

最终 Release Gate：

```text
publishable Expressions   = 176
baseline existing KE      = 66
Grade 5–6 new KE          = 110
reused Stable KE groups   = 8
source-only occurrences   = 15
review status             = approved 66 + model-reviewed 110
LearningOrder             = 000001..000176
```

---

## 5. Expressions Anki device checkpoint — CHECKPOINTED

长期契约保持：

```text
Note Type = Klose Expression
Deck      = Klose-English::Expressions
Card Type = Production
Identity  = ExpressionID
1 Note    = 1 Card
```

2026-09-11 实际导入 `anki/klose/expressions/publish/anki-import.csv`：

```text
notes found in file            = 176
new notes imported             = 110
already present / unchanged    = 54
existing notes updated         = 12
final Notes / Cards            = 176 / 176
```

数量闭合：

```text
54 unchanged + 12 updated = 66 existing Stable Expression notes
66 existing + 110 new     = 176 total
```

导入后实际 Card State：

```text
Total Cards                         = 176
is:new                              = 170
already Learning / Review           = 6
suspended                           = 0
```

仅对：

```text
deck:"Klose-English::Expressions" is:new
```

共 170 张 Cards 按 `LearningOrder` 升序执行 Reposition：

```text
Start position = 1
Step           = 1
Randomize      = OFF
Shift existing = ON
```

用户确认 Reposition 后：

```text
current New Cards = 170
New #             = 1..170
```

6 张已进入 Learning / Review 的 Cards 未参与 Reposition；没有重建或覆盖其 FSRS / Review History / Due / Interval。

同步 checkpoint：

```text
Desktop import / validation   = completed
New-card reposition           = completed
Desktop -> AnkiWeb sync       = user-confirmed completed
device / iPad sync            = user-confirmed completed
Expressions Anki Updated      = true
```

至此 Grade 5–6 Expressions 从 Source → Stable ExpressionID → Learner Presentation → Release → Anki → Device Sync 的本轮闭环完成。

---

## 6. Third-party Vocabulary Stage-B — CHECKPOINTED

Stage A 保持 sealed：

```text
StageACheckpointFingerprint = c6083db4da4437a77fa9b9723ffb510bd11e6ecc34f8184e8bc8d578ce4659cd
source occurrences          = 18887
Vocabulary identities       = 2820
learner candidates          = 2794
audited deferred surfaces   = 52
explicit exclusions         = a / an / the
```

Grade 5–6 Vocabulary allocation 后 Stable active Notes 从 901 增至 1189。旧 Stage-B snapshot 没有自动刷新，原因是 Stable allocation 由 `GITHUB_TOKEN` bot commit 产生，普通 `push` workflow 不会递归触发。已修复 Stage-B readiness lifecycle：增加 Stable Vocabulary allocation/build 的 `workflow_run` 触发。

```text
lifecycle fix commit        = 36d420ee127c8cb7be680f58e621a08e68faa706
refreshed premerge commit   = 6452c351c65d3cbf4f75986b6ad469d13c3978a7
Klose active NoteIDs        = 1189
changed CandidateFingerprint rows = 218
unchanged historical decisions    = 2602
```

当前 premerge candidate distribution：

```text
exact-multiple        = 17
exact-single          = 974
no-existing-match     = 1822
orthographic-single   = 6
spelling-single       = 1
TOTAL                 = 2820
```

218 个 stale decisions 全部先失效，再按当前 evidence 重审；没有利用旧 901-NoteID 边界强行 carry-forward。最终 Stage-B：

```text
reconciliation workflow run = #75 / 34581146513 / PASS
bot persist commit           = 153dfabd258eafc039d8545c1ffd1e77f1a362ca

ValidDurableDecisionCount    = 2820
ReviewQueueCount             = 0
SelectedCount                = 0
reuse-existing               = 903
new-stable-identity proposal = 1821
held                         = 96
high-risk multiple decided   = 17 / 17
learner-excluded held        = 26 / 26
```

Completion Recheck：

```text
all durable rows current-fingerprint bound = yes
Stable NoteID minted                       = no
Stage-B mutation authorized                = no
Merge authorized                           = no
Klose identity/learner/release/Anki isolation = pass
```

典型 sense-aware 决策：`take=拿/取/带走`、`heavy=重的`、`turn=转动`、`way=道路/方向` 不因同拼写而复用错误的现有 sense；`paint / email / Spanish / open` 等 Stage-A 混合义项保持 `held`。详细真源见 `docs/THIRD_PARTY_STAGE_B_RECONCILIATION.md`。

### Immediate next work — allocation / migration plan only

Stage-B read-only reconciliation 已 CLOSED，但 actual merge/allocation **尚未授权**。下一阶段若继续，应先形成可验证的 allocation/migration plan，至少定义：

```text
903 reuse-existing
→ 如何写 provenance / source mapping，且不改 Stable NoteID identity

1821 new-stable-identity proposals
→ 哪些允许进入 allocation candidate set
→ append-only NoteID allocation order / rollback / idempotency
→ Learner Admission 与 identity allocation 继续分离

96 held
→ 保持 held；不得自动 allocation / merge
```

计划还必须明确 mutation scope、stable identity diff、release isolation、rollback/retry、未来 Learner Presentation / review / admission / release 的独立 gate。在 plan VALIDATED / CHECKPOINTED 且用户明确授权实际 mutation 前，不执行 Stable NoteID allocation。

---

## 7. Mutation boundary

当前允许：

```text
third-party allocation / migration plan design
read-only validation / statistics / adversarial review
third-party reconciliation documentation / audit state
NEXT.md checkpoint
未来基于真实学习反馈修改 Learner Presentation（需 fingerprint re-review）
正常的未来 Vocabulary / Expressions incremental release（只有明确新 release 时）
```

当前禁止：

```text
actual third-party Stable NoteID allocation / merge without explicit authorization
turning held rows into automatic allocation or reuse
surface-word-only dedup when senses differ
manual edit of generated publish files
renumber/reuse of Stable NoteIDs / ExpressionIDs
rewrite/removal of historical Release rows
rerun / renumber Grade 5–6 Expression Stable allocation
new/duplicate Klose Vocabulary or Klose Expression Note Type
bulk resetting Learning/Review Cards to match repo curriculum
changing FSRS / Review History / Due from GitHub-side content operations
silent deletion/rewrite of Grade 5 Lower / Grade 6 Lower provenance evidence
automatically mixing ExpressionID operations into Vocabulary updates
```
