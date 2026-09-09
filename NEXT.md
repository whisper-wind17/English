# NEXT — Klose Learning

Last updated: 2026-09-10

## 1. 启动顺序

所有 Klose 任务固定读取：

```text
AGENTS.md
→ NEXT.md
→ docs/THIRD_PARTY_SOURCE_FIRST_EXECUTION.md
→ docs/THIRD_PARTY_VOCABULARY_MINIMAL_IDENTITY.md
→ docs/THIRD_PARTY_VOCABULARY_CORPUS.md
→ docs/THIRD_PARTY_VOCABULARY_REVIEW_POLICY.md
→ docs/SOURCE_RECONCILIATION.md
→ docs/THIRD_PARTY_STAGE_B_RECONCILIATION.md
→ anki/klose/third_party_vocabulary/config/source_freeze.json
→ anki/klose/third_party_vocabulary/audit/stage_a_status.json
→ anki/klose/third_party_vocabulary/audit/next_batch.json
→ anki/klose/third_party_vocabulary/premerge/readiness.json
```

动态进度以 repo 当前 machine state 为准；`stage_a_status.json` / `next_batch.json` 高于本文件静态快照。

---

## 2. Current phase

```text
Phase A1 — Source Adapter Bulk Ingestion = CLOSED
→ SOURCE FREEZE                         = ESTABLISHED
→ Phase A2 — Global Identity Closure     = CURRENT
→ final Stage-A seal
→ Stage B / Klose reconciliation
```

SOURCE FREEZE 后不得静默修改 source adapters、adapter occurrences 或 raw-source interpretation；确需 Source 修正必须显式 reopen freeze 并重新通过 Source gate。

---

## 3. SOURCE FREEZE — CLOSED

```text
enabled adapters                     = 20
source occurrences                   = 18887
normalized surfaces                  = 3763
source books                         = 178
blank Definition source facts        = 13
cross-adapter occurrence collision   = 0
dedicated prepare/check              = 20 / 20
source_adapters.csv SHA-256           = fdf79e5f48ed77d543dc05f3d347c3ce03d406e4884c89a426fdac8fa20e8272
unified occurrences SHA-256           = b025cb4f69b030da3664ab9b1bdd8500cb0166b122392b282a4293567702a7d4
Klose operational mutation           = 0
```

Terminal source boundaries：仁爱版 grades 7–9 excluded；鲁教版五四学制 grade 6+ middle-school segment excluded；译林低年级 / 牛津小学英语1A–2B deferred pending edition continuity。

---

## 4. Current Phase-A2 machine checkpoint

Latest sealed workflow：**#412 / 34408360726 = SUCCESS**

```text
sealed bot head                    = ac775cbb6d8984502094dcee5a578b6a46fe7643
sealed input commit                = e009ba657a42411b71308c15e921e355667f4c32
Source occurrences                 = 18887
Normalized surfaces                = 3763
Durable Identity decisions         = 3206
Identity Vocabulary Preview        = 2637
Learner Vocabulary Preview         = 2614
Review blockers                    = 718
Evidence-changed surfaces          = 0
Multipart resolved                 = 15
Grammar-form quarantine gates      = 88
CheckpointFingerprint              = 528a748d1fce9ac8d5a20a4dbbfb91a1da0528b40ba5a3c3f596c509cf23d685
```

Recent validated throughput：

```text
#409 — v6-semantic-throughput architecture validation
  semantic budget 120 + independent packet byte budget

#410 — 12-surface semantic-review batch
  water / wave / wing / yummy / may / rock / rough / smooth / snorkel / trick / miss / like
  EvidenceChangedSurfaces 4 → 0; ReviewBlockers 727 → 718

#411 — 8-surface split-resolution batch
  too / french / little / pass / flies / fan / get / line
  DurableIdentityDecisions 3187 → 3197

#412 — 5-surface split-resolution batch
  kind / letter / plant / right / sound
  14 decision rows; reviewed subgroups + explicit held partitions
  DurableIdentityDecisions 3197 → 3206
  full Validation Gate + bot persist + independent post-seal state recheck PASS
```

Every completed batch must pass：batch closure → apply → corpus → SOURCE FREEZE → Completion Recheck → learner gate → audit recheck → Klose isolation → Stage-A seal → bot persist → independent post-seal diff/state recheck。

