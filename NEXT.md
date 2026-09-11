# NEXT — Klose Learning

Last updated: 2026-09-11

## 1. Current task

Grade 5–6 current Vocabulary 已完成 GitHub Release、972-note Desktop import、Learning Admission / LearningOrder materialization 与设备同步，并已 **CHECKPOINTED**。

Grade 5–6 Expressions 的 GitHub identity / learner / review / release lane 也已完成并 **CHECKPOINTED**；当前尚未完成的是 Anki Desktop 实际导入与设备同步。

当前状态：

```text
Vocabulary GitHub Release   = IMPLEMENTED / VALIDATED / CHECKPOINTED
Vocabulary Anki Updated     = true / DEVICE IMPORT + SYNC USER-CONFIRMED

Expressions GitHub Release  = IMPLEMENTED / VALIDATED / CHECKPOINTED
Expressions Release Gate    = PASS
Expressions Anki Updated    = false / DESKTOP IMPORT PENDING
```

当前主任务因此切换为：

```text
Grade 5–6 Expressions Anki Desktop import
→ validate existing/new card state
→ only materialize New # for still-new cards if needed
→ Desktop -> AnkiWeb -> device sync
→ final Expressions Anki checkpoint
```

启动顺序：

```text
AGENTS.md
→ NEXT.md
→ docs/EXPRESSIONS_SYSTEM.md
→ anki/klose/expressions/anki/README.md
→ anki/klose/expressions/publish/anki-import.csv
→ docs/ANKI_SYNC_WORKFLOW.md
```

不得重新执行 Grade 5–6 Expression identity allocation，也不得用 GitHub curriculum 重建已经进入 FSRS 的现有 Expression Cards。

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

Vocabulary scope：

```text
anki/klose/learner/grade5_6_learning_scope.json
LearnerProfile                           = klose
LearnerLevel                             = 4
ScopeStatus                              = accepted
SourceProvenanceAffectsLearningAdmission = false
StableIdentityAllocationAuthorized       = true
```

Expressions scope：

```text
anki/klose/expressions/learner/grade5_6_learning_scope.json
LearnerProfile                           = klose
LearnerLevel                             = 4
ScopeStatus                              = accepted
SourceProvenanceAffectsLearningAdmission = false
StableIdentityAllocationAuthorized       = true
```

因此继续坚持：

```text
Source Grade 5/6 ≠ LearnerLevel 5/6
Klose current LearnerLevel = 4
```

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

Grade 5–6 new learner presentation / lexical facts 已完成；288 个新 Notes 已进行全量 model semantic review。审校中发现并修正 `grandparent / then / judge / run / off` 五条 learner presentation 问题。

### 3.1 Grade 5–6 Learner Presentation policy — FROZEN FOR CURRENT RELEASE

五、六年级来源词汇按 Klose 当前四年级理解能力生成 learner presentation。目标词本身可以高于四年级，但释义和例句 surrounding language 应尽量保持在 LearnerLevel 4。

本次 288 个 Grade 5–6 新 Stable Notes 的 learner-content gate 已验证：

```text
active new Notes             = 288
bilingual examples           = 288 / 288
unique English examples      = 288 / 288
maximum example length       = 14 tokens
high-risk sense cues checked = 24
later auxiliary vocabulary   = 0
```

Grade 5–6 reused Notes 进入 current learning scope 后同样按 `LearnerLevel=4` 处理；此前已有 11 条 reused learner examples 因辅助词难度过高而被降阶。未来如果提高 LearnerLevel，只升级 Learner Presentation 并重新 review；不得改变 Stable NoteID / Anki Review History。

正式 Vocabulary review / release checkpoint：

```text
approval manifest      = anki/klose/learner/review_approvals/grade5-6-current-v1-model-reviewed.csv
approval merge         = 4e74a910951fd4ed1fe8fc158eeb0632e8145f2c
PR #13 release merge   = 738343e7e03118cf0bcf5b76a14780db3d55a822
release delta          = 334 Notes
release total          = 972
post-merge generated   = 33b2e983efec50a8116bef151848775549ee6f98
```

Release registry 是长期发布真源；`study.csv` / `anki-import.csv` 由正常 Build 从 Release truth 生成，不允许手工维护。

## 4. GitHub validation evidence

### 4.1 Vocabulary

```text
PR #13 Build Klose Vocabulary                    = 34494566746 / PASS
PR #13 Grade 5–6 Current Merge                   = 34494566640 / PASS
main Build Klose Vocabulary                      = 34494909929 / PASS
main Grade 5–6 Current Merge                     = 34494909931 / PASS
main Grade 5–6 Reconciliation Completion         = 34494909937 / PASS
```

### 4.2 Expressions

Grade 5–6 Expressions reconciliation 在 allocation 前已独立 CLOSED / VALIDATED。正式 release 后：

```text
PR #15 merge commit                             = b3c8037d1fa9a85eb1454407fba743d4deed2a4e
branch release validation                       = 34568735308 / PASS
PR #15 pull-request release validation          = 34568924344 / PASS
PR #15 pull-request Vocabulary regression       = 34568924302 / PASS
main Grade 5–6 Reconciliation Completion        = 34568969377 / PASS
```

PR #15 merge 后旧 `Grade 5-6 Expression Reconciliation` workflow 仍假定 Stable Expression registry 固定为 66，因此历史 run `34568969362` 以 `176 != 66` 失败。该失败是 workflow lifecycle transition 缺陷，不是 release data failure。

生命周期修复：

