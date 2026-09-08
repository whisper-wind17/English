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
docs/THIRD_PARTY_VOCABULARY_MINIMAL_IDENTITY.md
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

## 2. Klose operational baseline

```text
Vocabulary Deck    = Klose-English::Vocabulary
Total Notes/Cards  = 638
Unsuspended        = 221
Suspended          = 417
New/day            = 8
FSRS               = ON / 90%
Stable Registry    = 901 active identities
Expressions Stable = 66
```

GitHub 管 Source / Identity / Learner / Review / Release；Anki 管 FSRS / Review History / Due / Interval / Card State。

当前 Third-party 工作仍不得修改 Klose Master/Learner/Release/Publish/Anki，不得 mint Stable NoteID。

---

## 3. Third-party Source Adapter phase — CHECKPOINTED / CLOSED

当前 8 个 enabled adapters：

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

统一 Source-only contract：

```text
Raw XLSX
→ prepare_third_party_<SourceID>.py
→ source_reference/<SourceID>_staging/occurrences.csv
→ check_third_party_<SourceID>.py
→ check_third_party_source_adapters.py
→ generic corpus builder
```

Machine-enforced：

- 8/8 adapters 有 dedicated prepare + checker；
- 8/8 raw source families、adapter tools、config、8 个 occurrence outputs 均触发统一 Stage-A rebuild；
- 8 个 edition-specific validators + global closure gate 每次运行；
- occurrence schema / SourceID / SourceOccurrenceKey closure PASS；
- adapter 内和跨 adapter occurrence key 无冲突；
- adapter output 不携带 Klose NoteID matching / Identity / Learner / Release state；
- Beijing 已从旧 Klose pre-merge generator 分离为独立 source-only parser；重建保持 808 / 734，Source truth 无漂移；
- Waiyan start1/start3 各有 2 条原 XLSX 空 `Definition`，属于合法 Source Fact，不在 adapter 层补写；
- 自动 adapter writer 已收敛为 **single owner**：`.github/workflows/prepare-third-party-renjiao-start1.yml`；
- 已退役三个重复/legacy writer：
  - `prepare-klose-beijing-vocabulary.yml`
  - `prepare-third-party-beishida-start1.yml`
  - `prepare-third-party-jijiao-start3.yml`
- `check_third_party_source_adapters.py` 现在强制 single-owner，不允许上述 legacy workflow 重新出现。

最终验证：

```text
29f05a8bf269506e1d57941ac9bf8569c6700a08
ci: enforce single-owner adapter workflow

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
bot persist                       = e4891f920debb2f39f09006365c753b84f55216d
```

Adapter phase 已无结构性遗留问题。后续 20 个 residual semantic blockers 是 Identity/source-context limitation，不属于 adapter defect。

---

## 4. Current Stage-A state — SEALED, one Identity audit active

```text
Source occurrences                 = 7535
Normalized surfaces                = 2362
Durable Identity decisions         = 2411
Identity Vocabulary Preview        = 2039
Learner Vocabulary Preview         = 2024
Real review_queue blockers         = 20
Machine review workload            = 21   # 20 audited-defer + program audit
Evidence-changed surfaces          = 0
Multipart resolved                 = 35
Grammar-form quarantine gates      = 61
NextBatch SelectedCount            = 1
NextBatch MatchKey                  = program
ExecutionReady                     = true
```

Current seal：

```text
StatusVersion         = stage-a-status-v2
CheckpointFiles       = 10
CheckpointFingerprint = eadb2d5163ff3193cc735b834a20dcec393df51f8d9d48867f93b5532060a556
SealedInputCommit     = 29f05a8bf269506e1d57941ac9bf8569c6700a08
Workflow              = #299 / 34292534943
```

20 个真实 residual blockers：

```text
fan / feel / flies / french / get / kind / letter / light / like / line /
little / mouse / pass / plant / put up / right / sound / square / too / watch
```

全部已按 current context machine-stamped 为 `audited-defer`。不得为了 blocker=0 猜 occurrence partition。

