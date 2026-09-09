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

Latest sealed workflow：**#407 / 34360581909 = SUCCESS**

```text
sealed bot head                    = e71e03e9b8b0ddf421c711551b4bb8866fcc6ab6
Source occurrences                 = 18887
Normalized surfaces                = 3763
Durable Identity decisions         = 3175
Identity Vocabulary Preview        = 2627
Learner Vocabulary Preview         = 2604
Review blockers                    = 727
Evidence-changed surfaces          = 4
Multipart resolved                 = 13
Grammar-form quarantine gates      = 88
CheckpointFingerprint              = 1c4acaaaca00c1001ad272d96c1edfeb7935aa7e4c675f62e8e74756dd4a1446
```

Recent validated throughput：

```text
#402 — orange / sand
  orange closed as fruit + color + 2 current-context held; sand closed as 沙/沙子
#403 — play / seal / several
  play closed as general + instrument + theatre + held; new play#theatre learner sense
#404 — save / seat / shoot / shower / silly / skateboard / slide / sore / spot / square / sticker
  save/square revalidated; shoot#sports and slide#movement added; spot kept audited-defer
#405 — show / taste / tasty / term / terrible
  show revalidated as verb + performance + held; taste added noun flavour identity without sense overlap
#406 — thin / throat / toe / tour / upstairs / exit
  thin revalidated as slim + object-thin + held; tour travel + held; four singleton identities closed
#407 — time / used / wake / waste
  time closed as general + count + held; used reuses use and is learner-quarantined; wake verb + held; waste split into verb + rubbish/waste noun
```

Workflow anomaly note：同一 input commit 曾被 GitHub 重复排出 #408。#408 的 batch closure、SOURCE FREEZE、Completion Recheck、learner gate、audit recheck、Klose isolation 与 seal 全部通过，仅在最终 persist 时因 #407 已先写入 `stage_a_status.json` 发生 rebase conflict；**#408 不是有效 checkpoint，authoritative sealed checkpoint 仍是 #407**。

Every completed batch must pass：batch closure → apply → corpus → SOURCE FREEZE → Completion Recheck → learner gate → audit recheck → Klose isolation → Stage-A seal → bot persist → independent post-seal diff/state recheck。

Multipart evidence-changed re-review must reuse existing stable `DecisionKey` / `CanonicalMatchKey` names. Do not create parallel sense names for already-reviewed partitions. Corpus builder intentionally fails closed on overlap。

---

## 5. NEXT TASK — current deterministic Phase-A2 batch

Machine-selected next batch：

```text
PlanVersion    = v5-throughput-delta
ReviewLane     = semantic-review
ReviewMode     = full-evidence
SelectedCount  = 4
EvidenceWeight = 60
ExecutionReady = true

water
wave
wing
rock
```

Fingerprints：

```text
ReviewBundleFingerprint = 17561cb7771dca48b3d4268416a5550c1e1ae59dfa30012769ca6ccdc0566693
ReviewPacketFingerprint = 00183cd360d245e057f12ce196bdc9e2b591497edc195a5174c971b8d1fbf151
```

Next execution sequence：

```text
read selected_review_packet.json / selected_review_view.csv
→ establish full-evidence semantic partitions for water / wave / wing / rock
→ create transient decision_updates.csv
→ pre-main diff/scope check
→ non-force main update
→ full Stage-A Validation Gate
→ bot persist
→ independent post-seal diff/state recheck
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
snapshot SourceOccurrences    = 7535   # stale historical Stage-B snapshot
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