```text
PR #16                                       = Fix Grade 5-6 Expression lifecycle after release
PR #16 head                                  = f89642daeb1ac6871a2f6502ef6e0b641838de9f
PR #16 validation                            = 34574349941 / PASS
PR #16 merge                                 = 0524d76751152693818ea4c67629c38d28b5bd72
main post-hotfix lifecycle validation         = 34574396182 / PASS
```

post-allocation workflow 现在明确：

```text
phase = release
reconciliation truth = frozen
pre-allocation planner / mutation steps = skipped
final check_klose_expressions_release_ready.py = PASS
```

最终 main release gate：

```text
publishable Expressions   = 176
baseline existing KE      = 66
Grade 5–6 new KE          = 110
reused Stable KE groups   = 8
source-only occurrences   = 15
review status             = approved 66 + model-reviewed 110
LearningOrder             = 000001..000176
```

## 5. Vocabulary Anki device checkpoint — CHECKPOINTED

现有 `Klose Vocabulary` Note Type 实际字段：

```text
1  NoteID
2  CanonicalWord
3  Word
4  PromptHint
5  British
6  American
7  MeaningPrimary
8  ExampleSentence
9  ExampleTranslation
10 LearnerLevel
11 LearningOrder
12 Sources
13 SourceBooks
14 UserMemo
```

正式导入契约：

```text
Note Type       = Klose Vocabulary
Deck            = Klose-English::Vocabulary
Existing Notes  = Update
Match scope     = Note Type
Identity        = NoteID
UserMemo        = Nothing / not mapped
```

实际 Vocabulary import：

```text
notes found in file            = 972
new notes imported             = 335
already present / unchanged    = 539
existing notes updated         = 98
final Notes / Cards            = 972 / 972
```

设备侧最终：

```text
25 already Learning / Review
602 current New unsuspended
345 held New suspended
LearningOrder materialized only for current is:new Cards
Desktop -> AnkiWeb sync = completed
Device sync              = completed
Anki Updated             = true
```

未批量修改已经进入 Learning / Review 的 Cards；没有用 GitHub curriculum 重置其 Due / FSRS state。

## 6. Expressions GitHub release — CHECKPOINTED

Grade 5–6 Expressions 已完成从 reconciliation 到正式 Stable identity / learner / release 的状态迁移：

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

第二遍独立内容审查曾发现自动 presentation 中的 slot 截取和教学元语言问题，包括称呼语进入 slot、小数身高被截断等；修复后重新执行完整 release gate 并通过。

当前正式生成文件：

```text
anki/klose/expressions/publish/study.csv       = 176 Expressions
anki/klose/expressions/publish/anki-import.csv = 176 Expressions
```

禁止手工编辑这两个 generated 文件。

## 7. Immediate next work — Expressions Anki import

下一步只进入 Anki Desktop operational lane，不再重新做 identity / reconciliation。

正式导入文件：

```text
anki/klose/expressions/publish/anki-import.csv
```

现有长期契约：

```text
Note Type = Klose Expression
Deck      = Klose-English::Expressions
Card Type = Production
Identity  = ExpressionID
1 Note    = 1 Card
```

导入必须使用现有 Note Type 原地 Update Existing Notes。预期文件结构：

```text
notes in release = 176
existing baseline = 66
new Grade 5–6     = 110
```

这是 repo 预期，不得在用户实际导入前写成 Anki 实测结果。

正式操作顺序：

```text
1. Desktop sync，确保当前 Anki 状态已先同步到本机
2. 检查现有 Klose Expression Note Type / Deck 仍存在
3. 导入 expressions/publish/anki-import.csv
4. Existing Notes = Update；以 ExpressionID 作为稳定 identity
5. 核对实际 imported / updated / unchanged / total counts
6. 核对哪些 Cards 已进入 Learning / Review，哪些仍 is:new
7. 只对仍为 is:new 的新增/当前 Cards 按 LearningOrder 初始化 New #；不得改已学习 Cards
8. Desktop -> AnkiWeb sync
9. iPad/device sync
10. 用户确认后再把 Expressions Anki Updated=true 写入 NEXT.md
```

现有 66 张 Expression Cards 的 FSRS / Review History / Due / Interval / Card State 只能以 Anki 为真源。即使 learner presentation 被更新，也不得删除重建这些 Cards。

## 8. Mutation boundary

当前允许：

```text
Expressions Anki Desktop import / validation / sync
NEXT.md 的 Anki checkpoint 更新
未来基于真实学习反馈修改 Learner Presentation（需 fingerprint re-review）
正常的未来 Vocabulary incremental sync（仅有新 release 时）
```

当前禁止：

```text
rerun / renumber Grade 5–6 Expression Stable allocation
manual edit of generated publish files
renumber/reuse of Stable NoteIDs / ExpressionIDs
rewrite/removal of historical Release rows
new/duplicate Klose Vocabulary or Klose Expression Note Type
bulk resetting Learning/Review Cards to match repo curriculum
changing FSRS / Review History / Due from GitHub-side content operations
silent deletion/rewrite of Grade 5 Lower / Grade 6 Lower provenance evidence
third-party merge/allocation before dedup / identity reconciliation
automatically mixing ExpressionID operations into Vocabulary updates
```

## 9. Third-party hold

第三方词库继续独立冻结：

```text
Stage A/B                  = CLOSED
Vocabulary identities     = 2820
learner candidates        = 2794
actual merge/allocation   = not started
explicit exclusions       = a / an / the
```

第三方数据在合入 Klose 当前学习词表前，必须先与现有 Stable Vocabulary 做去重与 sense-aware identity reconciliation；不得只按 surface word 直接 merge。详细历史见 `docs/THIRD_PARTY_STAGE_B_RECONCILIATION.md`。
