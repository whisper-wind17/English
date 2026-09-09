# NEXT — Klose Learning

Last updated: 2026-09-10

## 1. 启动顺序

所有 Klose 任务固定读取：`AGENTS.md → NEXT.md → 当前任务 docs → source_freeze.json → stage_a_status.json → next_batch.json → premerge/readiness.json`。动态进度以 machine state 为准。

## 2. Current phase

```text
Phase A1 Source Adapter Bulk Ingestion = CLOSED
SOURCE FREEZE                         = ESTABLISHED
Phase A2 Global Identity Closure      = CURRENT
Stage B / Klose reconciliation        = GATED
```

SOURCE FREEZE：20 adapters / 18887 occurrences / 3763 surfaces；source fingerprints 未变化；Stage A 不修改 Klose / Anki / Stable NoteID。

## 3. Current sealed checkpoint

Latest sealed workflow：**#416 / 34409506307 = SUCCESS**

```text
sealed input commit                = b00c259b750e8455445ef35b5ef5c2b76f10f008
Durable Identity decisions         = 3366
Identity Vocabulary Preview        = 2674
Learner Vocabulary Preview         = 2651
Review blockers                    = 558
Evidence-changed surfaces          = 0
Multipart resolved                 = 15
Grammar-form quarantine gates      = 88
CheckpointFingerprint              = 62ac157bf04d14d86a2062cf34dfd19c0ea5fbae922940680ce6c46eed05a767
```

High-throughput history：

```text
#413 object-boundary 40: blockers 718 → 678
#414 object-boundary 40: blockers 678 → 638
#415 object-boundary 40: blockers 638 → 598
#416 object-boundary 40: blockers 598 → 558
```

四批均 full Validation Gate + bot persist + independent post-seal recheck PASS；没有 Source/Klose 边界回归。

## 4. NEXT deterministic batch

```text
PlanVersion            = v6-semantic-throughput
ReviewLane             = object-boundary
SelectedCount          = 40
EvidenceWeight         = 120 / 120
PacketBytes            = 16148 / 260000
ExecutionReady         = true
```

```text
find out about
fitting room
for a minute
for here or to go?
for now
for you
fountain pen
fried rice
from door to door
fun park
get a haircut
get along
get dressed
get home
get hurt
get into
get out of
get ready
get to school
gift shop
give ... a big hand
given name
go around
go back
go back to
go climbing
go for it
go hiking
go in
go into
go off
go on the internet
go out to play
go running
go sightseeing
go to college
go to sleep
go to the park
go to the zoo
go well
```

```text
ReviewBundleFingerprint = d5af3a3fb5c65670f12a54dbfc3bc5524c58030520c697cf8f2d97aac0617481
ReviewPacketFingerprint = fb18e3c1540c1ebb654e0f7429000f4d43799318aeacabdc31374550d025958f
```

Execution rule：stable lexical/proper-name concept → Vocabulary；compositional phrase / construction / phrasal verb / communicative chunk → Expressions。object-boundary lane 不顺手做 alias merge 或 dictionary-sense expansion。

Every batch: closure → apply → corpus → SOURCE FREEZE → Completion Recheck → learner gate → audit recheck → Klose isolation → seal → bot persist → independent post-seal recheck。

## 5. Completion target

`Vocabulary/Expression boundary → polysemy closure → audited-defer refresh → duplicate audits → Completion Recheck → NextBatch=0 → final Stage-A seal`。允许 residual 仅为 current-context audited-defer，不得猜义。
