# Third-party Vocabulary Allocation / Migration Plan

## Purpose

Stage-B reconciliation is closed against the current Klose Stable Vocabulary boundary. Allocation/migration planning and the third-party source provenance contract are both CHECKPOINTED, but **actual Stable NoteID allocation / merge remains unauthorized**.

Current authoritative boundary:

```text
Stage-A checkpoint                = c6083db4da4437a77fa9b9723ffb510bd11e6ecc34f8184e8bc8d578ce4659cd
Klose active Stable NoteIDs       = 1189
persistent registry rows          = 1194
current max NoteID                = KV001194
Stage-B candidates / decisions    = 2820 / 2820
reuse-existing                    = 903
new-stable-identity proposal      = 1821
held                              = 96
learner-excluded held             = 26
review queue / selected batch     = 0 / 0
```

Machine contracts：

```text
anki/klose/third_party_vocabulary/allocation/plan.json
anki/klose/third_party_vocabulary/provenance/contract.json
```

Validation entries：

```text
tools/check_third_party_allocation_plan.py
tools/validate_third_party_source_provenance.py
```

---

## 1. Truth boundary and invalidation

Allocation plan 只对 exact closed Stage-B truth 与 exact current Stable Registry 有效，绑定：

```text
StageACheckpointFingerprint
reconciliation_decisions.csv Git blob SHA
identity_candidates.csv Git blob SHA
note_registry.csv Git blob SHA
note_registry_extensions.csv Git blob SHA
```

任何 Stage A、Stage-B decision 或 Stable Registry 变化都会令 plan stale。即使 max NoteID 没变，只要 registry blob 变化也必须重新验证。

当前没有预留任何 NoteID。

---

## 2. Three Stage-B action classes

### `reuse-existing` — 903

未来授权执行时：

```text
Stable Registry mutation = none
ExistingNoteID           = Stage-B reviewed NoteID
```

只允许在 provenance/evidence layer 建立第三方 evidence 与现有 NoteID 的关系；不得为同一 learning unit 再分配 NoteID，不得为了匹配第三方中文释义重写现有 CanonicalWord / MatchKey / SenseLabel，也不得顺带改变 learner/release state。

### `new-stable-identity` — 1821

这些是 reviewed future allocation proposals，不是已分配 identity。

若在当前 frozen registry 上获得用户显式 mutation 授权，理论 append-only 区间为：

```text
current max        = KV001194
hypothetical first = KV001195
hypothetical last  = KV003015
count              = 1821
reserved           = false
```

任何 Stable Registry 变化都使该区间失效。实际 allocator 必须从执行时 committed max 重新计算，禁止 force-push 预计算区间。

Allocation order 只用于确定性，不具有教学含义：

```text
sort by ProvisionalIdentityKey lexically
```

每条新 Stable row 只能来自当前 Stage-B proposal：

```text
CanonicalWord <- ProposedCanonicalWord
MatchKey      <- ProposedMatchKey
SenseLabel    <- ProposedSense
```

planned stable retry origin：

```text
third-party-vocabulary|<ProvisionalIdentityKey>
```

retry 时只有 NoteID 与 identity fields 完全一致才能视为 idempotent；任何冲突必须 fail closed。

### `held` — 96

`held` 是当前 evidence boundary 下的完整结果，不是待 allocation backlog：

```text
held -> no NoteID allocation
held -> no ExistingNoteID selection
held -> no evidence-to-Note binding
held -> no Master source promotion
```

只有新的 reviewed Stage-B decision 才能改变 held 状态。

---

## 3. Provenance architecture — CHECKPOINTED

此前 SourceEdition 是 allocation plan 的 blocker，因为 20 个 third-party adapter occurrence 没有 `SourceEdition`，而 Master source mapping 需要 `SourceID + SourceEdition + SourceItemKey`。

该 blocker 已通过 `docs/THIRD_PARTY_SOURCE_PROVENANCE_CONTRACT.md` 解决，方式不是制造 `unknown/unverified` 假 edition，而是明确区分：

```text
External Evidence Provenance
!=
Verified Textbook Source Fact
```

当前 third-party adapter 数据属于：

```text
external-evidence-provenance
EditionStatus = unverified
```

它可以支持 Stable Identity 判断，但：

```text
Stable Identity Allocation implies verified textbook provenance = false
```

未来新 Stable identity 的 planned origin 为：

```text
PrimaryOriginKey  = third-party-vocabulary|<ProvisionalIdentityKey>
CreatedSource     = third-party-vocabulary
CreatedSourceBook = external-evidence-corpus
```

这表示 identity 创建来源是冻结的 third-party evidence corpus，不声称某一教材 revision。

因此 **missing SourceEdition 不再阻止 Stable Identity allocation 本身**。它继续严格阻止：

```text
unverified third-party occurrence
→ anki/klose/master/source_identity_extensions.csv
```

只有后续拿到可验证 SourceEdition / Revision evidence，才能增加 Master Textbook Source Fact；external evidence 仍保留，不被删除。

---

## 4. Future external-evidence binding

