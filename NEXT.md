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
→ anki/klose/third_party_vocabulary/audit/stage_a_status.json
→ anki/klose/third_party_vocabulary/audit/next_batch.json
```

**不要直接从旧 `premerge/` / `reconciliation/` 文件恢复 Stage B。** 当前 Stage-A source corpus 已从旧 6005-occurrence baseline 扩展到 7535；旧 Stage-B artifacts 必须在当前 Stage-A 最终 seal 后重新生成并校验。

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

---

## 3. Third-party Source Adapter phase — CHECKPOINTED

8 个 enabled adapters 已全部纳入同一 Source-only contract：

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

统一 contract：

```text
Raw XLSX
→ prepare_third_party_<SourceID>.py
→ source_reference/<SourceID>_staging/occurrences.csv
→ check_third_party_<SourceID>.py
→ check_third_party_source_adapters.py
→ generic corpus builder
```

Machine-enforced：

- 8/8 enabled adapters 均有 dedicated prepare + checker；
- 8/8 raw source families、adapter tools、config、8 个 generated occurrence outputs 都能触发 Stage-A source rebuild；
- 每次 Stage-A workflow 均执行 8 个 edition-specific validator + global adapter closure gate；
- occurrence schema 统一；SourceID closure PASS；adapter 内及跨 adapter `SourceOccurrenceKey` 无冲突；
- Source Adapter 不携带 Klose NoteID matching / Identity / Learner / Release state；
- Beijing 已从旧 Klose pre-merge generator 分离出独立 source-only parser；重新 parse 后仍为 808 / 734，`occurrences.csv` 无 Source truth drift；
- Beijing staging 内旧 pre-merge candidate/review 文件仅保留为历史审计，不被当前 Third-party Stage A / Stage B 消费；
- Waiyan start1 / start3 各有 2 条 source-native 空 `Definition`，均为 contraction / expanded-form 邻域中的原 XLSX 事实；不得在 adapter 层擅自补写 gloss。Edition-specific checkers接受该基线。

Validation / checkpoint：

```text
684113b7e4b377324bb2ef027b0a3499732a47ef
ci: trigger Stage A on every enabled adapter output

