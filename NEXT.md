# NEXT — Klose Learning

Last updated: 2026-09-11

## 1. Current checkpoint

当前 Klose 主系统与第三方 Vocabulary 前置链路均已完成本阶段 checkpoint：

```text
Grade 5–6 Vocabulary GitHub Release   = IMPLEMENTED / VALIDATED / CHECKPOINTED
Vocabulary Anki Updated               = true / DEVICE IMPORT + SYNC USER-CONFIRMED

Grade 5–6 Expressions GitHub Release  = IMPLEMENTED / VALIDATED / CHECKPOINTED
Expressions Release Gate              = PASS
Expressions Anki Updated              = true / DEVICE IMPORT + SYNC USER-CONFIRMED

Third-party Stage-B reconciliation    = IMPLEMENTED / VALIDATED / CHECKPOINTED
Third-party provenance contract       = IMPLEMENTED / VALIDATED / CHECKPOINTED
Third-party allocation plan           = IMPLEMENTED / VALIDATED / CHECKPOINTED
Third-party allocation dry run        = IMPLEMENTED / VALIDATED / CHECKPOINTED
Guarded allocation mutator            = IMPLEMENTED / VALIDATED / CHECKPOINTED

Actual third-party allocation         = NOT AUTHORIZED / NOT STARTED
Actual third-party merge              = NOT AUTHORIZED / NOT STARTED
```

当前已经不是技术实现 blocker，而是明确的 **HOLD POINT**：

> 在用户明确授权执行 actual third-party Stable NoteID allocation / merge 之前，不修改 Stable Registry。

普通的：

```text
继续
继续处理
下一步
```

**不构成 actual allocation 授权。**

只有语义明确表达“授权执行第三方 Stable NoteID allocation / merge”的用户指令，才允许进入 authorization transition。

---

## 2. New-conversation startup order

凡继续 Klose Vocabulary / third-party allocation 任务，固定读取：

```text
AGENTS.md
→ NEXT.md
→ docs/THIRD_PARTY_ALLOCATION_MIGRATION_PLAN.md
→ docs/THIRD_PARTY_SOURCE_PROVENANCE_CONTRACT.md
→ docs/THIRD_PARTY_STAGE_B_RECONCILIATION.md
→ docs/KLOSE_VOCABULARY_SYSTEM.md
→ current anki/klose/master registries
→ anki/klose/third_party_vocabulary/allocation/plan.json
→ anki/klose/third_party_vocabulary/allocation/authorization.json
```

不要仅凭聊天历史推测是否已经授权 mutation。

---

## 3. Current Klose Stable Vocabulary / Anki checkpoint

```text
Stable Vocabulary active Notes                      = 1189
persistent registry rows incl. merged identities    = 1194
current max NoteID                                  = KV001194

Klose LearnerLevel                                  = 4
Learning Admission allowed                         = 627
Learning Admission held                            = 345
LearningOrder count / max                          = 627 / 627

released Vocabulary Notes                           = 972
learner review scope                                = 972
model-reviewed                                      = 972
pending                                             = 0

publish/study.csv                                   = 972 Notes
publish/anki-import.csv                             = 972 Notes
Vocabulary Anki Updated                             = true
```

Grade 5–6 source / identity checkpoint：

```text
source occurrences                                  = 509
reconciled provisional learning units               = 504
new Stable Notes                                    = 288
reused Stable Notes                                 = 144
unique Notes                                        = 432
```

当前 `note_registry_extensions.csv` 仍止于：

```text
KV001194 = dream / 梦
```

第三方 allocation 尚未向 Stable Registry 写入任何 NoteID。

Anki FSRS / Review History / Due / Interval / Card State 未被本轮第三方工作修改。

---

## 4. Grade 5–6 Expressions checkpoint

```text
source occurrences reviewed              = 153 / 153
mapped                                   = 138
source-only                              = 15
existing Stable KE groups reused         = 8
new Stable Expressions allocated         = 110
new ExpressionID range                   = KE000067..KE000176
Stable Expression registry total         = 176
publishable Expressions                  = 176
Expressions Anki Updated                 = true
```

现有 ExpressionID、FSRS / Review History 均保持稳定。

---

## 5. Third-party Stage A / Stage-B — CHECKPOINTED

Stage A：

