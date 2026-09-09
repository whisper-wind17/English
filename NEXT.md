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

## 2. Current phase

```text
Phase A1 — Source Adapter Bulk Ingestion = CLOSED
→ SOURCE FREEZE                         = ESTABLISHED
→ Phase A2 — Global Identity Closure     = CURRENT
→ final Stage-A seal
→ Stage B / Klose reconciliation
```

## 3. SOURCE FREEZE — CLOSED

```text
enabled adapters                     = 20
source occurrences                   = 18887
normalized surfaces                  = 3763
source books                         = 178
cross-adapter occurrence collision   = 0
source_adapters.csv SHA-256           = fdf79e5f48ed77d543dc05f3d347c3ce03d406e4884c89a426fdac8fa20e8272
unified occurrences SHA-256           = b025cb4f69b030da3664ab9b1bdd8500cb0166b122392b282a4293567702a7d4
Klose operational mutation           = 0
```

## 4. Current Phase-A2 machine checkpoint

Latest sealed workflow：**#415 / 34409298071 = SUCCESS**

```text
sealed input commit                = 45dba811bd288fd0e0ec02195e89070d919c412a
Source occurrences                 = 18887
Normalized surfaces                = 3763
Durable Identity decisions         = 3326
Identity Vocabulary Preview        = 2663
Learner Vocabulary Preview         = 2640
Review blockers                    = 598
Evidence-changed surfaces          = 0
Multipart resolved                 = 15
Grammar-form quarantine gates      = 88
CheckpointFingerprint              = 5eea9558caa487d849a5ec6e05daa96f7182bfe41262049b2f6546132b39c296
```

Recent validated throughput：

```text
#409 — v6-semantic-throughput architecture validation
#410 — 12-surface semantic-review batch
#411 — 8-surface split-resolution batch
#412 — 5-surface split-resolution batch
#413 — object-boundary 40: ReviewBlockers 718 → 678; 4 Vocabulary + 36 Expressions
#414 — object-boundary 40: ReviewBlockers 678 → 638; 9 Vocabulary + 31 Expressions
#415 — object-boundary 40: ReviewBlockers 638 → 598; 13 Vocabulary + 27 Expressions
```

#415 full Validation Gate + bot persist + independent post-seal state recheck PASS；transient decision batch 已清除；Source fingerprints 与 Klose isolation 保持。

Every completed batch must pass：batch closure → apply → corpus → SOURCE FREEZE → Completion Recheck → learner gate → audit recheck → Klose isolation → Stage-A seal → bot persist → independent post-seal state recheck。

## 5. NEXT TASK — deterministic Phase-A2 batch

```text
PlanVersion            = v6-semantic-throughput
ReviewLane             = object-boundary
ReviewMode             = full-evidence
SelectedCount          = 40
EvidenceWeight         = 120
PacketBytes            = 16769
PacketByteBudget       = 260000
ExecutionReady         = true
```

```text
cross the street
cry out
cut ... out
cut out
cycle helmet
different to ...
do eye exercises
do housework
do some reading
do some shopping
do some training
do some washing
do tai chi
do the dishes
do well in
dog food
dog sledding
don't litter.
don't pick flowers.
don't throw stones.
don't walk on the grass.
don't worry.
donald duck
dotted line
double ninth festival
dragon boat race
dress up as
drink water
drive ... away
drive a car
dunvegan castle
eat sea food
elementary school
enjoy themselves
every now and then
except for
family tree
fashion show
fast asleep
fifteen degrees celsius
```

```text
ReviewBundleFingerprint = ad9d98032c71b5a431cfb89ff21e8a491907c0ca52aaa2ad7c4d18904e44d60c
ReviewPacketFingerprint = 8afd8c3a5307ed7f35449e053307b32fa1c6f6d15d1f0f95edadaa57bba4db6b
```

Execution strategy：按 textbook evidence 区分 stable lexical/proper-name concepts 与 compositional phrase/construction；只做 object boundary，不顺手做 synonym merge 或 dictionary-sense expansion。

## 6. Completion target / frozen boundaries

```text
Vocabulary / Expression / source-only boundary
→ learner-relevant polysemy partition
→ audited-defer retirement / refresh
→ targeted duplicate audits
→ learner quarantine check
→ Completion Recheck
→ EvidenceChangedSurfaces = 0
→ NextBatch SelectedCount = 0
→ ExecutionReady = false
→ final Stage-A seal
```

允许最终 residual blocker 只能是 current-context `audited-defer`；不得猜 sense partition。Stage A 不 mint Stable ThirdPartyID / NoteID，不修改 Klose Master/Learner/Release/Publish/Anki；Stage B 仍 GATED。