Multipart re-review 必须复用已有稳定 `DecisionKey` / `CanonicalMatchKey`；允许把旧 whole-surface `split-required` 收敛成 reviewed subgroup + current-context held subgroup，但不得猜义。Corpus builder 对 overlap / incomplete partition fail closed。

---

## 5. NEXT TASK — current deterministic Phase-A2 batch

```text
PlanVersion            = v6-semantic-throughput
ReviewLane             = object-boundary
ReviewMode             = full-evidence
SelectedCount          = 40
EvidenceWeight         = 120
EffectiveWeightBudget  = 120
PacketBytes            = 16917
PacketByteBudget       = 260000
ExecutionReady         = true
```

Selected surfaces：

```text
... years old
100-meter race
a bar of chocolate
a bottle of ...
a bottle of water
a bowl of
a bowl of noodles
a cup of ...
a hope school
a loaf of bread
a packet of biscuits
a packet of sweets
a pair of gloves
a pair of shoes
a pair of socks
a piece of cake
a plate of
a quarter
a quarter past seven
a quarter to ...
a quarter to eight
act a play
after class
after some time
agree with
alarm clock
all day long
all right.
american football
and so on
and you?
any more
anything else ?
arrive at
art museum
as ... as
as big as
as old as
as tall as
ask ... for help
```

Fingerprints：

```text
ReviewBundleFingerprint = d104ee455ca8ebf3b2c21e45f672e4a5b7947996c34a9223e5814eb3855fca3b
ReviewPacketFingerprint = a67ca393e9d79983b05a6228d8fab6d3c5d399d3fb1f979c1ba982836cd5f424
```

Execution strategy：

```text
object-boundary lane
→ verify each selected surface is phrase/expression vs atomic vocabulary
→ batch route true phrases/constructions to Expressions
→ preserve any genuine lexicalized atomic unit as Vocabulary only with evidence
→ create transient review/decision_updates.csv
→ deterministic selected-batch closure
→ full Stage-A Validation Gate
→ bot persist
→ independent post-seal state recheck
```

Planner contract：v6 以 semantic complexity 为主预算；object-boundary 当前 `WeightBudget=120`、`PacketByteBudget=260000`。Source mutation 与 decision mutation 不得混合。

---

## 6. Phase A2 completion target

```text
morphology / form canonicalization
→ orthographic canonicalization
→ cross-source dedup
→ Vocabulary / Expression / source-only boundary
→ learner-relevant polysemy partition
→ evidence-changed re-review
→ audited-defer retirement / refresh
→ targeted duplicate audits
→ learner quarantine check
→ Completion Recheck
→ EvidenceChangedSurfaces = 0
→ NextBatch SelectedCount = 0
→ ExecutionReady = false
→ final Stage-A seal
```

允许最终 residual blocker 只能是 current-context `audited-defer`；不得为追求 blocker=0 猜 sense partition 或扩大 dictionary sense inventory。

---

## 7. Stage-B state — GATED

`premerge/readiness.json` 仍是旧 snapshot，不是当前 Stage-A authority。

```text
snapshot SourceOccurrences    = 7535
current Stage-A occurrences   = 18887
ReadyForPremergeReview        = false
StageBMutationAuthorized      = false
StableThirdPartyIDMinted      = false
MergeAuthorizedRows           = 0
```

Phase A2 完成并通过 final Stage-A seal 前，不刷新 Stage-B premerge snapshot，不开始 durable reconciliation / Stable NoteID allocation。

---

## 8. Frozen boundaries

```text
Source Fact ≠ Vocabulary Identity ≠ Learner Admission ≠ Anki state
Source Grade ≠ LearnerLevel
exact MatchKey equality != same-sense decision
proposal != durable decision
reconciliation != merge authorization
```

- actual textbook evidence > third-party dictionary gloss；
- Stage A 不 mint Stable ThirdPartyID / NoteID；
- Stable NoteID 不得重编号、复用或漂移；
- Stage A 不得修改 Klose Master/Learner/Release/Publish/Anki；
- reconciliation closure + Completion Recheck + explicit human gate 前不得 mint Stable NoteID。
