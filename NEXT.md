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

## 3. Final Stage-A seal after learner-content exclusion

Current sealed Stage-A machine state：

```text
Stage-A checkpoint                 = 02bec1239e717f8f9141c38cec2fa16947f9c16a6ec372478db26936c5451b0f
Source occurrences                 = 18887
Normalized surfaces                = 3763
Durable Identity decisions         = 3871
Identity Vocabulary Preview        = 2820
Learner Vocabulary Preview         = 2723
Review blockers                    = 52
Evidence-changed surfaces          = 0
Multipart resolved                 = 15
Grammar-form quarantine gates      = 88
NextBatch SelectedCount            = 0
NextBatch ExecutionReady           = false
```

### Learner content exclusion

按用户要求，第三方 Identity 真源保留，但以下内容不进入当前第三方 learner vocabulary：

```text
a / an / the                       = 3 identities excluded
number / ordinal learning units    = 71 identities excluded
user-requested simple exclusions   = 74 total
```

规则位于 `learner/content_exclusion_policy.csv`；派生证据位于 `learner/content_exclusion_view.csv`。数字规则只排除纯 cardinal / ordinal learning units，不误伤 `number`、`phone number`、`one day` 等独立 lexical/expression units。

`2820 - 2723 = 97` 个当前 learner-excluded identities 中，除上述 74 个外还包含既有 learner-policy exclusions（例如 grammar-form quarantine）；这些层次不得混为一谈。

Residual 52 Stage-A blockers 均为 current-context audited-defer，属于显式有效 hold，不是 active unprocessed work；不得为追求 blocker=0 猜义。

## 4. Stage-B final reconciliation checkpoint

Final reconciliation workflow：**#56 / 34420414777 = SUCCESS**

Final bot persist commit：`5b6936852a48abc3df337ada35666d357c5e9dd4`

Current machine state：

```text
StageACheckpointFingerprint        = 02bec1239e717f8f9141c38cec2fa16947f9c16a6ec372478db26936c5451b0f
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
reuse-existing                     = 692
new-stable-identity proposal       = 1977
held                               = 151
TOTAL                              = 2820
```

Interpretation：
- `reuse-existing` 只是确认与现有 Klose Stable NoteID 属于同一 learning unit；未修改该 NoteID。
- `new-stable-identity` 只是未来 allocation proposal；**没有分配 NoteID**。
- `held` 是完整 reconciliation 结果，表示当前不能安全一对一合并，或 Klose 现有 identity 本身有 mixed-sense boundary；不是遗漏。
- 97 个当前 learner-excluded identities 在 Stage B 全部保持 `held`，不绑定 ExistingNoteID、不提出 allocation。

## 5. Final validation evidence

Stage-B Completion Recheck 已在最终 batch 后 PASS：

```text
reconciliation closure             = 2820 / 2820
review queue                        = 0
selected review batch               = 0
high-risk multiple coverage         = 5 / 5
all decisions current-fingerprint   = yes
Stable NoteID minted                = no
Stage-B mutation authorized         = no
Merge authorized                    = no
Klose identity/learner/release/Anki isolation = pass
```

独立 post-persist recheck：
- current `reconciliation_next_batch.json` = 2820 decisions / queue 0 / selected 0；
- current queue 与 selected-view 均只有 header；
- final batch persist diff 仅修改 `third_party_vocabulary/premerge/**`、`third_party_vocabulary/reconciliation/**` 并移除 transient reviewed batch；
- 从 current Stage-B 起点到 final bot commit 的整体 diff 没有修改 `anki/klose/master/**`、`anki/klose/learner/**`、`anki/klose/publish/**`、`anki/klose/anki/**`；
- learner content exclusion view 仍为 74 条 user-requested exclusion records（3 articles + 71 number/ordinal）。

## 6. HOLD POINT — wait before merge

合并前工作已闭合。**下一步不是自动合并。** 在用户明确要求开始 merge / allocation 之前，保持：

```text
Stage B reconciliation truth       = frozen/current
Stable NoteID allocation           = prohibited
Klose Master mutation              = prohibited
Klose Learner/Release mutation     = prohibited
Publish regeneration for merge     = prohibited
Anki update                        = prohibited
```

如果未来用户明确启动合并，必须先设计并审核一个新的 allocation/migration gate，消费当前 100% reconciliation decision set；仍需保护 Stable NoteID 和既有 Anki FSRS / Review History，且不能把 `held` 或 current learner-excluded identities 静默带入学习词库。
