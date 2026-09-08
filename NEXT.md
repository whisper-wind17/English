# NEXT — Klose Learning

Last updated: 2026-09-08

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
→ anki/klose/third_party_vocabulary/premerge/readiness.json
→ anki/klose/third_party_vocabulary/premerge/identity_candidates.csv
→ anki/klose/third_party_vocabulary/premerge/audited_deferred.csv
→ anki/klose/third_party_vocabulary/reconciliation/reconciliation_decisions.csv
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

---

## 3. Stage A — COMPLETE / SEALED

```text
Source occurrences                 = 6005
Normalized surfaces                = 2161
Durable Identity decisions         = 2204
Identity Vocabulary Preview        = 1892
Learner Vocabulary Preview         = 1877
Review blockers                    = 13
Evidence-changed surfaces          = 0
Multipart resolved                 = 41
Grammar-form quarantine gates      = 60
NextBatch SelectedCount            = 0
ExecutionReady                     = false
```

13 个 residual blocker 是 Minimal Identity v6 下已审计的 source-context limitations，不是未处理 backlog：

```text
fan / flies / french / get / kind / letter / line / little / pass / plant / right / sound / too
```

这些 surface 保持 `split-required / held / audited-defer`，不得为了 blocker=0 猜 occurrence partition。

Stage-A machine seal：

```text
StatusVersion         = stage-a-status-v2
CheckpointFiles       = 10
FingerprintAlgorithm  = sha256-raw-bytes-v1
CheckpointFingerprint = 7ae428440b6f6e6298db8de2984da799179fef68e35ce2cd4022373e83afa0a0
```

Implementation / validation：

```text
0f7a2f279741609dd965f916d58c57c71cb76c14  feat: seal validated third-party Stage-A checkpoint
f24d2133f7836c83408613f391051cd2bbc4614d  ci: seal validated third-party Stage-A checkpoint
Workflow #252 / 34238181554 = SUCCESS
bot persist = 8fa64d0...
```

Seal 只有在 Corpus Completion Recheck、Learner checker、Audit-batch Recheck、Klose isolation 全部 PASS 后才生成。Stage-B 必须先验证 seal，再消费 Stage-A generated state。

---

## 4. Frozen Minimal Identity / learner rules

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

## 5. Stage-B premerge readiness — CHECKPOINTED

Read-only premerge artifacts：

```text
premerge/identity_candidates.csv
premerge/audited_deferred.csv
premerge/readiness.json
```

Current candidate state：

```text
Stage-A Identity candidates = 1892
Learner-admitted candidates = 1877
Audited deferred carry-forward = 13
Klose active NoteIDs = 901

exact-single       = 821
exact-multiple     = 7
no-existing-match  = 1064

ReadyForPremergeReview   = true
StageBMutationAuthorized = false
StableThirdPartyIDMinted = false
MergeAuthorizedRows      = 0
```

Implementation / validation：

```text
3a463f109981f770b8ebc99683cda10abb023545  feat: add third-party Stage-B premerge readiness
4fe04adfc1fe9f4988d38a2b7aff5af434cef73c  data: refresh third-party Stage-B premerge readiness
ea79964e2dd3c6a7b6956a2ffca087696cdbc341  ci: bind Stage-B readiness to sealed Stage-A checkpoint
Workflow #2 / 34238313346 = SUCCESS
```

Stage-B readiness 先重算 Stage-A 10 个 SHA-256 fingerprint；任何 sealed content 漂移直接 fail closed。

---

## 6. Stage-B reconciliation contract — CHECKPOINTED

Durable decision truth：

```text
anki/klose/third_party_vocabulary/reconciliation/reconciliation_decisions.csv
```

Contract / checker：

```text
docs/THIRD_PARTY_STAGE_B_RECONCILIATION.md
tools/check_third_party_stage_b_reconciliation.py
.github/workflows/third-party-stage-b-reconciliation.yml
```

Core contract：

```text
premerge candidate map = derived matching evidence
reconciliation_decisions.csv = durable reviewed decision truth
```

每条 durable decision 必须同时绑定：

```text
StageACheckpointFingerprint
+
CandidateFingerprint
```

前者保护 Stage-A identity truth；后者保护当前 Klose candidate NoteID / sense context。任一侧变化，旧 decision 必须失效并重审。

Allowed actions：

```text
reuse-existing
new-stable-identity
held
```