```text
StageACheckpointFingerprint = c6083db4da4437a77fa9b9723ffb510bd11e6ecc34f8184e8bc8d578ce4659cd
source occurrences          = 18887
Vocabulary identities       = 2820
learner candidates          = 2794
audited deferred surfaces   = 52
explicit exclusions         = a / an / the
```

Stage-B 已针对当前 **1189 active Stable NoteIDs** 完成 sense-aware reconciliation：

```text
CandidateCount              = 2820
ValidDurableDecisionCount   = 2820
ReviewQueueCount            = 0
SelectedCount               = 0

reuse-existing              = 903
new-stable-identity         = 1821
held                        = 96
learner-excluded held       = 26 / 26
high-risk multiple decided  = 17 / 17
```

最终 Stage-B workflow：

```text
run    = 34581146513 / PASS
commit = 153dfabd258eafc039d8545c1ffd1e77f1a362ca
```

Stage-B durable decisions 仍全部：

```text
MutationAuthorized = no
Stable NoteID minted = no
Merge authorized = no
```

详细真源：`docs/THIRD_PARTY_STAGE_B_RECONCILIATION.md`。

---

## 6. Third-party provenance contract — CHECKPOINTED

20 个 third-party adapters / 18887 occurrences 当前属于：

```text
External Evidence Provenance
```

而不是：

```text
Verified Textbook Source Fact
```

当前 adapter occurrence schema 没有真实 `SourceEdition / Revision` 字段。

因此：

```text
External evidence may support Stable Identity allocation = yes
Stable Identity implies verified textbook provenance     = no
```

禁止把以下值伪装成教材版本：

```text
unknown
unverified
third-party
klose-current
```

也禁止根据文件名、Grade、start1/start3 或第三方整理标签猜 Edition。

未来 actual allocation 后，第三方 evidence 与 NoteID 的关系进入独立层：

```text
anki/klose/third_party_vocabulary/provenance/stable_evidence_bindings.csv
```

当前该文件 **不存在**；说明 actual binding 尚未发生。

只有未来拿到独立可验证 SourceEdition / Revision evidence 后，才允许把对应 occurrence promotion 到：

```text
anki/klose/master/source_identity_extensions.csv
```

当前：

```text
MasterSourceMappingMutationAuthorized = false
```

详细真源：`docs/THIRD_PARTY_SOURCE_PROVENANCE_CONTRACT.md`。

---

## 7. Allocation plan / dry run — CHECKPOINTED

Current allocation baseline：

```text
persistent registry rows      = 1194
active Stable NoteIDs         = 1189
max NoteID                    = KV001194
reuse-existing                = 903
new-stable-identity proposal  = 1821
held                          = 96
```

如果 registry truth 完全不变，1821 个 future-new proposal 的 deterministic hypothetical range 为：

```text
KV001195..KV003015
```

但该区间：

```text
Reserved = false
```

任何 Stable Registry 变化都会让当前 plan / authorization truth boundary stale，并要求重新计算。

Mutation-disabled dry run 已闭合：

```text
identity actions                  = 2820
reuse-existing                    = 903
hypothetical new identities       = 1821
held                              = 96
hypothetical registry append      = 1821
external evidence bindings        = 15791
held source occurrences           = 993
repository mutation               = no
```

Dry-run validation：

```text
run = 34587553210 / PASS
```

Dry-run builder / independent validator 已显式处理 Stage-A canonical eligibility：

```text
valid single decision
resolved multipart
#variant scoped reuse
canonical blocker precedence
exact occurrence ownership
```

不能把“durable reviewed alias”机械等价为“当前已 materialize Vocabulary identity”。

---

## 8. Guarded mutation-capable allocator — CHECKPOINTED / UNAUTHORIZED

执行工具：

```text
tools/apply_third_party_allocation.py
```

授权真源：

```text
anki/klose/third_party_vocabulary/allocation/authorization.json
```

当前：

```text
Authorized = false
UserAuthorizationEvidence = <empty>
AuthorizedAt = <empty>
```

当前 plan mutation gates：

```text
ActualMutationAuthorized              = false
StableNoteIDAllocationAuthorized      = false
MasterSourceMappingMutationAuthorized = false
LearnerMutationAuthorized             = false
ReleaseMutationAuthorized             = false
PublishMutationAuthorized             = false
AnkiMutationAuthorized                = false
```

