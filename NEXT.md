# NEXT — Klose Learning

Last updated: 2026-09-09

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

Latest sealed workflow：**#401 / 34342256091 = SUCCESS**

```text
sealed bot head                    = 15f8e2cf9750adb14749e1d3f2774b213e8f97b4
Source occurrences                 = 18887
Normalized surfaces                = 3763
Durable Identity decisions         = 3140
Identity Vocabulary Preview        = 2602
Learner Vocabulary Preview         = 2579
Review blockers                    = 748
Evidence-changed surfaces          = 12
Multipart resolved                 = 9
Grammar-form quarantine gates      = 87
CheckpointFingerprint              = bd630e905cfea4ba845e96a7f725911619edba7de264954fd93a0339c27e628c
```

Recent validated throughput：

```text
#396 — film / mean / meeting / none / note / officer
  film preserved film#movie / film#photo; meeting kept as lexicalized noun; officer split police + held
#397 — fish / opposite
  fish fully closed as 27 noun + 7 verb occurrences
#398 — floor / outgoing / packet / page / pancake / parade / plum / position
  floor fully closed as 8 storey + 11 ground; outgoing kept as lexicalized adjective
#399 — hard / past / pineapple / point
  hard added hard#intense; past fully closed movement / clock / history; weak hard/point contexts held
#400 — hot / pool / pot / prepare / entrance
  hot preserved temperature / spicy with weak contexts held; pool/prepare/entrance closed; pot audited-defer
#401 — look / rainbow / raise / return / rope
  look fully partitioned as 17 see + 6 appearance + 3 held; rainbow/raise/return/rope closed
```

Compact decision inbox rule：human-authored `Rationale` fields are always CSV-quoted before submission。Each completed batch must pass batch closure → apply → corpus → SOURCE FREEZE → Completion Recheck → learner gate → audit recheck → Klose isolation → Stage-A seal → bot persist → independent post-seal diff/state recheck。

Multipart evidence-changed re-review must reuse existing stable `DecisionKey` / `CanonicalMatchKey` names. Do not create parallel sense names for already-reviewed partitions. Corpus builder intentionally fails closed on overlap。

---

## 5. NEXT TASK — current deterministic Phase-A2 batch

```text
PlanVersion    = v5-throughput-delta
ReviewLane     = semantic-review
ReviewMode     = full-evidence
SelectedCount  = 2
EvidenceWeight = 60
ExecutionReady = true

orange
sand
```

Fingerprints：

```text
ReviewBundleFingerprint = 13c5d33fe2f337765eb7ebadafd9684e1c983c5269c317fee9886c85b247ea0a
ReviewPacketFingerprint = dae0ada601c10eeac77fd475fa8829a0e755e08989a94123f8e09266549fd2f6
```

Planner contract：`semantic-review SurfaceCap = 60`，`EvidenceWeightBudget = 60`；单批大小由 evidence weight 主导。Source mutation 与 decision mutation 不得混合。

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
ReadyForPremergeReview     = false
StageBMutationAuthorized   = false
StableThirdPartyIDMinted   = false
MergeAuthorizedRows        = 0
```

Phase A2 完成并通过 final Stage-A seal 前，不刷新 Stage-B premerge snapshot。

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
