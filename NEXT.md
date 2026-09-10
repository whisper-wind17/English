# NEXT — Klose Learning

Last updated: 2026-09-10

## 1. 启动顺序

所有 Klose 任务固定读取：`AGENTS.md → NEXT.md → 当前任务 docs → source_freeze.json → stage_a_status.json → next_batch.json → premerge/readiness.json → premerge/reconciliation_next_batch.json`。动态进度以 machine state 为准。

当前任务文档：`docs/THIRD_PARTY_STAGE_B_RECONCILIATION.md`（Stage-B read-only reconciliation 已闭合，作为规则与历史审计参考）。

## 2. Current phase

```text
Phase A1 Source Adapter Bulk Ingestion = CLOSED
SOURCE FREEZE                         = ESTABLISHED
Phase A2 Global Identity Closure      = CLOSED
Stage B Identity Reconciliation       = CLOSED (read-only premerge work complete)
Merge / Stable NoteID allocation      = GATED / WAITING FOR USER
Klose learning vocabulary mutation    = NOT STARTED
```

用户明确要求：**暂不合并第三方词库进入 Klose 当前学习词库。** 在收到新的显式合并指令前，不得 mint StableThirdPartyID/NoteID，不得修改 Klose Master/Learner/Release/Publish/Anki。

SOURCE FREEZE：20 adapters / 18887 occurrences / 3763 normalized surfaces；source fingerprints 未变化。

## 3. Final Stage-A seal — cardinal / ordinal admitted

Current sealed Stage-A machine state：

```text
Stage-A workflow                   = #443 / 34425589766 = SUCCESS
Stage-A checkpoint                 = c6083db4da4437a77fa9b9723ffb510bd11e6ecc34f8184e8bc8d578ce4659cd
Source occurrences                 = 18887
Normalized surfaces                = 3763
Durable Identity decisions         = 3871
Identity Vocabulary Preview        = 2820
Learner Vocabulary Preview         = 2794
Review blockers                    = 52
Evidence-changed surfaces          = 0
Multipart resolved                 = 15
Grammar-form quarantine gates      = 88
NextBatch SelectedCount            = 0
NextBatch ExecutionReady           = false
```

### Learner content policy

Current explicit content exclusion is only:

```text
a / an / the                       = 3 identities excluded
cardinal / ordinal number units    = ADMITTED
```

用户于 2026-09-10 明确要求将此前排除的 **71 个基数词/序数词重新加入第三方 learner vocabulary**。该政策已通过完整 Stage-A learner gate / Completion Recheck / seal。

`learner/content_exclusion_policy.csv` 现在仅包含 `article:a / article:an / article:the`；`content_exclusion_view.csv` 也只剩这 3 条。数字 classifier 仍作为 adversarial guard：用于确认 elementary cardinal/ordinal identities 必须进入 learner preview，而不是作为 exclusion rule；`number`、`phone number`、`one day` 等独立 lexical/expression units 继续不受误判。

当前 Identity Preview 2820，Learner Preview 2794，因此总 learner-excluded identities = 26；其中 3 条来自当前 content policy，其余 23 条来自既有其他 learner gates。不要把这些与 52 个 Stage-A audited-defer surface 混为一谈。

Residual 52 Stage-A blockers 均为 current-context audited-defer，属于显式有效 hold，不是 active unprocessed work；不得为追求 blocker=0 猜义。

## 4. Stage-B final reconciliation checkpoint

Learner policy 改变导致 Stage-A checkpoint 从旧的 `02bec123...` 变为 `c6083db4...`，因此旧的 2820 条 reconciliation decisions 按规则全部失效；本轮重新在当前 checkpoint 下闭合。

Final reconciliation workflow：**#68 / 34426580726 = SUCCESS**

Final bot persist commit：`7a6ca633fb00e8eb4ffcb5484ede62d149925c1e`

Current machine state：

```text
StageACheckpointFingerprint        = c6083db4da4437a77fa9b9723ffb510bd11e6ecc34f8184e8bc8d578ce4659cd
CandidateCount                     = 2820
ValidDurableDecisionCount          = 2820
ReviewQueueCount                   = 0
SelectedCount                      = 0
ReviewLane                         = <none>
ExecutionReady                     = false
AutoExecutable                     = false
StageBMutationAuthorized           = false
StableThirdPartyIDMinted           = false
MergeAuthorizedRows                = 0
```

Final durable action distribution：

```text
reuse-existing                     = 719
new-stable-identity proposal       = 2021
held                               = 80
TOTAL                              = 2820
```

Interpretation：
- `reuse-existing` 只确认第三方 identity 与某个现有 Klose Stable NoteID 属于同一 learning unit；未修改 NoteID。
- `new-stable-identity` 只是未来 allocation proposal；**没有分配 NoteID**。
- `held` 是完整 reconciliation 结果，表示当前不能安全一对一合并，或现有 identity boundary 需要后续治理；不是遗漏。
- 当前 26 个 learner-excluded identities 在 Stage B 保持 held，不进入 allocation。

### Checkpoint-change revalidation

为避免 learner-policy 小改动后机械重审全部 2820 条，同时又不能静默继承旧判断，Stage-B 增加了 exact historical revalidation：

```text
same ProvisionalIdentityKey
+ byte-for-byte identical CandidateFingerprint
+ historical MutationAuthorized=no
→ 可把历史 decision 重新绑定当前 Stage-A checkpoint
```

只要 CandidateFingerprint 有任何变化，就必须进入显式 review。本次数词重新 admitted 后，发生变化的 number identities按当前 candidate evidence重新审核，其余语义未变化的历史 decision 通过上述规则重签。该机制不授权 merge，也不分配 NoteID。

## 5. Final validation evidence

Stage-B #68 Completion Recheck：

```text
reconciliation closure             = 2820 / 2820
review queue                        = 0
selected review batch              = 0
high-risk multiple coverage        = 5 / 5
all decisions current-fingerprint  = yes
learner-excluded held              = 26
Stable NoteID minted               = no
Stage-B mutation authorized        = no
Merge authorized                   = no
Klose identity/learner/release/Anki isolation = pass
```

独立 post-persist recheck：
- `stage_a_status.json` = 2820 Identity / 2794 Learner / checkpoint `c6083db4...`；
- `content_exclusion_view.csv` = exactly `a / an / the`；
- `reconciliation_next_batch.json` = 2820 decisions / queue 0 / selected 0；
- queue 与 selected-view 均只有 header；
- final bot persist diff 仅修改 `third_party_vocabulary/premerge/**`、`third_party_vocabulary/reconciliation/**` 并删除 transient `reviewed_batch.csv`；
- 未修改 `anki/klose/master/**`、`anki/klose/learner/**`、`anki/klose/publish/**`、`anki/klose/anki/**`。

## 6. HOLD POINT — wait before merge

合并前工作再次闭合。**下一步不是自动合并。** 在用户明确要求开始 merge / allocation 之前，保持：

```text
Stage B reconciliation truth       = frozen/current
Stable NoteID allocation           = prohibited
Klose Master mutation              = prohibited
Klose Learner/Release mutation     = prohibited
Publish regeneration for merge     = prohibited
Anki update                        = prohibited
```

未来若用户明确启动合并，必须先设计并审核新的 allocation/migration gate，消费当前 100% reconciliation decision set；仍需保护 Stable NoteID 和既有 Anki FSRS / Review History，且不能把 `held` 或 current learner-excluded identities 静默带入学习词库。