所有行当前强制：

```text
MutationAuthorized = no
```

不得在 reconciliation 阶段 mint NoteID、修改 Klose Master/Learner/Release/Publish/Anki。

Implementation：

```text
e86c5e7c03b6771164e07da98314d1fc5c09c30e
feat: establish Stage-B reconciliation decision contract
```

Validation：

```text
Workflow #1 / 34239573534 = SUCCESS
Stage-A seal verified = 7ae42844...
Premerge candidates = 1892
Durable decisions = 7
Exact-multiple coverage = 7 / 7 = 100%
reuse-existing = 4
new-stable-identity = 1
held = 2
overall reconciliation closure = 7 / 1892
Stage-B mutation authorized = NO
Stable NoteID minted = NO
Klose state mutated = NO
```

Independent compare `2cc267ec... → e86c5e7c...` 仅新增 reconciliation workflow / checker / contract doc / decision CSV；未修改 Klose Master/Learner/Publish/Anki。

---

## 7. Exact-multiple adjudication — FROZEN

```text
can
→ reuse KV000074 = 能；会；可以
→ KV000885 = 金属罐，明确不同 sense

cook#person
→ HELD
→ likely noun identity KV000424 仍是 legacy mixed SenseLabel“厨师；做饭”
→ KV000805 已承担 Klose actual Grade-4 verb“烹饪；煮”
→ 先清理 Klose stable identity boundary，再考虑 person reuse

cook#verb
→ reuse KV000805 = 烹饪；煮

free
→ reuse KV000502 = 空闲的
→ KV000876 = 免费的，明确不同 sense

milk
→ reuse KV000088 = 牛奶
→ KV000890 = 挤奶，明确不同 sense

over
→ new-stable-identity candidate
→ proposed sense = 在……上方；在……上面
→ KV000816 = 在……的远端（或对面）
→ KV000863 = 结束（的）
→ 两个 existing NoteID 均不等价；当前只形成 proposed identity，不 mint NoteID

speak
→ HELD
→ provisional broad sense = 说；讲；讲某种语言
→ 同时跨 KV000705 = 说/讲某种语言 与 KV000901 = 说话/发言
→ identity_migrations.csv 已明确批准两者 sense split
→ 不得任意二选一；需 occurrence-level reconciliation 或回到 Stage-A split
```

---

## 8. NEXT TASK — exact-single sense-confirmation fast lane

当前剩余 reconciliation：

```text
7 / 1892 closed
821 exact-single 尚待 sense confirmation
1064 no-existing-match 尚待 new-identity review
2 high-risk rows held: cook#person / speak
```

下一步先做 `exact-single` fast lane，但必须保持：

```text
exact MatchKey equality != same-sense decision
proposal != durable decision
proposal != merge authorization
```

推荐机制：

```text
A. 生成 derived exact-single proposal view
B. 每行绑定 Stage-A CheckpointFingerprint + CandidateFingerprint
C. 按 sense relation 分类，而不是只按 MatchKey：
   - exact/normalized same sense → high-confidence reuse proposal
   - narrow/broader but compatible → manual confirmation
   - conflicting/distinct sense → hold / new-identity review
D. proposal checker 必须保证只覆盖 exact-single current candidates
E. 不自动写 reconciliation_decisions.csv
F. 先抽样/审计高置信 proposals，确认规则无 false merge 后再批量 adjudicate
```

尤其不得把中文词义仅因字符串重叠就视为同一 Identity；应以 learner-relevant sense equivalence 为准。

---

## 9. Remaining Stage-B sequence

```text
1. exact-single proposal + validation
2. exact-single durable adjudication
3. no-existing-match new-identity review lane
4. 处理 held cook#person / speak
5. 1892 reconciliation closure PASS
6. read-only proposed Stable NoteID allocation / Source Identity migration plan
7. independent Completion Recheck
8. explicit human gate
9. 才允许正式 Stage-B identity mutation
10. Learner Review / Release / Publish / Anki 继续独立分层
```

仍然禁止：

```text
DO NOT mint Stable ThirdPartyID / NoteID before reconciliation closure + explicit gate.
DO NOT modify existing Stable NoteID numbering.
DO NOT modify Klose Master/Learner/Publish/Anki from reconciliation workflow.
DO NOT auto-merge exact-single by MatchKey alone.
DO NOT admit learner-quarantined identities into current learner release.
```
