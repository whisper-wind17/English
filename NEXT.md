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

Latest sealed workflow：**#376 / 34321902035 = SUCCESS**

```text
sealed bot head                    = dcabfc8668d89ad6228897847405952a01cf14df
Source occurrences                 = 18887
Normalized surfaces                = 3763
Durable Identity decisions         = 2803
Identity Vocabulary Preview        = 2300
Learner Vocabulary Preview         = 2281
Review blockers                    = 1066
Evidence-changed surfaces          = 34
Multipart resolved                 = 3
Grammar-form quarantine gates      = 74
CheckpointFingerprint              = 079ed349f8e253d2b86f504bc8ce20f291b11b2d6958f32fa8e4fc948ab7d579
```

Recent validated throughput：

```text
#370 — 18 / weight 60
  yourselves → yourself reuse; zipper source-gloss noise corrected; cleaner narrowed to 清洁工
#371 — 15 / weight 60
  congratulations → Expression; helped → help + learner quarantine
#374 — 16 / weight 60
  oops → Expression; longest retained as superlative source-form
  #372/#373 failed before durable apply because transient CSV quoting was malformed; #374 clean rerun passed all gates
#375 — 18 / weight 60
  phew / shh → Expressions; serious / rich narrowed to learner-core sense; shortest/smallest source-form
#376 — 17 / weight 60
  visited → visit + learner quarantine; talked kept source-form + learner quarantine; tallest source-form
```

Compact decision inbox rule：human-authored `Rationale` fields are always CSV-quoted before submission。Each completed batch must pass batch closure → apply → corpus → SOURCE FREEZE → Completion Recheck → learner gate → audit recheck → Klose isolation → Stage-A seal → bot persist → independent post-seal diff/state recheck。

---

## 5. NEXT TASK — current deterministic Phase-A2 batch

```text
PlanVersion    = v5-throughput-delta
ReviewLane     = semantic-review
ReviewMode     = full-evidence
SelectedCount  = 39
EvidenceWeight = 60
ExecutionReady = true

weak
weekday
yeah
yuan
zero
air-conditioned
alone
alright
arctic
assistant
autograph
ax
bandage
bar
barbecue
battle
bay
blink
block
blond
blood
blunt
blush
boss
bottom
branch
bucket
bulb
bush
cage
calculate
captain
cardboard
carnation
caterpillar
chain
champion
chance
chant
```

Fingerprints：

```text
ReviewBundleFingerprint = 47eb0a974d88e1e3b24c7c1393f529019ab633364ee157664f1a4e313e5d007c
ReviewPacketFingerprint = 8558073565e7adef815e85209174366b56dd4f1e4a4efad083ce90b30aefa1a8
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
