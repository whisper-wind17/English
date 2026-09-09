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

**当前不要处理 Identity review batch，包括 `program / programme`。**

原因：还有计划中的第三方小学教材 Adapter 未接入。后续 Adapter 会继续增加 occurrence/context；如果现在逐 Adapter 清空 semantic blocker，会造成 multipart / canonicalization / audited-defer 的重复 reopen 和无效 fingerprint churn。

完整规则：`docs/THIRD_PARTY_SOURCE_FIRST_EXECUTION.md`。

---

## 3. Existing enabled Adapter baseline — 9 CLOSED

```text
beijing_start1   =  808 occurrences /  734 MatchKeys / 12 books
beishida_start1  =  925 occurrences /  798 MatchKeys / 12 books
beishida_start3  =  699 occurrences /  663 MatchKeys /  8 books
hujiao_start3    = 1111 occurrences / 1067 MatchKeys /  8 books
jijiao_start3    =  605 occurrences /  510 MatchKeys /  8 books
renjiao_start1   =  908 occurrences /  802 MatchKeys / 12 books
renjiao_start3   =  851 occurrences /  818 MatchKeys /  8 books
waiyan_start1    = 1170 occurrences / 1071 MatchKeys / 12 books
waiyan_start3    = 1157 occurrences / 1023 MatchKeys /  8 books
---------------------------------------------------------------
Total            = 8234 source occurrences / 88 books
```

`beishida_start3` 已完成 Source-only contract：

```text
8 raw books / 699 occurrences / 663 MatchKeys
parser                         = PASS
dedicated edition checker      = PASS
global adapter closure          = PASS
Corpus Completion Recheck       = PASS
Learner quarantine check        = PASS
Audit-batch Recheck             = PASS
Klose isolation                 = PASS
Stage-A seal                    = PASS
Workflow #303 / 34296011755     = SUCCESS
CheckpointFingerprint           = a6d072381591e8bd6442a5594a71ef60c92e5e84902de5347781467a2508a5b9
```

自动生成提交 `3feae046f16c5193bdbdb58773da16fbaf37edef` 只刷新 Third-party Stage-A review/audit/learner/staging 文件；没有修改 Klose Master/Learner/Release/Publish/Anki，也没有改写既有 adapter source facts。

---

## 4. NEXT TASK — add `guangdong_start3`

下一步继续 Phase A1，不进入 Identity closure。

repo raw source 已确认 `广东版/` 存在完整三年级起点小学序列：

```text
广东版三年级起点三年级上 / 下
广东版三年级起点四年级上 / 下
广东版三年级起点五年级上 / 下
广东版三年级起点六年级上 / 下
```

共 8 册。Adapter ID：

```text
guangdong_start3
```

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
9. corpus rebuild + Completion Recheck PASS
10. existing Source Fact no unexpected drift
11. Klose Master/Learner/Release/Publish/Anki unchanged
```

达到以上条件后直接进入下一个计划 Adapter。

### Phase A1 中不要求先清零

以下项目不阻止继续下一个 Adapter：

```text
semantic / policy review queue
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

当前 sealed machine state：

```text
Source occurrences                 = 8234
Normalized surfaces                = 2405
Durable Identity decisions         = 2411
Identity Vocabulary Preview        = 1995
Learner Vocabulary Preview         = 1981
Review blockers                    = 86
Evidence-changed surfaces          = 25
Multipart resolved                 = 13
Grammar-form quarantine gates      = 61
```

当前 planner 选择的是 policy-review batch：

```text
eggs / flowers / fruits / left / cookies / birds / her
```

这是新增 source evidence 产生的 Identity-layer 工作，**Phase A1 暂不执行**。`program / programme` 同样继续 gated，统一留到 SOURCE FREEZE 后 Phase A2。

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

---

## 8. Stage-B state — CURRENT BUT GATED

`premerge/readiness.json` 仍是前一轮 7535-occurrence snapshot；Phase A1 source ingestion 后不会把它当作当前 authority。当前 Stage-A seal 已是 8234 occurrences，但 Stage B 仍保持 fail-closed：

```text
ReadyForPremergeReview     = false
StageBMutationAuthorized   = false
StableThirdPartyIDMinted   = false
MergeAuthorizedRows        = 0
```

SOURCE FREEZE + Phase A2 final closure 前，不刷新或解释该旧 premerge snapshot 为当前 readiness。

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
