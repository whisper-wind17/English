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

---

## 4. Current Phase-A2 machine checkpoint

Latest sealed workflow：**#414 / 34409080109 = SUCCESS**

```text
sealed input commit                = 8a998b8530665441113722c6d2132a6083d7e076
Source occurrences                 = 18887
Normalized surfaces                = 3763
Durable Identity decisions         = 3286
Identity Vocabulary Preview        = 2650
Learner Vocabulary Preview         = 2627
Review blockers                    = 638
Evidence-changed surfaces          = 0
Multipart resolved                 = 15
Grammar-form quarantine gates      = 88
CheckpointFingerprint              = 5a888061a036d4e97115b1fdba13fea3c2859f9d1fe68d1f2c0461ebdd652226
```

Recent validated throughput：

```text
#409 — v6-semantic-throughput architecture validation
#410 — 12-surface semantic-review batch; ReviewBlockers 727 → 718
#411 — 8-surface split-resolution batch
#412 — 5-surface split-resolution batch
#413 — 40-surface object-boundary batch; ReviewBlockers 718 → 678; 4 Vocabulary + 36 Expressions
#414 — 40-surface object-boundary batch; ReviewBlockers 678 → 638; 9 Vocabulary + 31 Expressions
```

#414 full Validation Gate + bot persist + independent post-seal state recheck PASS；transient `decision_updates.csv` 已清除；Source fingerprints 与 Klose isolation 均保持。

Every completed batch must pass：batch closure → apply → corpus → SOURCE FREEZE → Completion Recheck → learner gate → audit recheck → Klose isolation → Stage-A seal → bot persist → independent post-seal state recheck。

---

## 5. NEXT TASK — current deterministic Phase-A2 batch

```text
PlanVersion            = v6-semantic-throughput
ReviewLane             = object-boundary
ReviewMode             = full-evidence
SelectedCount          = 40
EvidenceWeight         = 120
EffectiveWeightBudget  = 120
PacketBytes            = 16317
PacketByteBudget       = 260000
ExecutionReady         = true
```

```text
buy a story book
buy an ice cream
buy some gifts
by myself
by the way
call ... friend
call my friend
call out
call up
can i help you?
care about
care for
carry on with ...
cat food
check out
cheer up
chewing gum
children's palace
children's park
chinese leaves
chinese new year
chinese new year's day
chinese new year's eve
chongyang festival
christmas eve
clean the windows
climb the mountain
climb up
close to
come along
come here
come over
come to a stop
come to an end
come to school
come up
computer lab
computer studies
cook the meal
cowboy hat
```

```text
ReviewBundleFingerprint = faf8f831f67ea3a284112e71643d1a18989f7b304b51c2d3138c12af30f44e6f
ReviewPacketFingerprint = 8896ff58f4939be3f4ff9c8ea6df3da946ca80aec3159581f260eab23b44bc3a
```

Execution strategy：按教材证据区分 lexicalized compound / proper named concept 与 compositional phrase / construction；前者留 Vocabulary，后者批量 route Expressions。不同 identity merge 不在 object-boundary lane 顺手处理。

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

`premerge/readiness.json` 仍是旧 snapshot，不是当前 Stage-A authority。Phase A2 完成并通过 final Stage-A seal 前，不刷新 Stage-B premerge snapshot，不开始 durable reconciliation / Stable NoteID allocation。

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
