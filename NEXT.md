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

Terminal source boundaries：仁爱版 grades 7–9 excluded；鲁教版五四学制 grade 6+ middle-school segment excluded；译林低年级 / 牛津小学1A–2B deferred pending edition continuity。

---

## 4. Current Phase-A2 machine checkpoint

Latest sealed workflow：**#410 / 34366294228 = SUCCESS**

```text
sealed bot head                    = ac51be4327ff289e953421ce57937e4823773e00
sealed input commit                = 5e3f3c462d848489ce7ee3956bae230c628557af
Source occurrences                 = 18887
Normalized surfaces                = 3763
Durable Identity decisions         = 3187
Identity Vocabulary Preview        = 2637
Learner Vocabulary Preview         = 2614
Review blockers                    = 718
Evidence-changed surfaces          = 0
Multipart resolved                 = 15
Grammar-form quarantine gates      = 88
CheckpointFingerprint              = 36eea59880e15c495d034209865b59adcb99b1f0231664e3fab83533534ec7b8
```

Recent validated throughput：

```text
#402 — orange / sand
#403 — play / seal / several
#404 — save / seat / shoot / shower / silly / skateboard / slide / sore / spot / square / sticker
#405 — show / taste / tasty / term / terrible
#406 — thin / throat / toe / tour / upstairs / exit
#407 — time / used / wake / waste

#409 — throughput architecture validation
  planner upgraded from occurrence-weighted v5 to v6-semantic-throughput
  semantic complexity budget = 120
  review packet byte budget = 300000
  source / learner / Klose isolation gates all PASS

#410 — 12-surface high-throughput semantic batch
  water / wave / wing / yummy / may / rock / rough / smooth / snorkel / trick / miss / like
  SelectedCount = 12, EvidenceWeight = 91, PacketBytes = 58255
  EvidenceChangedSurfaces 4 → 0
  ReviewBlockers 727 → 718
  MultipartResolved 13 → 15
  full Validation Gate + bot persist + independent post-seal state recheck PASS
```

同一 input commit 曾被 GitHub 重复排出 #408。#408 的 validation steps 通过，但最终 persist 与已先写入的 #407 发生 rebase conflict；它不是有效 checkpoint。

Every completed batch must pass：batch closure → apply → corpus → SOURCE FREEZE → Completion Recheck → learner gate → audit recheck → Klose isolation → Stage-A seal → bot persist → independent post-seal diff/state recheck。

Multipart re-review 必须复用已有稳定 `DecisionKey` / `CanonicalMatchKey`；允许把旧的 whole-surface `split-required` 收敛成 reviewed subgroup + current-context held subgroup，但不得猜义。Corpus builder 对 overlap / incomplete partition fail closed。

---

## 5. NEXT TASK — current deterministic Phase-A2 batch

Machine-selected next batch：

```text
PlanVersion            = v6-semantic-throughput
ReviewLane             = split-resolution
ReviewMode             = full-evidence
SelectedCount          = 8
EvidenceWeight         = 119
EffectiveWeightBudget  = 120
PacketBytes            = 48238
PacketByteBudget       = 300000
ExecutionReady         = true

too
french
little
pass
flies
fan
get
line
```

Fingerprints：

```text
ReviewBundleFingerprint = ef1772f4001bb4095ae6af98ce4fe968a2b1858d8c3ebd405347862c403521c1
ReviewPacketFingerprint = d4eb6664c27197058e34eb378172fa1d4351e0ed0c6eae76352d2d499a33fc48
```

Execution strategy：

```text
too / french / little / pass / fan / line
→ establish only evidence-supported reviewed subgroups
→ put ambiguous occurrences into explicit current-context held partitions

flies / get
→ current source window is still insufficient for safe partition
→ refresh audited split-required defer; do not guess

then:
→ create transient review/decision_updates.csv
→ pre-main partition/diff/scope check
→ non-force main update
→ full Stage-A Validation Gate
→ bot persist
→ independent post-seal diff/state recheck
```

Planner contract：v6 以 semantic complexity 为主预算，`WeightBudget=120`，并独立限制 `PacketByteBudget=300000`；lane-specific SurfaceCap 只作表面数量 guard。Source mutation 与 decision mutation 不得混合。

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