实际 allocation 被授权并完成后，third-party evidence 与 NoteID 的关系写入独立层：

```text
anki/klose/third_party_vocabulary/provenance/stable_evidence_bindings.csv
```

planned schema：

```text
NoteID
ProvisionalIdentityKey
SourceOccurrenceKey
SourceID
SourceBook
Grade
Semester
SourceRow
SourceSnapshotFingerprint
EvidenceStatus
```

其中：

```text
EvidenceStatus = external-unverified-edition
SourceSnapshotFingerprint = frozen unified-occurrences fingerprint
```

该文件目前必须不存在；plan 阶段不得提前制造 NoteID binding。

---

## 5. Future authorized mutation transaction

用户未来明确授权 actual allocation/merge 后，执行前必须重新做 preflight：

```text
Stage-B closure = 2820 / 2820
review queue / selected = 0 / 0
all decisions current-fingerprint bound
allocation truth blobs == current blobs
provenance contract == current source freeze
registry active count / max == current plan baseline
all 903 reuse NoteIDs still active
all 1821 new proposals still valid against current registry
all 96 held still held
```

然后 transaction 只做 identity + external evidence binding：

```text
903 reuse-existing
  -> no Stable Registry row change
  -> build external evidence bindings

1821 new-stable-identity
  -> append-only NoteID allocation
  -> build external evidence bindings

96 held
  -> no mutation
```

本事务不得同时：

- 生成或审批 Learner Presentation；
- 修改 Learning Admission / LearningOrder；
- 写 Release Registry；
- 手工改 generated publish；
- 更新 Anki；
- 把 unverified evidence 写进 Master textbook source map。

---

## 6. Retry, rollback and concurrency

Allocator 必须对 committed state 幂等。

成功 commit 后 rerun 应通过 stable origin key 识别已有 allocation 并产生零新增 NoteID。partial/conflicting state 必须 fail closed，不能另分配一个 NoteID。

Git commit 是 transaction boundary。commit 前必须：

- 在内存中构建全部 registry/evidence-binding changes；
- 运行 persistent state checker、allocation checker、provenance checker；
- 证明既有 NoteID identity byte-for-byte stable；
- 证明 diff 只落在授权 identity/evidence files。

错误 allocation 的 rollback 不能复用 NoteID；应通过 status/migration history 修正并保留 audit trail。

并发 Stable Registry 变化会使 plan stale；执行时必须基于最新 main 重新 preflight。

---

## 7. Learner / release / Anki separation

Stable identity allocation 不等于 Klose 开始学习。

后续仍是独立 lifecycle：

```text
Stable Identity
→ Learner Presentation at LearnerLevel=4
→ Learning Admission + LearningOrder
→ content review / fingerprint approval
→ Release Registry
→ generated study.csv / anki-import.csv
→ Release Gate
→ Anki Update Existing Notes / add new Notes
```

当前 Vocabulary release 仍为 972 Notes。Allocation 阶段不得改变 Anki FSRS / Review History / Due / Interval / Card State。

Stage A 有 2794 learner candidates 也不代表 2794 条自动进入 release。

---

## 8. Validation checkpoint and current gate

Allocation plan validation：

```text
initial plan validation               = 34584336799 / PASS
post-fix final plan validation         = 34584719664 / PASS
```

Provenance contract validation：

```text
allocation/provenance validation      = 34585155788 / PASS
```

验证确认：

```text
registry persistent rows              = 1194
registry active NoteIDs               = 1189
registry max NoteID                   = KV001194
Stage-B closure                       = 2820 / 2820
reuse / new / held                    = 903 / 1821 / 96
hypothetical append range             = KV001195..KV003015 / NOT RESERVED
external-evidence adapters            = 20
external-evidence occurrences         = 18887
SourceEdition present in adapters     = no
unverified occurrence in Master map   = no
Master provenance promotion           = not authorized
validation workspace mutation         = no
```

此前 Stage-A workflow 的 `tools/check_third_party_*.py` 过宽触发 allocation checker，造成 metadata-only reseal。已由 `b8883e1b4d801567ae46decf503ea9a168cdd807` 排除 allocation checker；完整 Stage-A recheck `34584514294` PASS，content fingerprint 未变化。

当前 planning/provenance layer 已：

```text
IMPLEMENTED / VALIDATED / CHECKPOINTED
```

但 actual mutation gates 全部保持 false：

```text
ActualMutationAuthorized               = false
StableNoteIDAllocationAuthorized       = false
MasterSourceMappingMutationAuthorized  = false
LearnerMutationAuthorized              = false
ReleaseMutationAuthorized              = false
PublishMutationAuthorized              = false
AnkiMutationAuthorized                 = false
```

当前剩余实际 allocation blocker：

1. append-only allocator + `stable_evidence_bindings.csv` generator 尚未 IMPLEMENTED / VALIDATED；
2. 用户尚未显式授权 actual allocation / merge。

因此下一阶段可以继续 **实现 dry-run / mutation-disabled allocator 和 evidence-binding generator**，但不得执行 Stable Registry mutation。