Workflow #298 / 34291873165 = SUCCESS
8 adapter parsers                 = PASS
8 adapter validators              = PASS
global adapter closure            = PASS
Corpus Completion Recheck         = PASS
Learner quarantine check          = PASS
Audit-batch Recheck               = PASS
Klose isolation                   = PASS
Stage-A seal                      = PASS
bot persist                       = ceec28315cde0bb94d9c3139e1fa6f160c4e133c
```

当前 adapter 层没有未处理的结构性 blocker。后续 residual semantic blockers 属于 Identity/source-context review，不应重新记为 adapter defect。

---

## 4. Current Stage-A machine state — SEALED, one targeted Identity audit active

```text
Source occurrences                 = 7535
Normalized surfaces                = 2362
Durable Identity decisions         = 2411
Identity Vocabulary Preview        = 2039
Learner Vocabulary Preview         = 2024
Real review_queue blockers         = 20
Machine review workload            = 21   # 20 blockers + program orthographic audit
Evidence-changed surfaces          = 0
Multipart resolved                 = 35
Grammar-form quarantine gates      = 61
NextBatch SelectedCount            = 1
NextBatch MatchKey                  = program
ExecutionReady                     = true
```

Stage-A machine seal：

```text
StatusVersion         = stage-a-status-v2
CheckpointFiles       = 10
FingerprintAlgorithm  = sha256-raw-bytes-v1
CheckpointFingerprint = eadb2d5163ff3193cc735b834a20dcec393df51f8d9d48867f93b5532060a556
SealedInputCommit     = 684113b7e4b377324bb2ef027b0a3499732a47ef
Workflow              = #298 / 34291873165
```

20 个真实 residual blocker 都已 machine-stamped 为 current-context `audited-defer`：

```text
fan / feel / flies / french / get / kind / letter / light / like / line /
little / mouse / pass / plant / put up / right / sound / square / too / watch
```

它们是当前 source evidence 无法安全完成 occurrence-level sense partition / object boundary 的限制，不是 adapter 漏解析，也不是未执行 review backlog。不得为了 blocker=0 猜义。

---

## 5. NEXT TASK — resolve `program / programme` targeted Identity audit

Adapter phase 完成后，Stage A 只剩 1 个 active deterministic batch：

```text
program
```

Targeted orthographic audit 对当前 corpus 的显式 US/UK pairs 做了 read-only 扫描，唯一发现的独立重复 identity 是：

```text
program   = 节目；节目单
programme = 节目；电视节目
```

两边实际 source context 均指向 media/event programme learner unit；这是 orthographic variation，不应保留两个 Vocabulary identities。

预期 adjudication：

```text
program → reuse-identity → programme
```

但仍必须通过当前 deterministic selected-batch contract：

```text
selected_review_packet
→ decision_updates.csv
→ batch closure 100%
→ apply
→ corpus/learner rebuild
→ independent Completion Recheck
→ Klose isolation
→ seal + persist
```

Targeted audit `AutoApply = no`；不要直接编辑 durable `identity_decisions.csv`。

完成后必须确认：

```text
NextBatch SelectedCount = 0
ExecutionReady = false
EvidenceChangedSurfaces = 0
20 residual blockers remain audited-defer
program/programme only one learner Identity
```

---

## 6. Frozen Minimal Identity / learner rules

```text
Source Fact ≠ Vocabulary Identity ≠ Learner Admission ≠ Anki state
```

- Singleton Identity 绑定 learning unit；OccurrenceKeys 只是 provenance snapshot，additive source occurrence 自动重绑。
- Multipart OccurrenceKeys 是 semantic partition，必须 non-empty + disjoint + complete 才 release。
- Dictionary 多义本身不是 reopen 条件。
- pure past / past-participle Identity 可 resolved，但当前 learner quarantine。
- lexicalized adjective/noun 不得误 gate；homograph learner gate 必须 DecisionKey-scoped。
- contractions 默认 Expressions；ordinary plural / 三单 / -ing 不自动 quarantine。
- actual textbook evidence > third-party dictionary gloss。
- Source Grade 与 LearnerLevel 独立。

---

## 7. Stage-B artifacts — STALE / DO NOT CONSUME YET

当前 `premerge/` / `reconciliation/` 文件来自较早 Stage-A checkpoint。已确认 `premerge/readiness.json` 存在内部新旧状态混合：

```text
SourceOccurrences          = 6005   # stale
StageAIdentityCandidates   = 2039
StageALearnerCandidates    = 2024
AuditedDeferredSurfaces    = 20
```

因此现有 Stage-B readiness 不是当前 7535-occurrence seal 的可信 machine state。

旧 Stage-B decisions 也绑定旧 `StageACheckpointFingerprint`，不能直接继续消费。历史 exact-multiple adjudication 可作为 review evidence，但必须在新的 Stage-B generation/checker 下重新绑定当前 Stage-A + CandidateFingerprint。

当前强制：

```text
DO NOT mint Stable ThirdPartyID / NoteID.
DO NOT modify existing Klose Stable NoteID numbering.
DO NOT modify Klose Master/Learner/Release/Publish/Anki.
DO NOT resume exact-single reconciliation from stale premerge artifacts.
```

---

## 8. After `program` — Stage-B restart sequence

```text
1. resolve program/programme and obtain final Stage-A NextBatch=0 seal
2. regenerate Stage-B premerge/readiness from the current sealed Stage A
3. verify all Stage-A checkpoint fingerprints before accepting new premerge state
4. regenerate candidate classes / counts from current 2038-ish post-dedup Identity Preview
5. revalidate historical reconciliation decisions against current CandidateFingerprint
6. only then resume exact-single sense-confirmation fast lane
7. no Stable NoteID mutation until reconciliation closure + independent Completion Recheck + explicit human gate
```

Stage B 仍坚持：

```text
exact MatchKey equality != same-sense decision
proposal != durable decision
proposal != merge authorization
```
