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

Latest sealed workflow：**#400 / 34341946713 = SUCCESS**

```text
sealed bot head                    = 932aa791397cff66b4b0abe210d82b47cc1929f8
Source occurrences                 = 18887
Normalized surfaces                = 3763
Durable Identity decisions         = 3135
Identity Vocabulary Preview        = 2598
Learner Vocabulary Preview         = 2575
Review blockers                    = 752
Evidence-changed surfaces          = 13
Multipart resolved                 = 9
Grammar-form quarantine gates      = 87
CheckpointFingerprint              = d3487d7746e0bc99e0cb27e37717296a03ad93319cc1600b4571e09ae0c7fd49
```

Recent validated throughput：

```text
#395 — feel / market / match / mobile / movie
  resolved fail-closed multipart overlap by reusing stable DecisionKeys and canonical senses
#396 — film / mean / meeting / none / note / officer
  film preserved film#movie / film#photo; meeting kept as lexicalized noun; officer split police + held
#397 — fish / opposite
  fish fully closed as 27 noun + 7 verb occurrences
#398 — floor / outgoing / packet / page / pancake / parade / plum / position
  floor fully closed as 8 storey + 11 ground; outgoing kept as lexicalized adjective
#399 — hard / past / pineapple / point
  hard added hard#intense; past fully closed movement / clock / history; weak hard/point contexts held
#400 — hot / pool / pot / prepare / entrance
  hot preserved temperature / spicy with weak contexts held; pool/prepare/entrance closed; pot audited-defer due insufficient container evidence
```

Compact decision inbox rule：human-authored `Rationale` fields are always CSV-quoted before submission。Each completed batch must pass batch closure → apply → corpus → SOURCE FREEZE → Completion Recheck → learner gate → audit recheck → Klose isolation → Stage-A seal → bot persist → independent post-seal diff/state recheck。

Multipart evidence-changed re-review must reuse existing stable `DecisionKey` / `CanonicalMatchKey` names. Do not create parallel sense names for already-reviewed partitions. Corpus builder intentionally fails closed on overlap。

---

## 5. NEXT TASK — current deterministic Phase-A2 batch

```text
PlanVersion    = v5-throughput-delta
ReviewLane     = semantic-review
ReviewMode     = full-evidence
SelectedCount  = 5
EvidenceWeight = 59
ExecutionReady = true

look
rainbow
raise
return
rope
```

Fingerprints：

```text
ReviewBundleFingerprint = d256c97b3e320c439c32727d4c3ecfe7fdb1323de75e5131c7e00fbbde128110
ReviewPacketFingerprint = 984256a51928fdb02101c0c697237f7d0ce457fac76fb0075ccff08d6ac3097d
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
