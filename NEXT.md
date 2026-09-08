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
→ anki/klose/third_party_vocabulary/audit/stage_a_status.json
→ anki/klose/third_party_vocabulary/premerge/readiness.json
→ anki/klose/third_party_vocabulary/premerge/identity_candidates.csv
→ anki/klose/third_party_vocabulary/premerge/audited_deferred.csv
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

## 3. Third-party Stage A — COMPLETE / SEALED

Enabled source baseline：

```text
beijing_start1   =  808
renjiao_start1   =  908
renjiao_start3   =  851
hujiao_start3    = 1111
waiyan_start1    = 1170
waiyan_start3    = 1157
Total            = 6005
Normalized       = 2161 surfaces
```

Current validated state：

```text
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

Stage A completion semantics：

```text
1892 reviewed provisional identities
→ eligible for Stage-B reconciliation

13 v6 audited defers
→ explicit unresolved carry-forward
→ excluded from Stage-B identity candidates
→ do not guess occurrence partitions merely to reach blocker=0
```

Residual audited defers：

```text
fan
flies
french
get
kind
letter
line
little
pass
plant
right
sound
too
```

`mouse` 已完整 resolve 为 `mouse#animal / mouse#computer`，不再属于 residual blocker。

---

## 4. FROZEN — Minimal Learner Identity v6

```text
Singleton MatchKey
→ Identity 内容稳定
→ OccurrenceKeys = provenance snapshot
→ additive source occurrence 自动重绑
→ 不重复 semantic review

Multipart MatchKey
→ OccurrenceKeys = semantic sense partition
→ non-empty + disjoint + complete 才 release
→ context 不足则 audited defer
```

核心不变量：

```text
Source Fact ≠ Vocabulary Identity ≠ Learner Admission ≠ Anki state
Identity 绑定 learning unit，不绑定教材 occurrence。
只有真实多义 Sense 才绑定 occurrence partition。
```

普通 singleton 只有 actual textbook 证明第二个 learner-relevant sense、source reconciliation / canonical / object-boundary 判断被证明错误，或显式 split/held/pending 时才 reopen。Dictionary 多义本身不是 reopen 条件。

---

## 5. Stage-A validated checkpoint seal — CHECKPOINTED

原 `stage_a_status-v1` 只记录 counts，无法证明 Stage-B 消费的 generated files 就是最后一次 validated Stage-A 内容。该 truth-boundary 缺口已修复。

Implementation：

```text
0f7a2f279741609dd965f916d58c57c71cb76c14
feat: seal validated third-party Stage-A checkpoint

f24d2133f7836c83408613f391051cd2bbc4614d
ci: seal validated third-party Stage-A checkpoint
```

`tools/seal_third_party_stage_a_checkpoint.py` 在以下 gate 全部 PASS 后执行：

```text
Corpus Completion Recheck
Learner grammar gate check
Audit-batch Completion Recheck
Klose isolation
→ seal stage-a-status-v2
→ bot persist
```

Sealed machine checkpoint：

```text
StatusVersion         = stage-a-status-v2
CheckpointFiles       = 10
FingerprintAlgorithm  = sha256-raw-bytes-v1
CheckpointFingerprint = 7ae428440b6f6e6298db8de2984da799179fef68e35ce2cd4022373e83afa0a0
```

Protected content boundary：

```text
config/source_adapters.csv
review/identity_decisions.csv
learner/grammar_form_quarantine.csv
staging/occurrences.csv
staging/surface_candidates.csv
staging/review_queue.csv
staging/unified_vocabulary_preview.csv
learner/learner_vocabulary_preview.csv
audit/defer_context.csv
audit/next_batch.json
```

Validation：

```text
Stage-A workflow #252 / 34238181554 = SUCCESS
bot persist = 8fa64d0...
```

Bot persist only changed `audit/stage_a_status.json`; Klose Master/Learner/Publish/Anki remained untouched.

---

## 6. Stage-B premerge readiness — CHECKPOINTED

Read-only premerge implementation：

```text
3a463f109981f770b8ebc99683cda10abb023545
feat: add third-party Stage-B premerge readiness

4fe04adfc1fe9f4988d38a2b7aff5af434cef73c
bot: data: refresh third-party Stage-B premerge readiness
```

Artifacts：

```text
anki/klose/third_party_vocabulary/premerge/identity_candidates.csv
anki/klose/third_party_vocabulary/premerge/audited_deferred.csv
anki/klose/third_party_vocabulary/premerge/readiness.json
```

