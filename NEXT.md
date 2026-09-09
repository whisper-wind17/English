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

动态进度以 repo 当前 machine state 为准。

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
source books                         = 178
blank Definition source facts        = 13
cross-adapter occurrence collision   = 0
dedicated prepare/check              = 20 / 20
source_adapters.csv SHA-256           = fdf79e5f48ed77d543dc05f3d347c3ce03d406e4884c89a426fdac8fa20e8272
unified occurrences SHA-256           = b025cb4f69b030da3664ab9b1bdd8500cb0166b122392b282a4293567702a7d4
Klose operational mutation           = 0
```

Contract / checker：

```text
anki/klose/third_party_vocabulary/config/source_freeze.json
tools/check_third_party_source_freeze.py
CI: Enforce Third-party SOURCE FREEZE
```

Terminal source boundaries：

```text
仁爱版                     = excluded; grades 7–9 only
鲁教版五四学制             = excluded; grade 6+ middle-school segment
译林低年级 / 牛津小学1A–2B = deferred; edition continuity not established
```

Source validation：

```text
workflow #351 / 34303418551 = final 20-adapter union SUCCESS
workflow #353 / 34303742198 = SOURCE FREEZE establishment SUCCESS
```

---

## 4. Current Phase-A2 machine checkpoint

Latest sealed workflow：**#362 / 34313782981 = SUCCESS**

```text
Source occurrences                 = 18887
Normalized surfaces                = 3763
Durable Identity decisions         = 2486
Identity Vocabulary Preview        = 2014
Learner Vocabulary Preview         = 1998
Review blockers                    = 1383
Evidence-changed surfaces          = 34
Multipart resolved                 = 3
Grammar-form quarantine gates      = 62
CheckpointFingerprint              = 63307ec86e8f6376098f750674126c0039b12ff1c9719fb61a136c09375fdbad
```

Recent validated batches：

```text
light — #359 / 34312798133
  illumination / weight / intensity / ignite + 2 held
  #358 initially failed because a new held DecisionKey overlapped the old partition;
  fixed by replacing the stable held DecisionKey rather than appending a synonym row.

mouse — #360 / 34312987272
  animal 8 / computer 2 / held 1

watch — #361 / 34313132665
  wristwatch noun 11 / viewing verb 11 / held 5

semantic batch — #362 / 34313782981
  30 selected MatchKeys fully closed
  program reused reviewed canonical programme for programme/show sense
  abracadabra / achoo / atishoo / aw routed to Expressions
  action / album retained as current-context audited-defer rather than guessing a sense
  numeric ordinals retained as reviewed source-form Vocabulary identities for now
  aeroplane / airplane retained separately in semantic pass; later orthographic duplicate audit may reconcile them
```

Every validated batch passed：batch closure → apply → corpus build/check → SOURCE FREEZE → Completion Recheck → learner gate → audit recheck → Klose isolation → Stage-A seal → bot persist。

---

## 5. NEXT TASK — current deterministic Phase-A2 batch

```text
PlanVersion    = v5-throughput-delta
ReviewLane     = semantic-review
ReviewMode     = full-evidence
SelectedCount  = 30
EvidenceWeight = 31
ExecutionReady = true

baker
bangkok
beauty
began
blazer
bookworm
brazil
brightly
britain
budgie
builder
bund
cactus
california
campsite
cardigan
cassette
celebration
celery
certainly
cheaper
check-up
checklist
childish
chilli
chimney
circus
college
conductor
confident
```

Fingerprints：

```text
ReviewBundleFingerprint = 3b62597925d5fe808b6d5a64773f644af3ece0d61d1b2059e4a0f501d1c10f2f
ReviewPacketFingerprint = b92dbcff1f35aa63975705bbe9ed23a1406cd534132b0bce3274573fb91348d7
```

Batch contract：

```text
next_batch.json
→ selected-only full evidence
→ decision_updates.csv
→ submitted MatchKey set == planner selected set
→ apply
→ corpus build/check
→ SOURCE FREEZE check
→ learner build/check
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

## 7. Stage-B state — OLD SNAPSHOT, GATED

`premerge/readiness.json` 仍是旧 7535-occurrence snapshot，不是当前 authority。

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
