# Third-party Vocabulary Allocation / Migration Plan

## Purpose

Stage-B reconciliation、allocation/migration plan、third-party source provenance contract、mutation-disabled dry run 与 guarded allocator simulation 均已完成当前阶段验证。**Actual Stable NoteID allocation / merge 仍未授权、未执行。**

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
anki/klose/third_party_vocabulary/allocation/authorization.json
anki/klose/third_party_vocabulary/provenance/contract.json
```

Validation / execution entries：

```text
tools/check_third_party_allocation_plan.py
tools/validate_third_party_source_provenance.py
tools/build_third_party_allocation_dry_run.py
tools/validate_third_party_allocation_dry_run.py
tools/apply_third_party_allocation.py
tools/validate_third_party_allocation_simulation.py
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

任何 Stage A、Stage-B decision 或 Stable Registry 变化都会令 plan / authorization stale。即使 max NoteID 没变，只要 registry blob 变化也必须重新验证。

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

若当前 frozen registry 获得用户显式 mutation 授权，当前 hypothetical append-only 区间为：

```text
current max        = KV001194
hypothetical first = KV001195
hypothetical last  = KV003015
count              = 1821
reserved           = false
```

任何 Stable Registry 变化都使该区间失效。实际 allocator 必须先验证 exact committed truth boundary，禁止把该区间当作永久预留号段。

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

stable retry origin：

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

20 个 third-party adapter occurrence 当前没有 `SourceEdition`。系统不制造 `unknown / unverified` 假 edition，而是明确区分：

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

未来新 Stable identity 的 origin：

```text
PrimaryOriginKey  = third-party-vocabulary|<ProvisionalIdentityKey>
CreatedSource     = third-party-vocabulary
CreatedSourceBook = external-evidence-corpus
```

这表示 identity 创建来源是冻结的 third-party evidence corpus，不声称某一教材 revision。

因此 missing SourceEdition 不阻止 Stable Identity allocation 本身，但继续严格阻止：

```text
unverified third-party occurrence
→ anki/klose/master/source_identity_extensions.csv
```

只有后续拿到可验证 SourceEdition / Revision evidence，才能增加 Master Textbook Source Fact；external evidence 仍保留，不删除。

详细契约：`docs/THIRD_PARTY_SOURCE_PROVENANCE_CONTRACT.md`。

---

## 4. External-evidence binding

实际 allocation 被授权并完成后，third-party evidence 与 NoteID 的关系写入独立层：

```text
anki/klose/third_party_vocabulary/provenance/stable_evidence_bindings.csv
```

schema：

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

该文件当前仍不存在；在 actual allocation 未授权前不得提前产生 repo truth binding。

当前 dry run 精确得到：

```text
external evidence bindings = 15791
held source occurrences     = 993
```

15791 只覆盖 Stage-B `reuse-existing + new-stable-identity`；96 个 held 对应的 993 个 source occurrences 不绑定 NoteID。

---

## 5. Mutation-disabled dry run — VALIDATED / CHECKPOINTED

Dry-run builder：

```text
tools/build_third_party_allocation_dry_run.py
```

只允许输出到 repo 外目录；repo-local output 会 fail closed。

独立 validator：

```text
tools/validate_third_party_allocation_dry_run.py
```

它不读取 builder 的内部中间状态，而是独立重建 Stage-A canonical eligibility，包括：

```text
valid single decision
resolved multipart
#variant scoped reuse
canonical blocker precedence
exact occurrence ownership
```

这一点很重要：durable reviewed alias 不等于当前一定 materialize 到 Vocabulary Preview。曾发现 13 个 alias / multipart subgroup 若只按 `reviewed` 判断会被错误多算；最终 builder 和 independent validator 都严格复刻 Stage-A Preview eligibility 后闭合。

Validation run：

```text
34587553210 / PASS
```

结果：

```text
identity actions                  = 2820
reuse-existing                    = 903
hypothetical new identities       = 1821
held                              = 96
hypothetical registry append      = 1821
hypothetical NoteID range         = KV001195..KV003015 / NOT RESERVED
external evidence bindings        = 15791
held source occurrences           = 993
repository mutation               = no
```

---

## 6. Guarded mutation-capable allocator — VALIDATED / UNAUTHORIZED

Mutator：

```text
tools/apply_third_party_allocation.py
```

默认 repository authorization：

```text
anki/klose/third_party_vocabulary/allocation/authorization.json
Authorized = false
```

