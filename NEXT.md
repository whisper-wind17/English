# NEXT — Klose Learning

Last updated: 2026-09-11

## 1. Current task

Grade 5–6 current Vocabulary 的 GitHub Release、Anki preflight、972-note Desktop import、Learning Admission materialization、LearningOrder Reposition 与设备同步均已完成并 **CHECKPOINTED**。

当前 Vocabulary lane 状态：

```text
GitHub Vocabulary Release = IMPLEMENTED / VALIDATED / CHECKPOINTED
Anki preflight            = PASS / CHECKPOINTED
Anki Updated              = true / DEVICE IMPORT + SYNC USER-CONFIRMED
```

下一主任务恢复为 **Grade 5–6 Expressions 独立 lane**；不得把 ExpressionID allocation / release 与 Vocabulary 或第三方词库 merge 混在一起。

启动顺序：

```text
AGENTS.md
→ NEXT.md
→ docs/EXPRESSIONS_SYSTEM.md
→ Grade 5–6 Expressions reconciliation / review artifacts
→ relevant anki/klose/ Expressions registries and tools
```

Vocabulary / Anki 后续同步继续遵守：

```text
docs/ANKI_CURRENT_RELEASE_IMPORT.md
docs/ANKI_SYNC_WORKFLOW.md
docs/KLOSE_VOCABULARY_SYSTEM.md
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
```

Grade 5–6 new learner presentation / lexical facts 已完成；288 个新 Notes 已进行全量 model semantic review。审校中发现并修正 `grandparent / then / judge / run / off` 五条 learner presentation 问题。

### 3.1 Grade 5–6 Learner Presentation policy — FROZEN FOR CURRENT RELEASE

Grade 5 / 6 是 **Source Grade**；Klose 当前学习这些词时仍使用：

```text
LearnerProfile = klose
LearnerLevel   = 4
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

Grade 5–6 reused Notes 进入 current learning scope 后同样按 `LearnerLevel=4` 处理；此前已有 11 条 reused learner examples 因辅助词难度过高而被降阶。未来如果提高 LearnerLevel，只升级 Learner Presentation 并重新 review；不得改变 Stable NoteID / Anki Review History。

正式 review / release checkpoint：

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

PR #13 与 main post-merge 已完成独立验证：

```text
PR #13 Build Klose Vocabulary                    = 34494566746 / PASS
PR #13 Grade 5–6 Current Merge                   = 34494566640 / PASS
main Build Klose Vocabulary                      = 34494909929 / PASS
main Grade 5–6 Current Merge                     = 34494909931 / PASS
main Grade 5–6 Reconciliation Completion         = 34494909937 / PASS
```

关键 repo state：

```text
released              = 972
current learning      = 627
  grade4              = 221
  grade5_6            = 432
  grade5_6_only       = 406
held                  = 345
LearningOrder         = 000001..000627
review pending        = 0
allowed unreleased    = 0
```

90 个 held legacy Notes 仍缺 British/American IPA；这些 Notes 不在当前 admitted learning set，因此是 library debt，不阻塞 current Vocabulary Release。

## 5. Anki device checkpoint — 2026-09-11 / CHECKPOINTED

### 5.1 Existing Note Type / import contract observed

现有 `Klose Vocabulary` Note Type 已实际检查，字段为：

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

正式 `anki/klose/publish/anki-import.csv` 以如下配置导入：

```text
Note Type       = Klose Vocabulary
Deck            = Klose-English::Vocabulary
Existing Notes  = Update
Match scope     = Note Type
Identity        = NoteID
Tags            = Tags
UserMemo        = Nothing / not mapped
```

### 5.2 Actual import result

Anki Desktop 实际导入结果：

```text
notes found in file            = 972
new notes imported             = 335
already present / unchanged    = 539
existing notes updated         = 98
final Notes / Cards            = 972 / 972
```

`539 + 98 = 637` 个 NoteID 在导入前已存在。当前 release 相对 638-note Grade-4 release 的正式增量为 334，因此设备上额外缺失了 1 个历史 Note；本次导入中确认该历史缺失 Note 为：

```text
NoteID        = KV000433
CanonicalWord = job
LearningOrder = 000002
Added         = 2026-09-11
Reviews       = 0
Lapses        = 0
Card Type     = Recognition
```

它此前未形成 Review History，因此本次补入不涉及 FSRS history 恢复或覆盖。

### 5.3 Actual learning-state materialization

导入后实测：

```text
Total Cards                         = 972
is:new                              = 947
already Learning / Review           = 25

