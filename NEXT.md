# NEXT — Klose Learning

Last updated: 2026-09-11

## 1. Current checkpoint

Grade 5–6 Vocabulary、Grade 5–6 Expressions、第三方 Vocabulary Stage-B reconciliation，以及第三方 allocation / migration plan 均已完成当前阶段，并已 **CHECKPOINTED**。

```text
Vocabulary GitHub Release       = IMPLEMENTED / VALIDATED / CHECKPOINTED
Vocabulary Anki Updated         = true / DEVICE IMPORT + SYNC USER-CONFIRMED

Expressions GitHub Release      = IMPLEMENTED / VALIDATED / CHECKPOINTED
Expressions Release Gate        = PASS
Expressions Anki Updated        = true / DEVICE IMPORT + SYNC USER-CONFIRMED

Third-party Stage-B             = IMPLEMENTED / VALIDATED / CHECKPOINTED
Third-party reconciliation      = 2820 / 2820

Third-party allocation plan     = IMPLEMENTED / VALIDATED / CHECKPOINTED
Third-party merge/allocation    = NOT AUTHORIZED / NOT STARTED
```

第三方 allocation/migration plan 已绑定当前 **1189 个 active Stable Vocabulary NoteIDs** 与闭合的 2820 条 Stage-B decision。当前唯一下一主任务是 **third-party Source provenance / SourceEdition contract design**：20 个第三方 adapter occurrence 当前没有 `SourceEdition`，因此不得伪造教材版本写入 Master provenance。`MasterSourceMappingMutationAuthorized=false`，实际 Stable NoteID allocation 也继续保持未授权。

启动顺序：

```text
AGENTS.md
→ NEXT.md
→ docs/THIRD_PARTY_ALLOCATION_MIGRATION_PLAN.md
→ docs/SOURCE_RECONCILIATION.md
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

---

## 7. Third-party allocation / migration plan — CHECKPOINTED

计划真源：

```text
docs/THIRD_PARTY_ALLOCATION_MIGRATION_PLAN.md
anki/klose/third_party_vocabulary/allocation/plan.json
tools/check_third_party_allocation_plan.py
.github/workflows/third-party-allocation-plan.yml
```

计划已绑定当前 Stage-B 与 Stable Registry 的 exact Git blob SHA。当前 baseline：

```text
persistent registry rows      = 1194
active Stable NoteIDs         = 1189
max NoteID                    = KV001194
reuse-existing                = 903
new-stable-identity proposal  = 1821
held                          = 96
```

1821 个 proposal 若未来在同一冻结 registry 上被明确授权执行，理论 append-only 区间为：

```text
KV001195..KV003015
```

该区间 **NOT RESERVED**；任何 Stable Registry 变化都会令 plan stale，并要求重新计算。903 个 reuse 不得改 Stable Registry，96 个 held 不得 allocation / merge。

Validation evidence：

```text
initial allocation-plan validation        = 34584336799 / PASS
Stage-A trigger isolation fix             = b8883e1b4d801567ae46decf503ea9a168cdd807
post-fix full Stage-A recheck             = 34584514294 / PASS
post-fix Stage-A seal metadata commit     = fd9ca00301b683e8741fbd20a39c91ea35dfbb8a
final plan validation after doc checkpoint = 34584719664 / PASS
```

独立 adversarial recheck 曾发现：Stage-A workflow 的 `tools/check_third_party_*.py` 路径过宽，会把 allocation-plan checker 误当作 Stage-A input，导致无内容变化时重复 reseal metadata。已加入 `!tools/check_third_party_allocation_plan.py` 排除；修复后完整 Stage-A 验证通过，Stage-A content fingerprint 与 checkpoint `c6083...` 均未变化。

### Current blocker — Source provenance / SourceEdition

20 个第三方 source adapter 的标准 occurrence schema 当前不包含 `SourceEdition`，而 Master source mapping 以：

```text
SourceID + SourceEdition + SourceItemKey + NoteID
```

为 provenance identity。因此不得根据文件名、年级或第三方整理数据猜测 `2024-revision / pre-2024-revision / klose-current`。

下一主任务只做 **third-party Source provenance / SourceEdition contract design**，需要决定：

```text
A. 从可验证 source evidence 补真实 SourceEdition / Revision
或
B. 在 source model 中显式建模 unknown / unverified edition，且语义不能冒充教材版本事实
```

在此 contract VALIDATED / CHECKPOINTED 前：

```text
MasterSourceMappingMutationAuthorized = false
StableNoteIDAllocationAuthorized      = false
```

即使 provenance contract 之后完成，实际 allocator 仍需独立 IMPLEMENTED / VALIDATED，并且用户必须显式授权实际 mutation 后才可执行。

---

## 8. Mutation boundary

当前允许：

```text
third-party Source provenance / SourceEdition contract design
read-only allocation plan validation / statistics / adversarial review
third-party reconciliation / allocation-plan documentation / audit state
NEXT.md checkpoint
未来基于真实学习反馈修改 Learner Presentation（需 fingerprint re-review）
正常的未来 Vocabulary / Expressions incremental release（只有明确新 release 时）
```

当前禁止：

```text
actual third-party Stable NoteID allocation / merge without explicit authorization
master third-party source mapping mutation before SourceEdition contract closes
inventing SourceEdition / Revision from filename, grade, or third-party organizer labels
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

Current allocation mutation gates：

```text
ActualMutationAuthorized              = false
StableNoteIDAllocationAuthorized      = false
MasterSourceMappingMutationAuthorized = false
LearnerMutationAuthorized             = false
ReleaseMutationAuthorized             = false
PublishMutationAuthorized             = false
AnkiMutationAuthorized                = false
```