---

## 5. Stage-B premerge — CURRENT BUT GATED

Adapter 扩容后发现并修复了一个下游 fail-open 风险：旧 premerge builder 把 `SourceOccurrences=6005` 硬编码，且当 Stage A 重新出现 active batch 时会让 readiness workflow 失败，从而残留旧 `Ready=true` snapshot。

现已改为 `third-party-stage-b-readiness-v2`：每次 snapshot 必须绑定当前 Stage-A seal；即使 Stage A 未闭合，也要生成 **current but gated** 状态，不能保留旧 ready 状态。

当前 machine state：

```text
StageAStatusVersion       = stage-a-status-v2
StageACheckpointFingerprint = eadb2d5163ff3193cc735b834a20dcec393df51f8d9d48867f93b5532060a556
SourceOccurrences         = 7535
StageAIdentityCandidates  = 2039
StageALearnerCandidates   = 2024
AuditedDeferredSurfaces   = 20
KloseActiveNoteIDs        = 901
exact-multiple            = 7
exact-single              = 811
no-existing-match         = 1221
ActiveReviewBatch         = true
ReadyForPremergeReview    = false
StageBMutationAuthorized  = false
StableThirdPartyIDMinted  = false
MergeAuthorizedRows       = 0
```

Validation：

```text
Stage-B readiness workflow #5 / 34292245929 = SUCCESS
bot persist = cdd6d77c234a82b857449aec5db37b4d2cd9dd6c

Stage-B reconciliation workflow #5 / 34292266672 = SUCCESS
premerge current snapshot check = PASS
durable reconciliation check    = SKIPPED BY GATE
Klose isolation                  = PASS
```

因此当前 `premerge/` 已不是 stale；它是当前且可信的 derived snapshot，但 **禁止开始 Stage-B reconciliation**，直到 Stage-A `program` batch 完成并产生 `ReadyForPremergeReview=true`。

历史 reconciliation decisions 只能作为 review evidence；当前 Stage-A fingerprint/candidate fingerprint 未重新绑定前不得消费。

---

## 6. NEXT TASK — resolve `program / programme`

Adapter phase 已完成。Stage A 现在只剩一个 active deterministic batch：

```text
program
```

Targeted orthographic audit 发现：

```text
program   = 节目；节目单
programme = 节目；电视节目
```

两边 source context 均指向 media/event programme learner unit；这是 US/UK orthographic variation，不应保留两个 Vocabulary identities。

预期 adjudication：

```text
program → reuse-identity → programme
```

仍必须走当前 deterministic batch contract：

```text
selected_review_packet
→ decision_updates.csv
→ selected batch closure 100%
→ apply
→ corpus / learner rebuild
→ independent Completion Recheck
→ Klose isolation
→ seal + persist
```

Targeted audit `AutoApply=no`；不要直接编辑 `identity_decisions.csv`。

完成标准：

```text
NextBatch SelectedCount = 0
ExecutionReady = false
EvidenceChangedSurfaces = 0
20 residual blockers remain audited-defer
program/programme = one learner Identity
Stage-B premerge regenerates current READY snapshot
ReadyForPremergeReview = true
```

---

## 7. Frozen rules for next phase

```text
Source Fact ≠ Vocabulary Identity ≠ Learner Admission ≠ Anki state
Source Grade ≠ LearnerLevel
exact MatchKey equality != same-sense decision
proposal != durable decision
proposal != merge authorization
```

- Singleton occurrence growth does not itself reopen Identity semantics.
- Multipart OccurrenceKeys remain semantic partition truth; non-empty + disjoint + complete required.
- actual textbook evidence > third-party dictionary gloss.
- learner quarantine remains independent from Identity reconciliation.
- DO NOT mint Stable ThirdPartyID / NoteID before reconciliation closure + independent recheck + explicit human gate.
- DO NOT modify Klose Master/Learner/Release/Publish/Anki from Stage-A or reconciliation workflows.