Current readiness：

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

Important：exact MatchKey equality 只是 candidate signal，不是 same-sense decision。

Stage-B readiness 已绑定 Stage-A seal：

```text
ea79964e2dd3c6a7b6956a2ffca087696cdbc341
ci: bind Stage-B readiness to sealed Stage-A checkpoint
```

Stage-B workflow 在 build candidate map 前必须：

```text
verify stage-a-status-v2
→ recompute 10 SHA-256 fingerprints
→ require exact aggregate fingerprint match
→ require review/defer MatchKey uniqueness
```

Validation：

```text
Stage-B readiness workflow #2 / 34238313346 = SUCCESS
Stage-A seal fingerprint verified = 7ae42844...
Premerge identity coverage = 100%
Deferred surface coverage = 100%
Unknown Klose NoteID references = NO
Klose Master/Learner/Publish/Anki = UNTOUCHED
```

Premerge outputs were unchanged, therefore no new bot data commit was needed.

Independent compare `4fe04ad... → ea79964...` only changed：

```text
Stage-A workflow
Stage-B readiness workflow
stage_a_status.json
tools/seal_third_party_stage_a_checkpoint.py
```

No Klose identity/release/publish/Anki mutation occurred.

---

## 7. High-risk Stage-B candidate classes

Current 7 `exact-multiple` provisional identities must be reviewed before any bulk reconciliation：

```text
can
cook#person
cook#verb
free
milk
over
speak
```

Examples of why MatchKey-only merge is unsafe：

```text
can   → modal vs metal container
cook  → person vs verb
free  → spare-time vs no-cost
milk  → drink noun vs milk verb
over  → spatial relation vs finished
speak → language-speaking vs speaking/addressing
```

`cook#person` and `cook#verb` are two provisional identities over one source surface and therefore account for two of the 7 rows.

---

## 8. NEXT TASK — Stage-B Identity Reconciliation Contract

Do **not** mint NoteID yet.

先建立一个独立、可审计的 Stage-B reconciliation state machine，把 1892 provisional identities 映射到：

```text
reuse-existing
new-stable-identity
held/deferred
```

要求：

1. reconciliation decision truth 必须与 generated candidate map 分离；
2. 每个 decision 必须绑定 exact `ProvisionalIdentityKey` + 当前 Stage-A `CheckpointFingerprint`；
3. `exact-single` 仍需 sense confirmation，不能因 MatchKey 相等自动 merge；
4. `exact-multiple` 必须显式选择具体 existing NoteID 或 hold；优先先处理 7 条高风险；
5. `no-existing-match` 只能成为 new-identity candidate，未 review 前不得 mint NoteID；
6. 13 audited defers 不进入 reconciliation decisions，只从 `audited_deferred.csv` carry forward；
7. Identity reconciliation 覆盖全部 1892 Identity；Learner Admission 独立，15 个 learner-quarantined identities 仍可完成 identity reconciliation，但不得进入当前 learner release；
8. Stable NoteID allocation 必须 append-only，existing NoteID 永不重编号；
9. Source Identity Map / SourceEdition provenance 必须在正式 mutation 前有 machine gate；
10. Stage-B mutation、learner review、release/publish 必须继续分层，不能在同一步完成。

推荐 execution order：

```text
A. 定义 reconciliation_decisions schema + checker
B. 先 adjudicate 7 exact-multiple high-risk rows
C. 设计 exact-single sense-confirmation fast lane
D. 设计 no-existing-match new-identity review lane
E. 1892 reconciliation closure PASS
F. 生成 proposed stable NoteID allocation / source identity migration plan（仍 read-only）
G. 独立 Completion Recheck
H. 用户 gating 后才允许正式 Stage-B mutation
```

---

## 9. Frozen learner / release rules

- pure past / past-participle form：Identity 可 resolved，当前 learner quarantine；
- lexicalized adjective/noun 不得因词形误 gate；
- homograph learner gate 必须 DecisionKey-scoped；
- contractions 默认 Expressions；
- ordinary plural / 三单 / -ing 不自动 quarantine；
- irregular pedagogical forms 可按明确策略保留独立 Identity；
- actual textbook evidence > third-party dictionary gloss；
- Source Grade 与 LearnerLevel 独立；
- Stable NoteID append-only；
- generated publish 文件不得手工修改；
- existing Anki Review History 不得破坏。
