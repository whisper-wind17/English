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

动态进度以 repo 当前 machine state 为准；`stage_a_status.json` / `next_batch.json` 高于本文件中的静态快照。

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

Terminal source boundaries：

```text
仁爱版                     = excluded; grades 7–9 only
鲁教版五四学制             = excluded; grade 6+ middle-school segment
译林低年级 / 牛津小学1A–2B = deferred; edition continuity not established
```

---

## 4. Current Phase-A2 machine checkpoint

Latest sealed workflow：**#369 / 34319003085 = SUCCESS**

```text
sealed bot head                    = f96a27cd7ba381096fcbecfd5fd351b0e70d58fa
Source occurrences                 = 18887
Normalized surfaces                = 3763
Durable Identity decisions         = 2719
Identity Vocabulary Preview        = 2223
Learner Vocabulary Preview         = 2205
Review blockers                    = 1150
Evidence-changed surfaces          = 34
Multipart resolved                 = 3
Grammar-form quarantine gates      = 71
CheckpointFingerprint              = 6403eaf556dc57fccf3c3f14422b83f86f849373a89c4d554aea9ff4b0e012c8
```

Recent throughput validation：

```text
#367 — 57 selected / EvidenceWeight 60
  jumped/listened → reviewed canonical + learner quarantine
  looked → look#appearance scoped reuse

#368 — 59 selected / EvidenceWeight 60
  module → source-only
  mustn't / ow / Really? → Expressions
  pencil-case / policemen → reviewed canonical reuse
  meant / planted → source-form identity + learner quarantine

#369 — 57 selected / EvidenceWeight 60
  sold → sell; threw → throw + learner quarantine
  studying → study ing-form reuse
  Spiderman / starter / trainer resolved by textbook context
```

Planner throughput contract：`semantic-review SurfaceCap = 60`，`EvidenceWeightBudget = 60`。数量 cap 不再重复限流；单批大小由 evidence weight 主导。

Each completed batch must pass：batch closure → apply → corpus → SOURCE FREEZE → Completion Recheck → learner gate → audit recheck → Klose isolation → Stage-A seal → bot persist。

---

## 5. NEXT TASK — current deterministic Phase-A2 batch

```text
PlanVersion    = v5-throughput-delta
ReviewLane     = semantic-review
ReviewMode     = full-evidence
SelectedCount  = 18
EvidenceWeight = 60
ExecutionReady = true

 yourselves
 yucky
 yuk
 zipper
 zongzi
 activity
 aloud
 already
 anyway
 appear
 auntie
 badly
 biggest
 bun
 canteen
 cherry
 cleaner
 aboard
```

Fingerprints：

```text
ReviewBundleFingerprint = 98f411177e825ddb758f61b8768112c36bd9500b217df53b11eac3d12d7f7649
ReviewPacketFingerprint = 1938d374674c8d9a4044a299b3afd0b1762c42e64d24bccfa74c5f62ffec3521
```

18 surfaces 已占满 60 weight，说明当前批次进入多 occurrence / 较重 evidence 区；不得为了维持 surface 数量而提高 weight budget。

Batch contract：

```text
next_batch.json
→ selected-only full evidence
→ decision_updates.csv
→ selected set == submitted MatchKey set
→ apply
→ corpus build/check
→ SOURCE FREEZE
→ learner gate
→ audit recheck
→ Klose isolation
→ bot persist
```

Source mutation 与 decision mutation 不得混合。

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

允许最终保留的 residual blocker 只能是 current-context `audited-defer`；不得为追求 blocker=0 猜 sense partition 或扩大 dictionary sense inventory。

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
