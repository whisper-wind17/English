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

Authoritative contract：

```text
anki/klose/third_party_vocabulary/config/source_freeze.json
tools/check_third_party_source_freeze.py
CI: Enforce Third-party SOURCE FREEZE
```

Frozen invariants：

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

Terminal source boundaries：

```text
仁爱版                     = excluded; grades 7–9 only
鲁教版五四学制             = excluded; grade 6+ middle-school segment
译林低年级 / 牛津小学1A–2B = deferred; edition continuity not established
```

Source validation evidence：

```text
workflow #351 / 34303418551 = final 20-adapter union SUCCESS
workflow #353 / 34303742198 = SOURCE FREEZE establishment SUCCESS
```

---

## 4. Current Phase-A2 machine checkpoint

Latest sealed workflow：**#361 / 34313132665 = SUCCESS**

```text
Source occurrences                 = 18887
Normalized surfaces                = 3763
Durable Identity decisions         = 2457
Identity Vocabulary Preview        = 1992
Learner Vocabulary Preview         = 1976
Review blockers                    = 1411
Evidence-changed surfaces          = 34
Multipart resolved                 = 3
Grammar-form quarantine gates      = 62
CheckpointFingerprint              = 83647a4477acf83b06622337524549de970ee65f9328d5b1b5dc67cfbb061208
```

Recent validated batches：

```text
light — workflow #359 / 34312798133
  light#illumination = 灯；光；光线
  light#weight       = 轻的；轻便的
  light#intensity    = 轻微的；少量的（如小雨）
  light#ignite       = 点燃；点着
  held               = Beishida + Cambridge unresolved source rows

mouse — workflow #360 / 34312987272
  mouse#animal       = 老鼠            (8 occurrences)
  mouse#computer     = 鼠标；电脑鼠标  (2 occurrences)
  held               = Beishida flat-list row (1 occurrence)

watch — workflow #361 / 34313132665
  watch#noun         = 手表            (11 occurrences)
  watch#verb         = 观看；注视      (11 occurrences)
  held               = 5 occurrences whose current context does not safely bind noun/verb
```

`light` 首次 attempt #358 因 held DecisionKey 被错误追加、造成 multipart occurrence overlap 而失败；修复为复用稳定 DecisionKey 后 #359 全门通过。该 failure mode 已作为后续 multipart update 的检查项：**扩展旧 partition 必须替换旧 DecisionKey，不得另起同义 held row。**

每次上述 batch 均通过：apply → corpus build → SOURCE FREEZE → Completion Recheck → learner gate → audit recheck → Klose isolation → Stage-A seal → bot persist。

---

## 5. NEXT TASK — current deterministic Phase-A2 batch

Planner 当前已从 `policy-review` 进入 `semantic-review`：

```text
PlanVersion    = v5-throughput-delta
ReviewLane     = semantic-review
ReviewMode     = full-evidence
SelectedCount  = 30
EvidenceWeight = 35
ExecutionReady = true

program
20th
21st
22nd
23rd
2nd
30th
31st
3rd
4th
ability
abracadabra
achoo
action
advertisement
aeroplane
airplane
album
alphabet
ambulance
america
anyone
anytime
area
argentina
athlete
atishoo
aviary
aw
bacon
```

Fingerprints：

```text
ReviewBundleFingerprint = cb1406210a980286ca6476c565ac605e9e530961c5dc5127348481fc33634715
ReviewPacketFingerprint = 0100c4cce39ca7e2e0f495d5eda9464dc42d01327a520bb2da6684808b084bfe
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