同时 allocation plan 当前 mutation gates 全部为 false。

实际 `--apply` 只有在 **authorization manifest + plan mutation gates** 同时显式进入 authorized state，且 exact truth blobs 仍匹配时才可能继续。当前直接执行 `--apply` 会被拒绝。

Actual apply 的硬编码 write scope 只有：

```text
anki/klose/master/note_registry_extensions.csv
anki/klose/third_party_vocabulary/provenance/stable_evidence_bindings.csv
```

它不会写：

```text
anki/klose/master/source_identity_extensions.csv
anki/klose/learner/
anki/klose/publish/
anki/klose/anki/
anki/klose/expressions/
```

### Simulation evidence

Guarded mutator 已在 repo 外临时目录完成完整模拟：

```text
validation run                    = 34588197818 / PASS
simulated new Stable rows         = 1821
simulated extension rows          = 2213
simulated full Stable NoteIDs     = 3015
simulated evidence bindings       = 15791
hypothetical range                = KV001195..KV003015 / NOT RESERVED
repository mutation               = no
```

### Fail-closed authorization

CI 直接调用 unauthorized `--apply`，必须返回失败；该 adversarial path 已 PASS。

### Interrupted transaction recovery

模拟：

```text
registry append 已存在
stable_evidence_bindings.csv 缺失
```

然后 retry 同一 mutator。结果：

```text
existing 1821 Stable origins recognized
new registry rows on retry = 0
missing evidence bindings  = restored to 15791
final simulated state      = exact expected state
```

### Idempotent retry

完整状态再次执行 simulation：

```text
new registry rows = 0
extension rows    = 2213
bindings          = 15791
```

说明 current origin-key based retry 在一致状态下是幂等的；任何 origin/NoteID/identity field 冲突都会 fail closed。

---

## 7. Future authorized mutation transaction

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
authorization manifest explicitly enabled with user evidence
```

然后 transaction 只做 identity + external evidence binding：

```text
903 reuse-existing
  -> no Stable Registry row change
  -> write external evidence bindings

1821 new-stable-identity
  -> append-only NoteID allocation
  -> write external evidence bindings

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

Actual mutation 后必须立即做独立 Completion Recheck，再进入任何 learner/release 工作。

---

## 8. Retry, recovery, rollback and concurrency

Allocator 对 committed state 使用 append-only + stable origin key 幂等策略。

成功后 rerun 应识别已有 allocation 并产生零新增 NoteID；registry-only partial state 可以通过 retry 补齐 evidence binding。冲突状态必须 fail closed，不能另分配一个 NoteID。

错误 allocation 的 rollback **不能删除后重用 NoteID**。如实际 mutation 后发现内容错误，应通过 status / explicit identity migration 修正并保留 audit trail。

并发 Stable Registry 变化会改变 registry blob，从而使 plan + authorization stale；apply 会在写入前拒绝旧 truth boundary。

---

## 9. Learner / release / Anki separation

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

## 10. Validation checkpoint and current gate

Validation evidence：

```text
initial plan validation               = 34584336799 / PASS
post-fix final plan validation         = 34584719664 / PASS
provenance contract validation         = 34585155788 / PASS
allocation dry-run validation          = 34587553210 / PASS
guarded mutator + state-transition     = 34588197818 / PASS
```

最终 current pre-mutation state：

```text
allocation plan                       = CHECKPOINTED
provenance contract                   = CHECKPOINTED
dry-run allocator                     = VALIDATED / CHECKPOINTED
guarded mutation-capable allocator    = VALIDATED / CHECKPOINTED
actual allocation                     = NOT AUTHORIZED / NOT STARTED
Stable registry current active Notes  = 1189
current max NoteID                    = KV001194
current Vocabulary release            = 972
Master textbook mapping mutation      = none
Learner / Release / Publish mutation  = none
Anki mutation                         = none
```

Actual mutation gates 保持：

```text
ActualMutationAuthorized               = false
StableNoteIDAllocationAuthorized       = false
MasterSourceMappingMutationAuthorized  = false
LearnerMutationAuthorized              = false
ReleaseMutationAuthorized              = false
PublishMutationAuthorized              = false
AnkiMutationAuthorized                 = false
```

因此当前技术准备已收敛到 mutation-ready 状态。**剩余硬 blocker 是用户对 actual third-party Stable NoteID allocation / merge 的明确授权。** 在该授权出现前，不修改 Stable Registry。
