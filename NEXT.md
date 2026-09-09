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

## 2. Current execution phase — Phase A1 Source Adapter Bulk Ingestion

当前执行策略已经冻结为：

```text
Phase A1 — Source Adapter Bulk Ingestion
→ SOURCE FREEZE
→ Phase A2 — Global Identity Closure
→ final Stage-A seal
→ Stage B / Klose reconciliation
```

**当前不要先处理 `program / programme`。**

原因：还有计划中的第三方教材 Adapter 未接入。后续 Adapter 会继续增加 occurrence/context；如果现在逐 Adapter 清空 semantic blocker，会造成 multipart / canonicalization / audited-defer 的重复 reopen 和无效 fingerprint churn。

当前吞吐目标：

```text
最大安全 Source throughput
+ 最少重复 Identity review
+ 最少无效 Stage-A / Stage-B 重算
```

完整规则：

```text
docs/THIRD_PARTY_SOURCE_FIRST_EXECUTION.md
```

---

## 3. Existing enabled Adapter baseline — 8 CLOSED

```text
beijing_start1   =  808 occurrences /  734 MatchKeys / 12 books
beishida_start1  =  925 occurrences /  798 MatchKeys / 12 books
hujiao_start3    = 1111 occurrences / 1067 MatchKeys /  8 books
jijiao_start3    =  605 occurrences /  510 MatchKeys /  8 books
renjiao_start1   =  908 occurrences /  802 MatchKeys / 12 books
renjiao_start3   =  851 occurrences /  818 MatchKeys /  8 books
waiyan_start1    = 1170 occurrences / 1071 MatchKeys / 12 books
waiyan_start3    = 1157 occurrences / 1023 MatchKeys /  8 books
---------------------------------------------------------------
Total            = 7535 source occurrences / 80 books
```

8/8 已满足 Source-only contract：

```text
Raw XLSX
→ prepare_third_party_<SourceID>.py
→ source_reference/<SourceID>_staging/occurrences.csv
→ check_third_party_<SourceID>.py
→ check_third_party_source_adapters.py
→ generic corpus rebuild
```

最终已验证：

```text
Stage-A Workflow #299 / 34292534943 = SUCCESS
8 adapter parsers                 = PASS
8 adapter validators              = PASS
global adapter closure            = PASS
single automated workflow owner   = PASS
Corpus Completion Recheck         = PASS
Learner quarantine check          = PASS
Audit-batch Recheck               = PASS
Klose isolation                   = PASS
Stage-A seal                      = PASS
```

当前 8 个 Adapter 没有 Source/Adapter blocker。

---

## 4. NEXT TASK — add next Source Adapter

下一步继续 Phase A1，不进入 Identity closure。

优先接入：

```text
beishida_start3
```

repo raw source 已确认存在北师大三年级起点小学序列，范围应只包含：

```text
3年级上 / 3年级下
4年级上 / 4年级下
5年级上 / 5年级下
6年级上 / 6年级下
```

共 8 册。不得混入北师大一年级起点、初中或高中文件。

Per-Adapter Definition of Done：

```text
1. dedicated parser
2. dedicated edition-specific checker
3. books / occurrences / MatchKeys baseline frozen
4. standard occurrence schema
5. SourceOccurrenceKey adapter 内唯一 + cross-adapter no collision
6. SourceID / Grade / Semester / SourceBook / SourceFile / SourceRow 正确
7. source_adapters.csv enable
8. global adapter closure PASS
9. corpus rebuild PASS
10. existing Source Fact no unexpected drift
11. Klose Master/Learner/Release/Publish/Anki unchanged
```

达到以上条件后直接进入下一个计划 Adapter。

### Phase A1 中不要求先清零

以下项目**不阻止**继续下一个 Adapter：

```text
semantic review queue
program / programme
multipart unresolved
Vocabulary / Expression boundary
current-context audited-defer
orthographic / morphology canonicalization
Stage-B premerge ReadyForPremergeReview=false
```

但如果这些问题实际暴露 parser/source mapping 错误，则立即升级为 Source blocker，当场修复。

---

## 5. Current Identity state — carry forward, DO NOT close yet

当前 machine state仍可作为 corpus 观察值，但不是 Phase-A1 exit gate：

```text
Source occurrences                 = 7535
Normalized surfaces                = 2362
Durable Identity decisions         = 2411
Identity Vocabulary Preview        = 2039
Learner Vocabulary Preview         = 2024
Real residual semantic blockers    = 20 audited-defer
Targeted active Identity audit     = program
Evidence-changed surfaces          = 0
Multipart resolved                 = 35
Grammar-form quarantine gates      = 61
```

20 个 current-context audited-defer：

```text
fan / feel / flies / french / get / kind / letter / light / like / line /
little / mouse / pass / plant / put up / right / sound / square / too / watch
```

`program / programme` 以及上述 20 项全部留到 SOURCE FREEZE 后的 Phase A2 统一处理，除非新 Adapter evidence 明确把某项变成 Source defect。

---

## 6. SOURCE FREEZE gate

在所有计划第三方小学教材 Adapter 完成前：

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

## 7. Phase A2 — Global Identity Closure

SOURCE FREEZE 后，对最终 corpus 一次性完成：

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

只有到这里，`program / programme` 等 Identity 问题才作为最终 closure 工作处理。

---

## 8. Stage-B state — CURRENT BUT GATED

当前 premerge snapshot 与当前 Stage-A seal 一致，但 Phase A1 尚未完成，因此只能作为 fail-closed derived state：

```text
SourceOccurrences          = 7535
StageAIdentityCandidates   = 2039
StageALearnerCandidates    = 2024
AuditedDeferredSurfaces    = 20
KloseActiveNoteIDs         = 901
exact-multiple             = 7
exact-single               = 811
no-existing-match          = 1221
ReadyForPremergeReview     = false
StageBMutationAuthorized   = false
StableThirdPartyIDMinted   = false
MergeAuthorizedRows        = 0
```

即使某次中间 Stage-A `NextBatch=0`，也不能在 SOURCE FREEZE 前把它当成最终 Stage-B readiness。

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
- Stable NoteID 不得重编号、复用或漂移；
- Stage A / reconciliation workflow 不得修改 Klose Master/Learner/Release/Publish/Anki；
- reconciliation closure + independent Completion Recheck + explicit human gate 前不得 mint Stable NoteID。
