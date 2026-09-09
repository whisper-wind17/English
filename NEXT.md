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
→ anki/klose/third_party_vocabulary/audit/stage_a_status.json
→ anki/klose/third_party_vocabulary/audit/next_batch.json
→ anki/klose/third_party_vocabulary/premerge/readiness.json
```

动态进度以 repo 当前 machine state 为准。

---

## 2. Current phase — Phase A1 Source Adapter Bulk Ingestion

冻结执行顺序：

```text
Phase A1 — Source Adapter Bulk Ingestion
→ SOURCE FREEZE
→ Phase A2 — Global Identity Closure
→ final Stage-A seal
→ Stage B / Klose reconciliation
```

**当前不要处理 Identity review batch，包括 `program / programme`。**

Phase A1 允许新增 source evidence 持续扩大 pending / evidence-changed / multipart / object-boundary 队列；只有 parser/source mapping 错误才是 Source blocker。

---

## 3. Existing enabled Adapter baseline — 16 CLOSED

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
niujin_shanghai_start1  = 1186 occurrences /  974 MatchKeys / 12 books
renjiao_start1          =  908 occurrences /  802 MatchKeys / 12 books
renjiao_start3          =  851 occurrences /  818 MatchKeys /  8 books
waiyan_start1           = 1170 occurrences / 1071 MatchKeys / 12 books
waiyan_start3           = 1157 occurrences / 1023 MatchKeys /  8 books
xiangshao_start3        =  698 occurrences /  674 MatchKeys /  8 books
---------------------------------------------------------------------
Total                   = 15448 source occurrences / 148 books
```

Latest completed adapter: `cambridge_join_start3`.

```text
8 raw books / 1456 occurrences / 1333 MatchKeys
blank Definition source facts       = 1
parser                               = PASS
dedicated edition checker            = PASS
all dedicated source checkers        = 16 PASS
global adapter closure               = PASS
Corpus Completion Recheck            = PASS
Learner quarantine check             = PASS
Audit-batch Recheck                  = PASS
Klose isolation                      = PASS
Stage-A seal                         = PASS
Workflow #333 / 34301045752          = SUCCESS
CheckpointFingerprint                = c6271bc1bcf69b24c05dc6f97c940790e34d5a84ae7efb6ec7f4b4545f1ed2eb
```

Edition-specific blank `Definition` source facts currently total 6: `cambridge_join_start3=1`, `guangzhou_start3=1`, `waiyan_start1=2`, `waiyan_start3=2`. These are frozen Source Facts and must not be normalized away manually.

---

## 4. Remaining raw-source inventory before SOURCE FREEZE

```text
yilin_start3            # 译林版三年级起点，3–6，上下册，共 8 册
minjiao_start3          # 闽教版三年级起点，3–6，上下册，共 8 册
shaanxi_start3          # 陕西版三年级起点，3–6，上下册，共 8 册
luke_54_start3          # 鲁科版五四学制，小学 3–5，上下册，共 6 册；五年制小学边界
```

明确不进入当前小学 corpus：

```text
仁爱版   # raw source 仅七/八/九年级
鲁教版   # 五四学制六–九年级；六年级起属于该学制初中段
```

译林版另有一年级/二年级及 `牛津小学英语1A/1B/2A/2B`，但没有与其明确同一 edition/revision 的 3–6 连续命名序列。**不得与 `译林版三年级起点` 静默拼成 start1 adapter**；如未来需要，先做 edition/source reconciliation。

---

## 5. NEXT TASK — add `yilin_start3`

只接入明确命名的 8 册：

```text
译林版三年级起点三年级上 / 下
译林版三年级起点四年级上 / 下
译林版三年级起点五年级上 / 下
译林版三年级起点六年级上 / 下
```

Per-Adapter Definition of Done：

```text
1. dedicated parser
2. dedicated edition-specific checker
3. books / occurrences / MatchKeys baseline frozen from raw XLSX
4. standard occurrence schema
5. SourceOccurrenceKey adapter 内唯一 + cross-adapter no collision
6. SourceID / Grade / Semester / SourceBook / SourceFile / SourceRow 正确
7. source_adapters.csv enable
8. global adapter closure PASS
9. corpus rebuild + Completion Recheck PASS
10. existing Source Fact no unexpected drift
11. Klose Master/Learner/Release/Publish/Anki unchanged
```

---

## 6. Current Identity state — carry forward, DO NOT close yet

```text
Source occurrences                 = 15448
Normalized surfaces                = 3471
Durable Identity decisions         = 2411
Identity Vocabulary Preview        = 1967
Learner Vocabulary Preview         = 1954
Review blockers                    = 1165
Evidence-changed surfaces          = 41
Multipart resolved                 = 0
Grammar-form quarantine gates      = 61
```

这些变化来自新增 Source evidence；Phase A1 暂不处理 Identity review，也不处理 `program / programme`。

---

## 7. SOURCE FREEZE gate

所有计划第三方小学教材 Adapter 完成前：

```text
DO NOT declare final Stage-A completion.
DO NOT require NextBatch=0 as Phase-A1 exit condition.
DO NOT begin final Identity closure.
DO NOT begin Stage-B reconciliation.
DO NOT mint Stable ThirdPartyID / NoteID.
DO NOT modify Klose Master/Learner/Release/Publish/Anki.
```

所有计划 Adapter 完成后，先建立 SOURCE FREEZE：

```text
all planned adapters terminal
source union deterministic
all enabled adapters have dedicated prepare/check
cross-adapter occurrence collision = 0
unexpected Source Fact drift = 0
Klose mutation = 0
```

随后才进入 Phase A2。

---

## 8. Phase A2 — Global Identity Closure

SOURCE FREEZE 后一次性完成：

```text
morphology / form canonicalization
→ orthographic canonicalization
→ cross-source dedup
→ Vocabulary / Expression / source-only boundary
→ learner-relevant polysemy partition
→ evidence-changed re-review
→ audited-defer refresh / retirement
→ targeted duplicate audits
→ learner quarantine check
→ Completion Recheck
→ NextBatch = 0
→ final Stage-A seal
```

---

## 9. Stage-B state — OLD SNAPSHOT, GATED

`premerge/readiness.json` 仍是旧的 7535-occurrence snapshot，不是当前 Phase-A1 authority。

```text
ReadyForPremergeReview     = false
StageBMutationAuthorized   = false
StableThirdPartyIDMinted   = false
MergeAuthorizedRows        = 0
```

SOURCE FREEZE + Phase A2 final closure 前，不刷新或解释该旧 snapshot 为当前 readiness。

---

## 10. Frozen boundaries

```text
Source Fact ≠ Vocabulary Identity ≠ Learner Admission ≠ Anki state
Source Grade ≠ LearnerLevel
exact MatchKey equality != same-sense decision
proposal != durable decision
reconciliation != merge authorization
```

- actual textbook evidence > third-party dictionary gloss；
- Stable NoteID 不得重编号、复用或漂移；
- Stage A / reconciliation workflow 不得修改 Klose Master/Learner/Release/Publish/Anki；
- reconciliation closure + independent Completion Recheck + explicit human gate 前不得 mint Stable NoteID。