Actual allocator 的硬编码 write scope 只有：

```text
anki/klose/master/note_registry_extensions.csv
anki/klose/third_party_vocabulary/provenance/stable_evidence_bindings.csv
```

禁止顺带修改：

```text
anki/klose/master/source_identity_extensions.csv
anki/klose/learner/
anki/klose/publish/
anki/klose/anki/
anki/klose/expressions/
```

Validation evidence：

```text
guarded mutator + recovery/idempotency        = 34588197818 / PASS
authorization-aware control-plane validation  = 34588814219 / PASS
final plan checkpoint revalidation             = 34589018187 / PASS
```

验证覆盖：

```text
unauthorized direct --apply rejected           = PASS
simulation initial new Stable rows             = 1821
simulated extension rows                       = 2213
simulated full Stable NoteIDs                  = 3015
simulated evidence bindings                    = 15791

registry-written / bindings-missing interruption recovery = PASS
retry new Stable rows after interruption                  = 0
idempotent full-state retry new Stable rows               = 0
repository mutation during validation                     = no
```

控制面支持两个显式状态：

```text
closed
  Authorized = false
  all mutation gates = false

authorized-pending-apply
  Authorized = true
  ActualMutationAuthorized = true
  StableNoteIDAllocationAuthorized = true
  Master / Learner / Release / Publish / Anki gates remain false
```

`Third-party Allocation Plan Validation` workflow 在两种状态下都 **只验证，不自动执行 `--apply`**。

---

## 9. Immediate next work — HOLD POINT

### 当前不要继续自动推进 actual allocation

技术准备已经到：

```text
mutation-ready
```

但业务状态仍是：

```text
unauthorized
```

因此下一步只有在用户明确授权后才能发生。

### 什么才算明确授权

必须是语义明确的 actual mutation 指令，例如：

```text
授权执行第三方 Vocabulary Stable NoteID allocation / merge
```

仅说：

```text
继续
继续处理
下一步
```

不得转换 `authorization.json`，不得改变 mutation gates，不得执行 Stable Registry mutation。

### 获得显式授权后才执行的 transition

1. 重新读取最新 main 与所有 truth boundary；
2. 确认 Stage-B 仍 2820/2820、queue=0；
3. 确认 current Stable Registry blob / max NoteID 与 plan 一致；
4. 重新运行 provenance / plan / dry-run validation；
5. 将 `authorization.json` 显式切到 `Authorized=true`，记录用户授权证据和时间；
6. 只把 plan gates 切为：

```text
ActualMutationAuthorized              = true
StableNoteIDAllocationAuthorized      = true
MasterSourceMappingMutationAuthorized = false
LearnerMutationAuthorized             = false
ReleaseMutationAuthorized             = false
PublishMutationAuthorized             = false
AnkiMutationAuthorized                = false
```

7. authorization-aware validation 必须 PASS；该 workflow 仍不得自动 apply；
8. 单独执行 actual allocator；
9. mutation diff 只能包含授权的两个文件；
10. actual mutation 后立即执行独立 Completion Recheck；
11. CHECKPOINTED 后才能开始 Learner Presentation / Admission / Review / Release 的下一生命周期。

---

## 10. Mutation boundary

当前允许：

```text
read-only inspection / validation
allocation/provenance control-plane maintenance
adversarial checks
NEXT.md / docs checkpoint maintenance
```

当前禁止：

```text
actual third-party Stable NoteID allocation / merge without explicit user authorization
changing authorization.json to Authorized=true from a generic continue instruction
changing StableNoteIDAllocationAuthorized=true without explicit user authorization
creating stable_evidence_bindings.csv before actual authorized allocation
promoting unverified third-party occurrences into Master textbook source map
turning held rows into automatic allocation or reuse
surface-word-only dedup when senses differ
manual edit of generated publish files
renumber/reuse of Stable NoteIDs / ExpressionIDs
bulk resetting Learning/Review Cards
changing FSRS / Review History / Due from GitHub-side content operations
automatically mixing ExpressionID operations into Vocabulary updates
```

Current authoritative state：

```text
Stable Vocabulary current max NoteID = KV001194
actual third-party Stable rows        = 0
actual third-party evidence bindings  = 0
current Vocabulary release            = 972
actual allocation                     = NOT AUTHORIZED / NOT STARTED
```