Grade-4 current is:new              = 196
Grade-5/6 current is:new            = 406
current-tag overlap in is:new       = 0
current New total                   = 602

initial suspended New               = 417
of which Grade-5/6 current          = 72
held New                            = 345
```

仅对 `Grade-5/6 current AND is:new AND suspended` 的 72 张执行 Unsuspend；操作后：

```text
current New unsuspended             = 602
held New suspended                  = 345
```

数量闭合：

```text
25 already learned + 602 current New = 627 current learning
627 current + 345 held               = 972 released
```

未批量修改已经进入 Learning / Review 的 25 张 Cards；没有用 GitHub curriculum 重置其 Due / FSRS state。

### 5.4 LearningOrder -> New Card Position

仅选择：

```text
deck:"Klose-English::Vocabulary" is:new -is:suspended
```

共 602 张 current New Cards。Browser Sort Field 使用 `LearningOrder`，升序后起始序列实测为：

```text
000002
000027
000028
000029
...
```

这与 25 张 current Cards 已离开 New 状态一致。

执行 Reposition：

```text
Start position = 1
Step           = 1
Randomize      = OFF
Shift existing = ON
```

执行后 current New Cards 按 `LearningOrder` materialize 为连续 `New #1..#602`；345 张 held New Cards 继续 suspended。

### 5.5 Sync

用户已确认完成同步。当前 checkpoint 记录：

```text
Desktop import / validation   = completed
Desktop -> AnkiWeb sync       = user-confirmed completed
device sync                   = user-confirmed completed
Anki Updated                  = true
```

本轮没有创建第二个 Note Type / Card Type，没有重建 Stable NoteID，没有从 repo 覆盖 FSRS / Review History / Due。

## 6. Immediate next work

Vocabulary 当前 release 已完成，不再重复执行 972-note import / suspension reset / Reposition。

下一任务进入 **Grade 5–6 Expressions 独立 lane**：

```text
1. 读取 docs/EXPRESSIONS_SYSTEM.md 与已完成 reconciliation artifacts
2. 对 110 个 new stable proposal groups 做 Stable ExpressionID allocation 前 recheck
3. 保留 8 个 existing Stable KE groups reuse
4. 不把 source-only / non-card material 机械转成 Cards
5. 完成 learner presentation / review / admission / release gate
6. 只有 Expressions release 独立通过后，才进入其 Anki import/sync
```

若在此之前用户显式切换到第三方词库任务，则先从冻结的 Stage A/B 状态继续，仍不得直接 merge/allocation；必须先按现有 Stable Vocabulary 做 dedup / identity reconciliation。

## 7. Mutation boundary

当前允许：

```text
Grade 5–6 Expressions 独立 identity / learner / review / release 工作
NEXT.md 后续 checkpoint
正常的未来 Vocabulary incremental sync（有新 release 时）
```

当前禁止：

```text
manual edit of generated publish files
renumber/reuse of Stable NoteIDs / ExpressionIDs
rewrite/removal of historical Release rows
new/duplicate Klose Vocabulary Note Type or Card Type
bulk resetting Learning/Review Cards to match repo curriculum
changing FSRS / Review History / Due from GitHub-side content operations
silent deletion/rewrite of Grade 5 Lower / Grade 6 Lower provenance evidence
third-party merge/allocation before dedup / identity reconciliation
automatically mixing ExpressionID allocation into Vocabulary updates
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

第三方词库继续独立冻结：

```text
Stage A/B                  = CLOSED
Vocabulary identities     = 2820
learner candidates        = 2794
actual merge/allocation   = not started
explicit exclusions       = a / an / the
```

第三方数据在合入 Klose 当前学习词表前，必须先与现有 Stable Vocabulary 做去重与 sense-aware identity reconciliation；不得只按 surface word 直接 merge。详细历史见 `docs/THIRD_PARTY_STAGE_B_RECONCILIATION.md`。
