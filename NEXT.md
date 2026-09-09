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

Latest sealed workflow：**#411 / 34407926063 = SUCCESS**

```text
sealed bot head                    = 3a5eb61359fb9be8eba0af421dc09c14559929a5
sealed input commit                = c7dfc4a0c94893fd9ee4e508f4cad5d7fb39ded8
Source occurrences                 = 18887
Normalized surfaces                = 3763
Durable Identity decisions         = 3197
Identity Vocabulary Preview        = 2637
Learner Vocabulary Preview         = 2614
Review blockers                    = 718
Evidence-changed surfaces          = 0
Multipart resolved                 = 15
Grammar-form quarantine gates      = 88
CheckpointFingerprint              = e2d6e2724052e413fe6b63519d80dcb9af3d0e0b53aef33f53230e4fa779d71e
```

Recent validated throughput：

```text
#409 — throughput architecture validation
  v6-semantic-throughput; semantic budget 120 + packet budget 300000

#410 — 12-surface semantic-review batch
  water / wave / wing / yummy / may / rock / rough / smooth / snorkel / trick / miss / like
  EvidenceChangedSurfaces 4 → 0; ReviewBlockers 727 → 718; MultipartResolved 13 → 15

#411 — 8-surface split-resolution batch
  too / french / little / pass / flies / fan / get / line
  SelectedCount = 8, EvidenceWeight = 119, PacketBytes = 48238
  reviewed evidence-supported subgroups + explicit current-context held partitions
  DurableIdentityDecisions 3187 → 3197
  full Validation Gate + bot persist + independent post-seal state recheck PASS
```

Every completed batch must pass：batch closure → apply → corpus → SOURCE FREEZE → Completion Recheck → learner gate → audit recheck → Klose isolation → Stage-A seal → bot persist → independent post-seal diff/state recheck。

Multipart re-review 必须复用已有稳定 `DecisionKey` / `CanonicalMatchKey`；允许把旧 whole-surface `split-required` 收敛成 reviewed subgroup + current-context held subgroup，但不得猜义。Corpus builder 对 overlap / incomplete partition fail closed。

---

## 5. NEXT TASK — current deterministic Phase-A2 batch

```text
PlanVersion            = v6-semantic-throughput
ReviewLane             = split-resolution
ReviewMode             = full-evidence
SelectedCount          = 5
EvidenceWeight         = 81
EffectiveWeightBudget  = 120
PacketBytes            = 48883
PacketByteBudget       = 300000
ExecutionReady         = true

kind
letter
plant
right
sound
```

Fingerprints：

```text
ReviewBundleFingerprint = 5858044741fe3a9934cfc43dec26fc3666f1658939d52a4a58e99d7390827a5f
ReviewPacketFingerprint = b8a9be4cd8c53f7310d39de54b7df3e8c2b0d923ecaa7b8c929878f7b85fa580
```

Execution sequence：

```text
read selected_review_packet.json / selected_review_view.csv
→ establish only evidence-supported disjoint learner subgroups
→ preserve ambiguous current-context occurrences as held
→ create transient review/decision_updates.csv
→ pre-main partition/diff/scope check
→ non-force main update
→ full Stage-A Validation Gate
→ bot persist
→ independent post-seal diff/state recheck
```

Planner contract：v6 以 semantic complexity 为主预算，`WeightBudget=120`，并独立限制 `PacketByteBudget=300000`；lane-specific SurfaceCap 只作数量 guard。Source mutation 与 decision mutation 不得混合。

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
