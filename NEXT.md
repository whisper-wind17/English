# NEXT — Klose Learning

Last updated: 2026-09-09

## 1. 启动顺序

所有 Klose 任务先读取：

```text
AGENTS.md
→ NEXT.md
```

当前 Third-party Vocabulary 继续读取：

```text
docs/THIRD_PARTY_SOURCE_FIRST_EXECUTION.md
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

## 2. Current phase — Phase A2 Global Identity Closure

冻结执行顺序：

```text
Phase A1 — Source Adapter Bulk Ingestion       = CLOSED
→ SOURCE FREEZE                               = ESTABLISHED
→ Phase A2 — Global Identity Closure           = CURRENT
→ final Stage-A seal
→ Stage B / Klose reconciliation
```

Phase A2 现在可以处理 Identity review；但 **SOURCE FREEZE 后不得静默修改 source_adapters、adapter occurrences 或 raw-source interpretation**。任何确有必要的 Source 修正都必须显式 reopen Source Freeze，重新通过 Source gate 后再回到 A2。

---

## 3. SOURCE FREEZE — 20 adapters / CLOSED

```text
beijing_start1          =  808 occurrences /  734 MatchKeys / 12 books
beishida_start1         =  925 occurrences /  798 MatchKeys / 12 books
beishida_start3         =  699 occurrences /  663 MatchKeys /  8 books
cambridge_join_start3   = 1456 occurrences / 1333 MatchKeys /  8 books
guangdong_start3        =  741 occurrences /  665 MatchKeys /  8 books
guangzhou_start3        = 1268 occurrences / 1212 MatchKeys /  8 books
hujiao_start3           = 1111 occurrences / 1067 MatchKeys /  8 books
jiaoke_eec_start3       = 1093 occurrences / 1033 MatchKeys /  8 books
jijiao_start3           =  605 occurrences /  510 MatchKeys /  8 books
kepu_start3             =  772 occurrences /  771 MatchKeys /  8 books
luke_54_start3          =  714 occurrences /  681 MatchKeys /  6 books
minjiao_start3          =  772 occurrences /  732 MatchKeys /  8 books
niujin_shanghai_start1  = 1186 occurrences /  974 MatchKeys / 12 books
renjiao_start1          =  908 occurrences /  802 MatchKeys / 12 books
renjiao_start3          =  851 occurrences /  818 MatchKeys /  8 books
shaanxi_start3          =  917 occurrences /  880 MatchKeys /  8 books
waiyan_start1           = 1170 occurrences / 1071 MatchKeys / 12 books
waiyan_start3           = 1157 occurrences / 1023 MatchKeys /  8 books
xiangshao_start3        =  698 occurrences /  674 MatchKeys /  8 books
yilin_start3            = 1036 occurrences /  998 MatchKeys /  8 books
---------------------------------------------------------------------
Total                   = 18887 source occurrences / 178 books
```

Final adapter `luke_54_start3`:

```text
6 raw books / 714 occurrences / 681 MatchKeys
raw schema                            = headerless A=Word / B=Definition (6/6)
British / American source columns     = absent
blank Definition source facts         = 2
grade-6-plus leakage                  = 0
parser / dedicated checker            = PASS
```

Edition-specific blank `Definition` source facts total **13**:

```text
cambridge_join_start3=1
guangzhou_start3=1
luke_54_start3=2
minjiao_start3=1
shaanxi_start3=1
waiyan_start1=2
waiyan_start3=2
yilin_start3=3
```

这些是冻结 Source Facts，不得手工补写或归一化掉。

---

## 4. SOURCE FREEZE machine contract

```text
contract = anki/klose/third_party_vocabulary/config/source_freeze.json
checker  = tools/check_third_party_source_freeze.py
CI step  = Enforce Third-party SOURCE FREEZE
```

Frozen invariants：

```text
planned enabled adapters             = exactly 20
source occurrences                   = 18887
source books                         = 178
blank Definition facts               = 13
all adapters dedicated prepare/check = yes
cross-adapter occurrence collision   = 0
source_adapters.csv SHA-256           = fdf79e5f48ed77d543dc05f3d347c3ce03d406e4884c89a426fdac8fa20e8272
unified occurrences SHA-256           = b025cb4f69b030da3664ab9b1bdd8500cb0166b122392b282a4293567702a7d4
Klose mutation                       = 0 (independent workflow git-diff gate)
```

Terminal scope boundaries are recorded in the contract:

```text
仁爱版                     = excluded; only grades 7-9
鲁教版五四学制             = excluded; grade 6+ is middle-school segment
译林低年级 / 牛津小学1A-2B = deferred; edition continuity with start3 not established
```

Validation evidence：

```text
Final source-union workflow #351 / 34303418551 = SUCCESS
SOURCE FREEZE CI workflow #353 / 34303742198   = SUCCESS
Stage-A CheckpointFingerprint                  = fe96f22917626ef0ade57f0e92426ddf6d82dc703dab062649338316f555fe17
```

---

## 5. Current Phase-A2 Identity state

Authoritative machine state:

```text
Source occurrences                 = 18887
Normalized surfaces                = 3763
Durable Identity decisions         = 2411
Identity Vocabulary Preview        = 1966
Learner Vocabulary Preview         = 1953
Review blockers                    = 1457
Evidence-changed surfaces          = 41
Multipart resolved                 = 0
Grammar-form quarantine gates      = 61
```

这些 blocker 是最终 frozen source evidence 上的 Identity-layer 工作，不再因后续 Adapter 接入继续 churn。

Minimal Learner Identity 规则继续生效：

```text
reviewed singleton + additive same-MatchKey evidence
→ refresh provenance only; no semantic re-review

true learner-relevant polysemy
→ multipart exact occurrence partition

Identity resolved
≠ Learner Admission
```

---

## 6. NEXT TASK — execute Phase A2 review batch

Current deterministic batch：

```text
PlanVersion    = v5-throughput-delta
ReviewLane     = policy-review
ReviewMode     = full-evidence
SelectedCount  = 13
ExecutionReady = true

heard
eggs
flowers
relatives
fruits
left
1st
can i ...?
cd player
cd-rom
dr
ha
hmm
```

Batch execution contract：

```text
next_batch.json
→ selected-only review packet/view
→ decision_updates.csv
→ planner selected set == submitted MatchKey set
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

## 7. Phase A2 completion target

按最终 frozen corpus 统一完成：

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

## 8. Stage-B state — OLD SNAPSHOT, GATED

`premerge/readiness.json` 仍是旧的 7535-occurrence snapshot，不是当前 authority。

```text
ReadyForPremergeReview     = false
StageBMutationAuthorized   = false
StableThirdPartyIDMinted   = false
MergeAuthorizedRows        = 0
```

只有 Phase A2 完成、final Stage-A seal 验证后，才能刷新 Stage-B premerge snapshot。

---

## 9. Frozen boundaries

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
- Stage A / reconciliation workflow 不得修改 Klose Master/Learner/Release/Publish/Anki；
- reconciliation closure + independent Completion Recheck + explicit human gate 前不得 mint Stable NoteID。
